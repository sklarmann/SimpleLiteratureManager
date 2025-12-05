from django import forms
from .models import Author, Journal, Project, Publication, Tag

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "orcid", "university", "department"]


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["name", "issn", "publisher"]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = [
            "title",
            "year",
            "doi",
            "publication_type",
            "authors",
            "journal",
            "journal_volume",
            "pages",
            "tags",
            "projects",
            "abstract",
            "pdf",
        ]
        widgets = {
            "authors": forms.SelectMultiple(attrs={"class": "form-select"}),
            "journal": forms.Select(attrs={"class": "form-select"}),
            "publication_type": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select"}),
            "projects": forms.SelectMultiple(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "doi": forms.TextInput(attrs={"class": "form-control"}),
            "journal_volume": forms.TextInput(attrs={"class": "form-control"}),
            "pages": forms.TextInput(attrs={"class": "form-control"}),
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


class ProjectForm(forms.ModelForm):
    publications = forms.ModelMultipleChoiceField(
        queryset=Publication.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Project
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["publications"].initial = self.instance.publications.all()

    def save(self, commit=True):
        project = super().save(commit)

        def save_m2m():
            project.publications.set(self.cleaned_data.get("publications", []))

        if commit:
            save_m2m()
        else:
            self.save_m2m = save_m2m

        return project
