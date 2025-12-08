import os
import re

from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


def _normalize_filename_component(value, fallback="unknown"):
    normalized = (value or "").strip().replace(" ", "_")
    normalized = re.sub(r"[^\w.-]", "", normalized, flags=re.UNICODE)
    return normalized or fallback


def publication_pdf_upload_to(instance, filename):
    base, extension = os.path.splitext(filename)

    pending_authors = getattr(instance, "_pending_ordered_authors", None) or []
    first_author = (pending_authors[0] if pending_authors else None) or (
        instance.ordered_authors.first() if instance.pk else None
    )

    year_part = _normalize_filename_component(str(instance.year or "unknown"))
    author_part = _normalize_filename_component(
        getattr(first_author, "last_name", None), fallback="UnknownAuthor"
    )
    title_part = _normalize_filename_component(instance.title, fallback="publication")

    filename = f"{year_part}_{author_part}_{title_part}{extension}"
    return os.path.join("publications", filename)

class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    orcid = models.CharField(max_length=19, blank=True, null=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Journal(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    issn = models.CharField(max_length=20, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Publication(models.Model):
    class PublicationType(models.TextChoices):
        ARTICLE = "article", "Artikel"
        PROCEEDINGS = "proceedings", "Proceedings"
        BOOK = "book", "Buch"

    title = models.CharField(max_length=500)
    year = models.PositiveIntegerField()
    doi = models.CharField(max_length=255, blank=True, null=True)
    publication_type = models.CharField(
        max_length=20,
        choices=PublicationType.choices,
        default=PublicationType.ARTICLE,
    )

    authors = models.ManyToManyField(
        Author, related_name="publications", through="PublicationAuthor"
    )
    journal = models.ForeignKey(Journal, on_delete=models.SET_NULL, null=True, blank=True)
    volume = models.CharField(max_length=50, blank=True, null=True)
    pages = models.CharField(max_length=50, blank=True, null=True)
    tags = models.ManyToManyField(Tag, related_name="publications", blank=True)
    projects = models.ManyToManyField(Project, related_name="publications", blank=True)

    abstract = models.TextField(blank=True, null=True)
    pdf = models.FileField(
        upload_to=publication_pdf_upload_to, blank=True, null=True
    )
    bibtex_key = models.CharField(max_length=255, unique=True, blank=True, editable=False)

    class Meta:
        ordering = ["-year", "title"]

    def save(self, *args, **kwargs):
        should_generate = not self.bibtex_key
        if self.pk and not should_generate:
            existing = Publication.objects.filter(pk=self.pk).only("year").first()
            if existing and existing.year != self.year:
                should_generate = True

        if should_generate:
            self.generate_bibtex_key(force=True)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.year})"

    def generate_bibtex_key(self, force=False):
        if self.bibtex_key and not force:
            return self.bibtex_key

        from django.utils.text import slugify

        first_author = None
        if self.pk:
            first_author = self.ordered_authors.first()
        base_name = slugify(first_author.last_name) if first_author else "publication"
        if not base_name:
            base_name = "publication"

        year_part = str(self.year or "")
        candidate = f"{base_name}{year_part}"
        suffix = 1

        while (
            Publication.objects.filter(bibtex_key=candidate)
            .exclude(pk=self.pk)
            .exists()
        ):
            suffix += 1
            candidate = f"{base_name}{year_part}-{suffix}"

        self.bibtex_key = candidate
        return candidate

    @property
    def ordered_authors(self):
        return Author.objects.filter(author_publications__publication=self).order_by(
            "author_publications__position", "author_publications__id"
        )

    def set_authors_in_order(self, authors):
        authors = list(authors)

        PublicationAuthor.objects.filter(publication=self).delete()
        PublicationAuthor.objects.bulk_create(
            [
                PublicationAuthor(
                    publication=self, author=author, position=index
                )
                for index, author in enumerate(authors, start=1)
            ]
        )
        return authors

    def _abbreviate_first_name(self, first_name):
        import re

        tokens = re.split(r"([\s-])", (first_name or "").strip())
        abbreviated = []
        for token in tokens:
            if not token:
                continue
            if token in {" ", "-"}:
                abbreviated.append(token)
            else:
                abbreviated.append(f"{token[0]}.")
        return "".join(abbreviated)

    def _format_authors(self, short_first_names=False):
        authors = list(self.ordered_authors)
        if not authors:
            return ""

        formatted_authors = []
        for author in authors:
            first_name = (
                self._abbreviate_first_name(author.first_name)
                if short_first_names
                else author.first_name
            )
            formatted_authors.append(f"{author.last_name}, {first_name}")
        return " and ".join(formatted_authors)

    def get_biblatex_entry(self, short_first_names=False, short_journal_names=False):
        entry_type_map = {
            self.PublicationType.ARTICLE: "article",
            self.PublicationType.PROCEEDINGS: "inproceedings",
            self.PublicationType.BOOK: "book",
        }
        entry_type = entry_type_map.get(self.publication_type, "article")

        fields = []

        formatted_authors = self._format_authors(short_first_names=short_first_names)
        if formatted_authors:
            fields.append(("author", formatted_authors))

        fields.append(("title", self.title))

        if self.year:
            fields.append(("year", str(self.year)))

        if self.journal:
            journal_title = (
                self.journal.short_name
                if short_journal_names and self.journal.short_name
                else self.journal.name
            )
            if entry_type == "article":
                fields.append(("journaltitle", journal_title))
            else:
                fields.append(("booktitle", journal_title))

        if self.volume:
            fields.append(("volume", self.volume))

        if self.pages:
            fields.append(("pages", self.pages))

        if self.doi:
            fields.append(("doi", self.doi))
            if not self.doi.lower().startswith("http"):
                fields.append(("url", f"https://doi.org/{self.doi}"))
            else:
                fields.append(("url", self.doi))

        field_lines = ",\n".join(
            f"    {name} = {{{value}}}" for name, value in fields if value
        )
        return f"@{entry_type}{{{self.bibtex_key},\n{field_lines}\n}}"

    @property
    def biblatex_entry(self):
        return self.get_biblatex_entry()

    @property
    def biblatex_entry_short(self):
        return self.get_biblatex_entry(short_first_names=True)

    @property
    def biblatex_entry_short_journal(self):
        return self.get_biblatex_entry(short_journal_names=True)

    @property
    def biblatex_entry_short_all(self):
        return self.get_biblatex_entry(short_first_names=True, short_journal_names=True)


class PublicationAuthor(models.Model):
    publication = models.ForeignKey(
        Publication, related_name="publication_authors", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        Author, related_name="author_publications", on_delete=models.CASCADE
    )
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["publication", "author"], name="unique_publication_author"
            ),
            models.UniqueConstraint(
                fields=["publication", "position"],
                name="unique_publication_author_position",
            ),
        ]

    def __str__(self):
        return f"{self.publication} - {self.author} (Pos {self.position})"


class PublicationAnnotation(models.Model):
    publication = models.ForeignKey(
        Publication, related_name="annotations", on_delete=models.CASCADE
    )
    page_number = models.PositiveIntegerField()
    x = models.FloatField(help_text="Linke Position relativ zur Seite (0-1)")
    y = models.FloatField(help_text="Obere Position relativ zur Seite (0-1)")
    width = models.FloatField(help_text="Breite relativ zur Seite (0-1)")
    height = models.FloatField(help_text="Höhe relativ zur Seite (0-1)")
    color = models.CharField(max_length=20, default="#ffeb3b")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["publication", "page_number", "created_at"]

    def __str__(self):
        return f"Annotation Seite {self.page_number} für {self.publication.title}"


@receiver(m2m_changed, sender=Publication.authors.through)
def refresh_bibtex_key_on_authors_change(sender, instance, action, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    publications = []
    if isinstance(instance, Publication):
        publications = [instance]
    elif hasattr(instance, "publications"):
        publications = list(instance.publications.all())

    for publication in publications:
        publication.generate_bibtex_key(force=True)
        publication.save(update_fields=["bibtex_key"])
