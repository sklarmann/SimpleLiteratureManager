from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0004_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="publication_type",
            field=models.CharField(
                choices=[
                    ("article", "Artikel"),
                    ("proceedings", "Proceedings"),
                    ("book", "Buch"),
                ],
                default="article",
                max_length=20,
                verbose_name="Typ",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="journal_volume",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="Journal Volume"),
        ),
        migrations.AddField(
            model_name="publication",
            name="pages",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="Seiten"),
        ),
    ]
