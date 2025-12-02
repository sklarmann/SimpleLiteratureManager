from django.urls import path
from . import views

urlpatterns = [
    path("authors/", views.author_list, name="author_list"),
    path("authors/add/", views.author_create, name="author_create"),
    path("authors/<int:pk>/delete/", views.author_delete, name="author_delete"),
    path("journals/", views.journal_list, name="journal_list"),
    path("journals/add/", views.journal_create, name="journal_create"),
    path("publications/", views.publication_list, name="publication_list"),
]
