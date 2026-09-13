# JobRadar

JobRadar is a configurable job-discovery and matching platform designed to continuously find vacancies from legitimate public sources, normalize them, deduplicate them, evaluate them against configurable search profiles, and surface the strongest opportunities with explainable match results.

The current QA search is the first real-world profile used to prove the platform. QA-specific criteria belong in configuration and rules rather than being hardcoded into the application.

## Product direction

The repository now keeps the product and architecture direction under `docs/`:

- [`docs/VISION.md`](docs/VISION.md) — mission, product principles, scope, and long-term direction
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — staged capability roadmap
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — domain boundaries and architectural rules

These documents are intended to guide implementation decisions as JobRadar evolves from the current backend pipeline into a complete job-search workspace.

## Current pipeline

```text
Search Profile
    ↓
Source Discovery
    ↓
ATS Detection
    ↓
Source Promotion
    ↓
Source Validation
    ↓
Job Collection
    ↓
Normalization + Requirement Extraction
    ↓
Canonical Deduplication
    ↓
Eligibility + Matching
    ↓
Ranked Opportunities
```

## Current capabilities

- Configurable `SearchProfile` records
- Configurable hard filters and weighted scoring rules
- Explicit missing-value behavior in matching
- Explainable match and rejection reasons
- Tavily-backed source discovery abstraction
- Profile-driven discovery queries
- Lever and Greenhouse ATS detection
- Logical ATS-source deduplication and promotion
- Source validation and health state
- Retry-safe handling of transient validation failures
- Lever public-postings collector
- Greenhouse public Job Board collector
- Provider-neutral collector registry
- Canonical source-neutral `Job` model
- Source-specific `JobListing` provenance
- Cross-source job fingerprinting and deduplication
- Deterministic experience-requirement extraction
- Configurable skill keyword extraction
- Django admin configuration
- REST endpoints for jobs, profiles, and matches
- Management commands for discovery, promotion, validation, collection, and matching

## Domain boundaries

JobRadar currently has three primary backend domains:

- **Discovery** finds candidate ATS/job sources.
- **Jobs** validates sources and ingests, normalizes, deduplicates, and stores vacancies.
- **Searches** represents search intent and evaluates jobs for eligibility and relevance.

Future application tracking and candidate/document management will be separate boundaries rather than being folded into `Job` or `JobMatch`.

## Local setup

The project targets Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

For discovery, configure the Tavily API key:

```bash
export TAVILY_API_KEY=<your-key>
```

Then run the test suite:

```bash
python manage.py test
```

SQLite is used by default for local development unless database settings are configured explicitly.

## Demo profile

Seed the working QA example:

```bash
python manage.py seed_demo
```

Useful commands include:

```bash
python manage.py preview_discovery qa-main
python manage.py discover_sources qa-main
python manage.py promote_sources <run-id>
python manage.py validate_sources --timeout 10
python manage.py collect_jobs
python manage.py evaluate_jobs --profile qa-main
```

The matching endpoint can then be used to inspect ranked results:

```text
GET /api/matches/?profile=qa-main&eligible=true
```

## Adding known ATS sources manually

Lever:

```bash
python manage.py add_lever_source <site> "Company Name"
```

For EU-hosted Lever sites:

```bash
python manage.py add_lever_source <site> "Company Name" --region eu
```

Greenhouse:

```bash
python manage.py add_greenhouse_source <board-token> "Company Name"
```

JobRadar can also discover and promote candidate ATS sources automatically through the discovery pipeline.

## Current development focus

The immediate focus is no longer simply adding collectors. It is proving the pipeline at real scale and improving the quality of what reaches the user:

1. bulk-ingestion quality across validated sources;
2. source relevance and source-quality signals;
3. remote/location eligibility modeling;
4. job/listing lifecycle and stale vacancy handling;
5. ranking calibration against reviewed real jobs;
6. collection/discovery run observability;
7. APIs for the future opportunity-review UI.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the broader sequence.
