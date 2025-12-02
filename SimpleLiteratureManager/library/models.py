from django.db import models

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
    issn = models.CharField(max_length=20, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Publication(models.Model):
    title = models.CharField(max_length=500)
    year = models.PositiveIntegerField()
    doi = models.CharField(max_length=255, blank=True, null=True)

    authors = models.ManyToManyField(Author, related_name="publications")
    journal = models.ForeignKey(Journal, on_delete=models.SET_NULL, null=True, blank=True)

    abstract = models.TextField(blank=True, null=True)
    pdf = models.FileField(upload_to="publications/", blank=True, null=True)

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return f"{self.title} ({self.year})"
