from django.db import migrations, models
from django.utils.text import slugify


def populate_bibtex_keys(apps, schema_editor):
    Publication = apps.get_model("library", "Publication")

    def generate_key(instance):
        first_author = instance.authors.order_by("last_name", "first_name").first()
        base_name = slugify(first_author.last_name) if first_author else "publication"
        if not base_name:
            base_name = "publication"

        year_part = str(instance.year or "")
        candidate = f"{base_name}{year_part}"
        suffix = 1

        while (
            Publication.objects.filter(bibtex_key=candidate)
            .exclude(pk=instance.pk)
            .exists()
        ):
            suffix += 1
            candidate = f"{base_name}{year_part}-{suffix}"

        return candidate

    for publication in Publication.objects.all():
        publication.bibtex_key = generate_key(publication)
        publication.save(update_fields=["bibtex_key"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0005_publication_additional_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="bibtex_key",
            field=models.CharField(
                blank=True, editable=False, max_length=255, null=True, unique=True
            ),
        ),
        migrations.RunPython(populate_bibtex_keys, noop_reverse),
        migrations.AlterField(
            model_name="publication",
            name="bibtex_key",
            field=models.CharField(
                blank=True, editable=False, max_length=255, null=False, unique=True
            ),
        ),
    ]
