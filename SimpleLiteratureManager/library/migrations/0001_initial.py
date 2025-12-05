from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('orcid', models.CharField(blank=True, max_length=19, null=True)),
                ('university', models.CharField(blank=True, max_length=255, null=True)),
                ('department', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={'ordering': ['last_name', 'first_name']},
        ),
        migrations.CreateModel(
            name='Journal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('issn', models.CharField(blank=True, max_length=20, null=True)),
                ('publisher', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
            ],
            options={'ordering': ['title']},
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('year', models.PositiveIntegerField()),
                ('doi', models.CharField(blank=True, max_length=255, null=True)),
                ('publication_type', models.CharField(choices=[('article', 'Artikel'), ('proceedings', 'Proceedings'), ('book', 'Buch')], default='article', max_length=20)),
                ('volume', models.CharField(blank=True, max_length=50, null=True)),
                ('pages', models.CharField(blank=True, max_length=50, null=True)),
                ('abstract', models.TextField(blank=True, null=True)),
                ('pdf', models.FileField(blank=True, null=True, upload_to='publications/')),
                ('bibtex_key', models.CharField(blank=True, editable=False, max_length=255, unique=True)),
                ('authors', models.ManyToManyField(related_name='publications', through='library.PublicationAuthor', to='library.author')),
                ('journal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='library.journal')),
                ('projects', models.ManyToManyField(blank=True, related_name='publications', to='library.project')),
                ('tags', models.ManyToManyField(blank=True, related_name='publications', to='library.tag')),
            ],
            options={'ordering': ['-year', 'title']},
        ),
        migrations.CreateModel(
            name='PublicationAnnotation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_number', models.PositiveIntegerField()),
                ('x', models.FloatField(help_text='Linke Position relativ zur Seite (0-1)')),
                ('y', models.FloatField(help_text='Obere Position relativ zur Seite (0-1)')),
                ('width', models.FloatField(help_text='Breite relativ zur Seite (0-1)')),
                ('height', models.FloatField(help_text='Höhe relativ zur Seite (0-1)')),
                ('color', models.CharField(default='#ffeb3b', max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='library.publication')),
            ],
            options={'ordering': ['publication', 'page_number', 'created_at']},
        ),
        migrations.CreateModel(
            name='PublicationAuthor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=1)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='author_publications', to='library.author')),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publication_authors', to='library.publication')),
            ],
            options={'ordering': ['position', 'id']},
        ),
        migrations.AddConstraint(
            model_name='publicationauthor',
            constraint=models.UniqueConstraint(fields=('publication', 'author'), name='unique_publication_author'),
        ),
        migrations.AddConstraint(
            model_name='publicationauthor',
            constraint=models.UniqueConstraint(fields=('publication', 'position'), name='unique_publication_author_position'),
        ),
    ]
