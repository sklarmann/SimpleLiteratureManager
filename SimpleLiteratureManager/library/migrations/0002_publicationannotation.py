from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationAnnotation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("page_number", models.PositiveIntegerField()),
                (
                    "x",
                    models.FloatField(
                        help_text="Linke Position relativ zur Seite (0-1)"
                    ),
                ),
                (
                    "y",
                    models.FloatField(
                        help_text="Obere Position relativ zur Seite (0-1)"
                    ),
                ),
                (
                    "width",
                    models.FloatField(
                        help_text="Breite relativ zur Seite (0-1)"
                    ),
                ),
                (
                    "height",
                    models.FloatField(
                        help_text="H\u00f6he relativ zur Seite (0-1)"
                    ),
                ),
                ("color", models.CharField(default="#ffeb3b", max_length=20)),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "publication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="annotations",
                        to="library.publication",
                    ),
                ),
            ],
            options={
                "ordering": ["publication", "page_number", "created_at"],
            },
        ),
    ]
