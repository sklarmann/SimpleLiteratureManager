from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0002_journal_short_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publication",
            name="pdf",
            field=models.FileField(
                blank=True,
                max_length=200,
                null=True,
                upload_to="library.models.publication_pdf_upload_to",
            ),
        ),
    ]
