# Generated manually because django is not available in the execution environment.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0004_project"),
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
                ("x", models.FloatField()),
                ("y", models.FloatField()),
                ("width", models.FloatField()),
                ("height", models.FloatField()),
                ("comment", models.TextField(blank=True)),
                ("color", models.CharField(default="#ffc107", max_length=20)),
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
            options={"ordering": ["publication", "page_number", "id"]},
        ),
    ]
