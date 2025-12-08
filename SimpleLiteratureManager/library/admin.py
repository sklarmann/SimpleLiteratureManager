from django.contrib import admin
from .forms import ProjectForm
from .models import Author, Journal, Project, Publication, PublicationAnnotation, Tag

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "university", "department", "orcid")
    search_fields = ("last_name", "first_name", "orcid", "university", "department")


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "issn", "publisher")
    search_fields = ("name", "short_name", "issn")


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "year",
        "publication_type",
        "journal",
        "volume",
        "pages",
        "bibtex_key",
    )
    list_filter = ("year", "journal", "tags", "publication_type")
    search_fields = ("title", "doi", "bibtex_key")
    # The authors relationship uses an explicit through model for ordered authors,
    # so it cannot be used with filter_horizontal.
    filter_horizontal = ("tags",)


@admin.register(PublicationAnnotation)
class PublicationAnnotationAdmin(admin.ModelAdmin):
    list_display = (
        "publication",
        "page_number",
        "comment",
        "color",
        "created_at",
    )
    list_filter = ("page_number", "publication")
    search_fields = ("comment", "publication__title")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title", "description")
    form = ProjectForm
