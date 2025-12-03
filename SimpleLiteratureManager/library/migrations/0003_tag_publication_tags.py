from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0002_author_department_university"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="publication",
            name="tags",
            field=models.ManyToManyField(
                blank=True, related_name="publications", to="library.tag"
            ),
        ),
    ]
