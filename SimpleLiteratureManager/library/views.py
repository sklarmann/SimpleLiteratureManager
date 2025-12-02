from django.shortcuts import get_object_or_404, redirect, render
from .forms import AuthorForm, JournalForm
from .models import Author, Journal, Publication

def author_list(request):
    authors = Author.objects.all()
    return render(request, "author_list.html", {"authors": authors})

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

def author_create(request):
    if request.method == "POST":
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("author_list")
    else:
        form = AuthorForm()
    return render(request, "author_form.html", {"form": form})


def author_delete(request, pk):
    author = get_object_or_404(Author, pk=pk)
    if request.method == "POST":
        author.delete()
        return redirect("author_list")
    return redirect("author_list")
