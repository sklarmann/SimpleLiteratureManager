# Generated manually due to offline environment
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0003_tag_publication_tags"),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
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
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["title"]},
        ),
        migrations.AddField(
            model_name="publication",
            name="projects",
            field=models.ManyToManyField(
                blank=True, related_name="publications", to="library.project"
            ),
        ),
    ]
