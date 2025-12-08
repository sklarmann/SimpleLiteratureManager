from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
import json
import re

import requests
from django.db import models, transaction
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags
from django.views.decorators.http import require_http_methods

from .forms import (
    AuthorForm,
    DoiImportForm,
    JournalForm,
    ProjectForm,
    PublicationForm,
    TagForm,
)
from .models import (
    Author,
    Journal,
    Project,
    Publication,
    PublicationAnnotation,
    PublicationAuthor,
    Tag,
)


AUTHOR_PREFETCH = Prefetch(
    "authors",
    queryset=Author.objects.order_by(
        "author_publications__position", "author_publications__id"
    ),
)

def author_list(request):
    authors = Author.objects.all()
    return render(request, "author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(
        Author.objects.prefetch_related("publications__journal"), pk=pk
    )
    publications = author.publications.select_related("journal").prefetch_related(
        AUTHOR_PREFETCH
    )
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


def journal_detail(request, pk):
    journal = get_object_or_404(
        Journal.objects.prefetch_related(
            "publication_set__authors",
            "publication_set__journal",
            "publication_set__tags",
        ),
        pk=pk,
    )
    publications = journal.publication_set.select_related("journal").prefetch_related(
        AUTHOR_PREFETCH,
        "tags",
    )
    return render(
        request, "journal_detail.html", {"journal": journal, "publications": publications}
    )


def tag_list(request):
    tags = Tag.objects.annotate(publication_count=models.Count("publications"))
    return render(request, "tag_list.html", {"tags": tags})


def tag_detail(request, pk):
    tag = get_object_or_404(
        Tag.objects.prefetch_related(
            "publications__authors",
            "publications__journal",
            "publications__tags",
        ),
        pk=pk,
    )
    publications = tag.publications.select_related("journal").prefetch_related(
        AUTHOR_PREFETCH, "tags"
    )
    return render(request, "tag_detail.html", {"tag": tag, "publications": publications})


def tag_create(request):
    if request.method == "POST":
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tag_list")
    else:
        form = TagForm()
    return render(request, "tag_form.html", {"form": form, "is_edit": False})


