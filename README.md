# JobRadar v0.2

A configurable job discovery and deterministic matching backend.

## Current scope

- Normalized jobs and job sources
- Configurable search profiles
- Configurable matching rules (no QA-specific logic hardcoded)
- Filter vs scoring rules
- Match explanations
- Pluggable collectors
- Django admin configuration
- REST endpoints for jobs, profiles and matches
- Demo collector + evaluation command
- Real Lever public-postings collector
- Provider-neutral collector registry
- `collect_jobs` management command
- Lever source configuration command

## Architecture

A collected `Job` is source data. A `SearchProfile` represents a particular job search.
`SearchRule` records define what the profile requires, excludes or prefers.
`JobMatch` stores the result of evaluating a job against a profile.

This lets one job be evaluated by multiple profiles without duplication.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DB_NAME=jobradar
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432

python manage.py makemigrations jobs searches
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For a quick SQLite start, omit `DB_NAME`.

## Seed a working QA example

```bash
python manage.py seed_demo
python manage.py evaluate_jobs
```

Then open:

- Django admin: http://127.0.0.1:8000/admin/
- API jobs: http://127.0.0.1:8000/api/jobs/
- API profiles: http://127.0.0.1:8000/api/profiles/
- API matches: http://127.0.0.1:8000/api/matches/

## Next milestone

1. Replace demo collector with real Lever collector.
2. Add Greenhouse collector.
3. Add normalized location/remote parsing.
4. Improve experience extraction.
5. Add deduplication across sources.
6. Build minimal Next.js results UI.


## Configure a real Lever company source

Lever's public Postings API is company-site scoped. Add a company whose careers
page is hosted by Lever:

```bash
python manage.py add_lever_source leverdemo "Lever Demo"
python manage.py collect_jobs --source "Lever Demo (Lever)"
python manage.py evaluate_jobs --profile qa-main
```

For a real employer, replace `leverdemo` with the site's Lever slug from
`https://jobs.lever.co/<site>`.

EU-hosted Lever sites:

```bash
python manage.py add_lever_source <site> "Company Name" --region eu
```

Then inspect ranked results:

```text
GET /api/matches/?profile=qa-main&eligible=true
```

## Important current boundary

Lever's public Postings API exposes published vacancies per company site; it is
not a global search endpoint. JobRadar therefore treats each Lever employer as a
configured `JobSource`. Discovering employers/ATS sites automatically will be a
separate source-discovery layer.

## v0.3 target

- deterministic experience-requirement extraction
- normalized skill extraction
- cross-source deduplication fingerprint
- Greenhouse collector
