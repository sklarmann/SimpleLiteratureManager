from django.contrib import admin
from .forms import ProjectForm
from .models import Author, Journal, Project, Publication, Tag

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "university", "department", "orcid")
    search_fields = ("last_name", "first_name", "orcid", "university", "department")


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("name", "issn", "publisher")
    search_fields = ("name", "issn")


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "journal")
    list_filter = ("year", "journal", "tags")
    search_fields = ("title", "doi")
    filter_horizontal = ("authors", "tags")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title", "description")
    form = ProjectForm
