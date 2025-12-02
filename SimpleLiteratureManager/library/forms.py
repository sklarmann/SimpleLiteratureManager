from django import forms
from .models import Author, Journal

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "orcid", "university", "department"]


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ["name", "issn", "publisher"]
