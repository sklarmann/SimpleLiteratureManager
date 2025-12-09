# Simple Literature Manager

Simple Literature Manager is a Django application for managing academic publications. It lets you capture authors, journals, projects, and tags; attach PDFs and DOIs; and maintain ordered author lists for each publication.

In its current state, the project is only for local use. There is no user management and no login page so far.

## Architecture and key features
- **Tech stack:** Django 5.1 (Python) with SQLite as the default database and classic server-side template rendering.
- **Publication management:** Track titles, years, DOIs, publication types, volume/page details, and optional PDF uploads with automatic filename generation.
- **Entities & relationships:** Manage authors, journals, tags, and projects, and link them to publications while preserving author order.
- **Import & data quality:** Retrieve DOI metadata using `requests`, check for duplicates, and merge author records when needed.
- **Admin and user interface:** Forms and list views enable curation and search directly in the browser (see `library/templates/`).

## Setup & development
1. Activate a Python environment and install dependencies (for example, `pip install django requests`).
2. Apply migrations: `python manage.py migrate`.
3. Start the development server: `python manage.py runserver` and open `http://127.0.0.1:8000/`.

## Third-party libraries
| Library | Purpose | License |
| --- | --- | --- |
| Django 5.1.14 | Web framework for models, views, templates, and admin | BSD-3-Clause |
| requests | HTTP client for retrieving DOI/metadata | Apache License 2.0 |
| pdf.js | In-browser PDF rendering for publication previews | Apache License 2.0 |

## License
This project is licensed under the BSD-3-Clause license (see `LICENSE`).
