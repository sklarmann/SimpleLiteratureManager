from collections import defaultdict

from django.db import connection, migrations, models


def migrate_author_relations(apps, schema_editor):
    PublicationAuthor = apps.get_model("library", "PublicationAuthor")
    Author = apps.get_model("library", "Author")

    author_map = {author.id: author for author in Author.objects.all()}

    with connection.cursor() as cursor:
        cursor.execute("SELECT publication_id, author_id FROM library_publication_authors")
        rows = cursor.fetchall()

    publications = defaultdict(list)
    for publication_id, author_id in rows:
        publications[publication_id].append(author_id)

    for publication_id, author_ids in publications.items():
        authors = [author_map[aid] for aid in author_ids if aid in author_map]
        authors.sort(
            key=lambda a: ((a.last_name or "").lower(), (a.first_name or "").lower())
        )
        PublicationAuthor.objects.bulk_create(
            [
                PublicationAuthor(
                    publication_id=publication_id, author=author, position=index
                )
                for index, author in enumerate(authors, start=1)
            ]
        )


def reverse_migration(apps, schema_editor):
    PublicationAuthor = apps.get_model("library", "PublicationAuthor")

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM library_publication_authors")
        rows = [
            (pa.publication_id, pa.author_id)
            for pa in PublicationAuthor.objects.all().order_by("position", "id")
        ]
        if rows:
            cursor.executemany(
                "INSERT INTO library_publication_authors (publication_id, author_id) VALUES (%s, %s)",
                rows,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0006_publication_bibtex_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationAuthor",
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
                (
                    "position",
                    models.PositiveIntegerField(default=1),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="author_publications",
                        to="library.author",
                    ),
                ),
                (
                    "publication",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="publication_authors",
                        to="library.publication",
                    ),
                ),
            ],
            options={
                "ordering": ["position", "id"],
                "db_table": "library_publicationauthor",
            },
        ),
        migrations.AddConstraint(
            model_name="publicationauthor",
            constraint=models.UniqueConstraint(
                fields=("publication", "author"), name="unique_publication_author"
            ),
        ),
        migrations.AddConstraint(
            model_name="publicationauthor",
            constraint=models.UniqueConstraint(
                fields=("publication", "position"),
                name="unique_publication_author_position",
            ),
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name="publication",
                    name="authors",
                ),
                migrations.AddField(
                    model_name="publication",
                    name="authors",
                    field=models.ManyToManyField(
                        related_name="publications",
                        through="library.PublicationAuthor",
                        to="library.author",
                    ),
                ),
            ],
        ),
        migrations.RunPython(migrate_author_relations, reverse_migration),
    ]
