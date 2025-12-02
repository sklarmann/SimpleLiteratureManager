from django.contrib import admin
from .models import Author, Journal, Publication

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
    list_filter = ("year", "journal")
    search_fields = ("title", "doi")
    filter_horizontal = ("authors",)
