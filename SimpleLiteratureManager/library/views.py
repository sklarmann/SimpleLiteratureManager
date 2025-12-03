from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
import re

import requests
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags

from .forms import AuthorForm, DoiImportForm, JournalForm, PublicationForm
from .models import Author, Journal, Publication, Tag

def author_list(request):
    authors = Author.objects.all()
    return render(request, "author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(
        Author.objects.prefetch_related("publications__journal"), pk=pk
    )
    publications = author.publications.select_related("journal")
    return render(
        request,
        "author_detail.html",
        {"author": author, "publications": publications},
    )


def author_duplicates(request):
    authors = list(Author.objects.all())

    def normalize_name(value):
        return re.sub(r"[^a-z]", "", (value or "").lower())

    def is_abbreviation_match(left, right):
        left_norm, right_norm = normalize_name(left), normalize_name(right)
        if not left_norm or not right_norm or left_norm[0] != right_norm[0]:
            return False

        short, long = (
            (left_norm, right_norm) if len(left_norm) <= len(right_norm) else (right_norm, left_norm)
        )
        return len(short) == 1 or long.startswith(short) or (len(short) <= 3 and long.startswith(short))

    def is_similar_enough(left, right, threshold=0.85):
        left_norm, right_norm = normalize_name(left), normalize_name(right)
        if not left_norm or not right_norm:
            return False
        if left_norm == right_norm:
            return True
        return SequenceMatcher(None, left_norm, right_norm).ratio() >= threshold

    def is_first_name_match(left, right):
        return is_abbreviation_match(left, right) or is_similar_enough(left, right, threshold=0.8)

    def is_last_name_match(left, right):
        return is_similar_enough(left, right, threshold=0.85)

    def is_potential_duplicate(first_author, second_author):
        return is_last_name_match(first_author.last_name, second_author.last_name) and is_first_name_match(
            first_author.first_name, second_author.first_name
        )

    parent = {author.id: author.id for author in authors}

    def find(author_id):
        while parent[author_id] != author_id:
            parent[author_id] = parent[parent[author_id]]
            author_id = parent[author_id]
        return author_id

    def union(first_id, second_id):
        root_first, root_second = find(first_id), find(second_id)
        if root_first != root_second:
            parent[root_second] = root_first

    for author_a, author_b in combinations(authors, 2):
        if is_potential_duplicate(author_a, author_b):
            union(author_a.id, author_b.id)

    grouped_authors = defaultdict(list)
    for author in authors:
        grouped_authors[find(author.id)].append(author)

    duplicate_groups = []
    for author_list in grouped_authors.values():
        if len(author_list) < 2:
            continue

        sorted_authors = sorted(author_list, key=lambda a: (a.last_name.lower(), a.first_name.lower()))
        representative = sorted_authors[0]
        duplicate_groups.append(
            {
                "key": (representative.first_name, representative.last_name),
                "authors": sorted_authors,
                "pairs": list(combinations(sorted_authors, 2)),
            }
        )

    duplicate_groups.sort(key=lambda entry: (entry["key"][1], entry["key"][0]))

    return render(
        request,
        "author_duplicates.html",
        {"duplicate_groups": duplicate_groups},
    )


def journal_list(request):
    journals = Journal.objects.all()
    return render(request, "journal_list.html", {"journals": journals})


def tag_list(request):
    tags = Tag.objects.annotate(publication_count=models.Count("publications"))
    return render(request, "tag_list.html", {"tags": tags})


def journal_create(request):
    if request.method == "POST":
        form = JournalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("journal_list")
    else:
        form = JournalForm()
    return render(request, "journal_form.html", {"form": form})

def publication_list(request):
    publications = (
        Publication.objects.select_related("journal")
        .prefetch_related("authors", "tags")
    )
    return render(request, "publication_list.html", {"publications": publications})


def publication_create(request):
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("publication_list")
    else:
        form = PublicationForm()
    return render(request, "publication_form.html", {"form": form, "is_edit": False})


def publication_detail(request, pk):
    publication = get_object_or_404(
        Publication.objects.select_related("journal").prefetch_related("authors", "tags"),
        pk=pk,
    )
    return render(request, "publication_detail.html", {"publication": publication})


def publication_update(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES, instance=publication)
        if form.is_valid():
            form.save()
            return redirect("publication_detail", pk=publication.pk)
    else:
        form = PublicationForm(instance=publication)

    return render(
        request,
        "publication_form.html",
        {"form": form, "publication": publication, "is_edit": True},
    )


def _extract_year(message):
    for key in ("published-print", "published-online", "issued"):
        info = message.get(key)
        if info and "date-parts" in info and info["date-parts"]:
            return info["date-parts"][0][0]
    raise ValueError("Kein Veröffentlichungsjahr in den DOI-Daten gefunden.")


