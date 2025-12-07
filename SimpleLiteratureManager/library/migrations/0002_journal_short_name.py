from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="short_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
