from django import forms
from .models import Author, Journal, Project, Publication, Tag

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "orcid", "university", "department"]


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["name", "short_name", "issn", "publisher"]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class PublicationForm(forms.ModelForm):
    authors_order = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Publication
        fields = [
            "title",
            "year",
            "doi",
            "publication_type",
            "authors",
            "authors_order",
            "journal",
            "volume",
            "pages",
            "tags",
            "projects",
            "abstract",
            "pdf",
        ]
        widgets = {
            "publication_type": forms.Select(attrs={"class": "form-select"}),
            "authors": forms.SelectMultiple(attrs={"class": "form-select"}),
            "journal": forms.Select(attrs={"class": "form-select"}),
            "volume": forms.TextInput(attrs={"class": "form-control"}),
            "pages": forms.TextInput(attrs={"class": "form-control"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-select"}),
            "projects": forms.SelectMultiple(attrs={"class": "form-select"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "doi": forms.TextInput(attrs={"class": "form-control"}),
            "abstract": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "pdf": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            ordered_ids = [author.pk for author in self.instance.ordered_authors]
            self.fields["authors"].initial = ordered_ids
            self.fields["authors_order"].initial = ",".join(
                str(author_id) for author_id in ordered_ids
            )

    def _ordered_authors_from_cleaned(self):
        order_raw = (self.cleaned_data.get("authors_order") or "").strip()
        if not order_raw:
            order_raw = (self.data.get("authors_order") or "").strip()

        order_ids = [int(value) for value in order_raw.split(",") if value.strip().isdigit()]

        selected_authors = list(self.cleaned_data.get("authors", []))
        selected_lookup = {author.pk: author for author in selected_authors}

        ordered_authors = [
            selected_lookup[author_id]
            for author_id in order_ids
            if author_id in selected_lookup
        ]

        remaining = [
            author for author in selected_authors if author.pk not in order_ids
        ]

        if not ordered_authors and self.instance.pk:
            ordered_authors = [
                author
                for author in self.instance.ordered_authors
                if author.pk in selected_lookup
            ]

        ordered_authors.extend(remaining)
        return ordered_authors

    def clean(self):
        cleaned_data = super().clean()
        self._cleaned_ordered_authors = self._ordered_authors_from_cleaned()
        return cleaned_data

    def save(self, commit=True):
        publication = super().save(commit=False)

        ordered_authors = getattr(self, "_cleaned_ordered_authors", None)

        if ordered_authors is not None:
            publication._pending_ordered_authors = ordered_authors

        def save_relations():
            publication.save()
            final_order = ordered_authors or self._ordered_authors_from_cleaned()
            publication.set_authors_in_order(final_order)

            if "tags" in self.cleaned_data:
                publication.tags.set(self.cleaned_data.get("tags", []))
            if "projects" in self.cleaned_data:
                publication.projects.set(self.cleaned_data.get("projects", []))

            publication.generate_bibtex_key(force=True)
            publication.save(update_fields=["bibtex_key"])

        if commit:
            save_relations()
        else:
            self.save_m2m = save_relations

        return publication


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
