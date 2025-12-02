from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags
from .forms import AuthorForm, DoiImportForm, JournalForm, PublicationForm
from .models import Author, Journal, Publication
import requests

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


def journal_list(request):
    journals = Journal.objects.all()
    return render(request, "journal_list.html", {"journals": journals})


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
    publications = Publication.objects.select_related("journal").prefetch_related("authors")
    return render(request, "publication_list.html", {"publications": publications})


def publication_create(request):
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("publication_list")
    else:
        form = PublicationForm()
    return render(request, "publication_form.html", {"form": form})


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