def tag_update(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect("tag_detail", pk=tag.pk)
    else:
        form = TagForm(instance=tag)

    return render(
        request, "tag_form.html", {"form": form, "is_edit": True, "tag": tag}
    )


def journal_create(request):
    if request.method == "POST":
        form = JournalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("journal_list")
    else:
        form = JournalForm()

    return render(request, "journal_form.html", {"form": form, "is_edit": False})


def journal_update(request, pk):
    journal = get_object_or_404(Journal, pk=pk)
    if request.method == "POST":
        form = JournalForm(request.POST, instance=journal)
        if form.is_valid():
            form.save()
            return redirect("journal_detail", pk=journal.pk)
    else:
        form = JournalForm(instance=journal)

    return render(
        request, "journal_form.html", {"form": form, "is_edit": True, "journal": journal}
    )

def publication_list(request):
    publications = (
        Publication.objects.select_related("journal")
        .prefetch_related(AUTHOR_PREFETCH, "tags", "projects")
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
        Publication.objects.select_related("journal").prefetch_related(
            AUTHOR_PREFETCH, "tags", "projects"
        ),
        pk=pk,
    )
    return render(request, "publication_detail.html", {"publication": publication})


def _serialize_annotation(annotation):
    return {
        "id": annotation.id,
        "page_number": annotation.page_number,
        "x": annotation.x,
        "y": annotation.y,
        "width": annotation.width,
        "height": annotation.height,
        "color": annotation.color,
        "comment": annotation.comment,
        "created_at": annotation.created_at,
        "updated_at": annotation.updated_at,
    }


@require_http_methods(["GET", "POST"])
def publication_annotations(request, pk):
    publication = get_object_or_404(Publication, pk=pk)

    if request.method == "GET":
        annotations = publication.annotations.all()
        return JsonResponse([_serialize_annotation(a) for a in annotations], safe=False)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Ungültiger JSON-Body."}, status=400)

    required_fields = ["page_number", "x", "y", "width", "height", "color"]
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        return JsonResponse(
            {"error": f"Fehlende Felder: {', '.join(missing_fields)}"}, status=400
        )

    annotation = PublicationAnnotation.objects.create(
        publication=publication,
        page_number=payload.get("page_number"),
        x=payload.get("x"),
        y=payload.get("y"),
        width=payload.get("width"),
        height=payload.get("height"),
        color=payload.get("color", "#ffeb3b"),
        comment=payload.get("comment", ""),
    )

    return JsonResponse(_serialize_annotation(annotation), status=201)


@require_http_methods(["PATCH", "DELETE"])
def publication_annotation_detail(request, pk, annotation_id):
    publication = get_object_or_404(Publication, pk=pk)
    annotation = get_object_or_404(
        PublicationAnnotation, pk=annotation_id, publication=publication
    )

    if request.method == "DELETE":
        annotation.delete()
        return JsonResponse({"status": "deleted"})

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Ungültiger JSON-Body."}, status=400)

    if "comment" in payload:
        annotation.comment = payload["comment"]
    if "color" in payload:
        annotation.color = payload["color"]
    annotation.save(update_fields=["comment", "color", "updated_at"])

    return JsonResponse(_serialize_annotation(annotation))


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


def publication_update_from_doi(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    doi_value = (publication.doi or "").strip()

    if not doi_value:
        return render(
            request,
            "publication_doi_update.html",
            {
                "publication": publication,
                "error": "Für diese Publikation ist keine DOI hinterlegt.",
                "doi_data": None,
            },
        )

    try:
        doi_data = _fetch_publication_by_doi(doi_value)
    except (requests.RequestException, ValueError) as exc:
        return render(
            request,
            "publication_doi_update.html",
            {"publication": publication, "error": str(exc), "doi_data": None},
        )

    doi_data["publication_type_label"] = None
    if doi_data.get("publication_type"):
        doi_data["publication_type_label"] = Publication.PublicationType(
            doi_data["publication_type"]
        ).label

    if request.method == "POST":
        publication.title = (
            doi_data["title"]
            if request.POST.get("title_source") == "doi"
            else publication.title
        )
        publication.year = (
            doi_data["year"]
            if request.POST.get("year_source") == "doi"
            else publication.year
        )
        publication.abstract = (
            doi_data["abstract"]
            if request.POST.get("abstract_source") == "doi"
            else publication.abstract
        )
        publication.volume = (
            doi_data.get("volume") or ""
            if request.POST.get("volume_source") == "doi"
            else publication.volume
        )
        publication.pages = (
            doi_data.get("pages") or ""
            if request.POST.get("pages_source") == "doi"
            else publication.pages
        )
        publication.publication_type = (
            doi_data.get("publication_type", Publication.PublicationType.ARTICLE)
            if request.POST.get("publication_type_source") == "doi"
            else publication.publication_type
        )

        if request.POST.get("journal_source") == "doi":
            journal = None
            if doi_data.get("journal_title"):
                journal, _ = Journal.objects.get_or_create(
                    name=doi_data["journal_title"],
                    defaults={"issn": doi_data.get("issn") or "", "publisher": ""},
                )
            publication.journal = journal

        if request.POST.get("authors_source") == "doi":
            author_instances = []
            for author in doi_data.get("authors", []):
                instance, _ = Author.objects.get_or_create(
                    first_name=author.get("first_name", ""),
                    last_name=author.get("last_name", ""),
                    defaults={
                        "orcid": author.get("orcid"),
                        "university": "",
                        "department": "",
                    },
                )
                author_instances.append(instance)
            publication.set_authors_in_order(author_instances)

        publication.generate_bibtex_key(force=True)
        publication.save()
        return redirect("publication_detail", pk=publication.pk)

    return render(
        request,
        "publication_doi_update.html",
        {"publication": publication, "doi_data": doi_data, "error": None},
    )


def project_list(request):
    projects = Project.objects.prefetch_related(
        "publications__authors", "publications__journal"
    )
    return render(request, "project_list.html", {"projects": projects})


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.prefetch_related(
            "publications__authors",
            "publications__journal",
            "publications__tags",
        ),
        pk=pk,
    )
    project_publications = list(
        project.publications.select_related("journal").prefetch_related(
            AUTHOR_PREFETCH, "tags"
        )
    )
    biblatex_entries = "\n\n".join(
        publication.biblatex_entry for publication in project_publications
    )
    biblatex_entries_short = "\n\n".join(
        publication.biblatex_entry_short for publication in project_publications
    )
    biblatex_entries_short_journal = "\n\n".join(
        publication.biblatex_entry_short_journal
        for publication in project_publications
    )
    biblatex_entries_short_names_short_journal = "\n\n".join(
        publication.biblatex_entry_short_names_short_journal
        for publication in project_publications
    )
    return render(
        request,
        "project_detail.html",
        {
            "project": project,
            "publications": project_publications,
            "biblatex_entries": biblatex_entries,
            "biblatex_entries_short": biblatex_entries_short,
            "biblatex_entries_short_journal": biblatex_entries_short_journal,
            "biblatex_entries_short_names_short_journal": biblatex_entries_short_names_short_journal,
        },
    )


def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, "project_form.html", {"form": form, "is_edit": False})


