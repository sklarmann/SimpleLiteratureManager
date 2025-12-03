from django import forms
from .models import Author, Journal, Publication, Tag

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "orcid", "university", "department"]


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["name", "issn", "publisher"]


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = [
            "title",
            "year",
            "doi",
            "authors",
            "journal",
            "tags",
            "abstract",
            "pdf",
        ]
        widgets = {
            "authors": forms.SelectMultiple(attrs={"class": "form-select"}),
            "journal": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "doi": forms.TextInput(attrs={"class": "form-control"}),
            "abstract": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "pdf": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class DoiImportForm(forms.Form):
    doi = forms.CharField(
        label="DOI",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "10.xxxx/xxxxx",
                "aria-label": "Digital Object Identifier",
            }
        ),
    )