def _parse_authors(message):
    authors = []
    for entry in message.get("author", []):
        first = entry.get("given", "").strip()
        last = entry.get("family", "").strip()
        if not (first or last):
            continue
        orcid = entry.get("ORCID") or ""
        authors.append(
            {
                "first_name": first,
                "last_name": last,
                "orcid": orcid.replace("https://orcid.org/", "") if orcid else None,
            }
        )
    return authors


def publication_add_by_doi(request):
    error = None
    if request.method == "POST":
        form = DoiImportForm(request.POST)
        if form.is_valid():
            doi = form.cleaned_data["doi"].strip()
            try:
                response = requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
                response.raise_for_status()
                message = response.json().get("message", {})

                title_list = message.get("title", [])
                if not title_list:
                    raise ValueError("Kein Titel in den DOI-Daten gefunden.")

                title = title_list[0]
                year = _extract_year(message)
                abstract = strip_tags(message.get("abstract", "")).strip()
                journal_title = (message.get("container-title") or [None])[0]
                issn = (message.get("ISSN") or [None])[0]
                authors = _parse_authors(message)

                with transaction.atomic():
                    journal = None
                    if journal_title:
                        journal, _ = Journal.objects.get_or_create(
                            name=journal_title,
                            defaults={"issn": issn or "", "publisher": ""},
                        )

                    publication = Publication.objects.create(
                        title=title,
                        year=year,
                        doi=doi,
                        journal=journal,
                        abstract=abstract,
                    )

                    author_instances = []
                    for author in authors:
                        instance, _ = Author.objects.get_or_create(
                            first_name=author["first_name"],
                            last_name=author["last_name"],
                            defaults={
                                "orcid": author.get("orcid"),
                                "university": "",
                                "department": "",
                            },
                        )
                        author_instances.append(instance)

                    if author_instances:
                        publication.authors.set(author_instances)

                return redirect("publication_list")
            except (requests.RequestException, ValueError) as exc:
                error = str(exc)
    else:
        form = DoiImportForm()

    return render(request, "publication_import_doi.html", {"form": form, "error": error})

def author_create(request):
    if request.method == "POST":
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("author_list")
    else:
        form = AuthorForm()
    return render(request, "author_form.html", {"form": form, "is_edit": False})


def author_update(request, pk):
    author = get_object_or_404(Author, pk=pk)
    if request.method == "POST":
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            form.save()
            return redirect("author_list")
    else:
        form = AuthorForm(instance=author)
    return render(
        request,
        "author_form.html",
        {
            "form": form,
            "author": author,
            "is_edit": True,
        },
    )


def author_delete(request, pk):
    author = get_object_or_404(Author, pk=pk)
    if request.method == "POST":
        author.delete()
        return redirect("author_list")
    return redirect("author_list")


def author_merge(request, primary_id, duplicate_id):
    author_primary = get_object_or_404(Author, pk=primary_id)
    author_duplicate = get_object_or_404(Author, pk=duplicate_id)

    if author_primary.id == author_duplicate.id:
        return redirect("author_duplicates")

    author_map = {"primary": author_primary, "duplicate": author_duplicate}

    if request.method == "POST":
        keep_choice = request.POST.get("keep", "primary")
        target = author_map.get(keep_choice, author_primary)
        other = author_duplicate if target is author_primary else author_primary

        def resolve_value(field_name):
            selected = request.POST.get(f"{field_name}_source", keep_choice)
            source_author = author_map.get(selected, target)
            return getattr(source_author, field_name)

        target.first_name = resolve_value("first_name")
        target.last_name = resolve_value("last_name")
        target.orcid = resolve_value("orcid")
        target.university = resolve_value("university")
        target.department = resolve_value("department")
        target.save()

        publications = other.publications.all()
        if publications.exists():
            target.publications.add(*publications)

        other.delete()

        return redirect("author_detail", pk=target.pk)

    merge_fields = [
        {
            "name": "first_name",
            "label": "Vorname",
            "primary_value": author_primary.first_name,
            "duplicate_value": author_duplicate.first_name,
        },
        {
            "name": "last_name",
            "label": "Nachname",
            "primary_value": author_primary.last_name,
            "duplicate_value": author_duplicate.last_name,
        },
        {
            "name": "orcid",
            "label": "ORCID",
            "primary_value": author_primary.orcid,
            "duplicate_value": author_duplicate.orcid,
        },
        {
            "name": "university",
            "label": "Universität",
            "primary_value": author_primary.university,
            "duplicate_value": author_duplicate.university,
        },
        {
            "name": "department",
            "label": "Abteilung",
            "primary_value": author_primary.department,
            "duplicate_value": author_duplicate.department,
        },
    ]

    return render(
        request,
        "author_merge.html",
        {
            "author_primary": author_primary,
            "author_duplicate": author_duplicate,
            "merge_fields": merge_fields,
        },
    )