def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "project_form.html",
        {"form": form, "is_edit": True, "project": project},
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


def _map_crossref_type(raw_type):
    mapping = {
        "journal-article": Publication.PublicationType.ARTICLE,
        "article": Publication.PublicationType.ARTICLE,
        "proceedings-article": Publication.PublicationType.PROCEEDINGS,
        "proceedings": Publication.PublicationType.PROCEEDINGS,
        "book": Publication.PublicationType.BOOK,
        "monograph": Publication.PublicationType.BOOK,
    }
    return mapping.get(raw_type, Publication.PublicationType.ARTICLE)


def _fetch_publication_by_doi(doi):
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
    publication_type = _map_crossref_type(message.get("type"))

    return {
        "title": title,
        "year": year,
        "abstract": abstract,
        "journal_title": journal_title,
        "issn": issn,
        "authors": authors,
        "volume": message.get("volume", ""),
        "pages": message.get("page", ""),
        "publication_type": publication_type,
    }


def publication_add_by_doi(request):
    error = None
    if request.method == "POST":
        form = DoiImportForm(request.POST)
        if form.is_valid():
            doi = form.cleaned_data["doi"].strip()
            try:
                publication_data = _fetch_publication_by_doi(doi)

                with transaction.atomic():
                    journal = None
                    if publication_data["journal_title"]:
                        journal, _ = Journal.objects.get_or_create(
                            name=publication_data["journal_title"],
                            defaults={
                                "issn": publication_data.get("issn") or "",
                                "publisher": "",
                            },
                        )

                    publication = Publication.objects.create(
                        title=publication_data["title"],
                        year=publication_data["year"],
                        doi=doi,
                        journal=journal,
                        abstract=publication_data["abstract"],
                        volume=publication_data.get("volume") or "",
                        pages=publication_data.get("pages") or "",
                        publication_type=publication_data.get(
                            "publication_type", Publication.PublicationType.ARTICLE
                        ),
                    )

                    author_instances = []
                    for author in publication_data["authors"]:
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
                        publication.set_authors_in_order(author_instances)

                    publication.generate_bibtex_key(force=True)
                    publication.save(update_fields=["bibtex_key"])

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
            touched_publications = set()
            with transaction.atomic():
                for publication in publications:
                    duplicate_link = PublicationAuthor.objects.filter(
                        publication=publication, author=other
                    ).first()

                    if duplicate_link is None:
                        continue

                    touched_publications.add(publication)

                    existing_link = PublicationAuthor.objects.filter(
                        publication=publication, author=target
                    ).first()

                    # If the target author is not linked yet, reuse the duplicate link
                    # by switching its author. This avoids violating the unique
                    # (publication, position) constraint while preserving ordering.
                    if existing_link is None:
                        duplicate_link.author = target
                        duplicate_link.save(update_fields=["author"])
                        continue

                    # When both authors are linked, keep the earlier of the two positions
                    # without introducing duplicate positions.
                    if duplicate_link.position < existing_link.position:
                        target_position = duplicate_link.position
                        duplicate_link.delete()
                        existing_link.position = target_position
                        existing_link.save(update_fields=["position"])
                    else:
                        duplicate_link.delete()

                for publication in touched_publications:
                    publication.generate_bibtex_key(force=True)
                    publication.save(update_fields=["bibtex_key"])

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
