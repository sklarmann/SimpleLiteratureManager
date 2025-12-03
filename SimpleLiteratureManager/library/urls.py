from django.urls import path
from . import views

urlpatterns = [
    path("authors/", views.author_list, name="author_list"),
    path("authors/duplicates/", views.author_duplicates, name="author_duplicates"),
    path(
        "authors/merge/<int:primary_id>/<int:duplicate_id>/",
        views.author_merge,
        name="author_merge",
    ),
    path("authors/<int:pk>/", views.author_detail, name="author_detail"),
    path("authors/add/", views.author_create, name="author_create"),
    path("authors/<int:pk>/edit/", views.author_update, name="author_update"),
    path("authors/<int:pk>/delete/", views.author_delete, name="author_delete"),
    path("journals/", views.journal_list, name="journal_list"),
    path("journals/add/", views.journal_create, name="journal_create"),
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/add/", views.tag_create, name="tag_create"),
    path("publications/", views.publication_list, name="publication_list"),
    path("publications/add/", views.publication_create, name="publication_create"),
    path("publications/<int:pk>/", views.publication_detail, name="publication_detail"),
    path(
        "publications/<int:pk>/edit/", views.publication_update, name="publication_update"
    ),
    path("publications/add-doi/", views.publication_add_by_doi, name="publication_add_by_doi"),
]
