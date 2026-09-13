# JobRadar Architecture Direction

This document captures the architectural boundaries that should guide implementation decisions as JobRadar grows.

It is intentionally higher-level than module documentation. The purpose is to prevent later features from collapsing distinct responsibilities into one tightly coupled workflow.

## Domain boundaries

### Discovery

Responsibility: find candidate places where jobs are published.

Owns concepts such as:

- discovery queries;
- search providers;
- discovery runs;
- discovered URLs;
- ATS detection;
- discovered source candidates;
- source promotion evidence.

Discovery should not own canonical job persistence or matching rules.

### Jobs

Responsibility: ingest and normalize jobs from known sources.

Owns concepts such as:

- registered job sources;
- source validation;
- collectors;
- canonical jobs;
- source-specific listings;
- normalization;
- requirement extraction;
- fingerprints and deduplication;
- source/listing lifecycle.

A `Job` represents the logical vacancy. A `JobListing` represents one source occurrence of that vacancy.

### Searches

Responsibility: represent search intent and evaluate jobs against it.

Owns concepts such as:

- search profiles;
- hard filters;
- scoring rules;
- missing-value behavior;
- job matches;
- rejection reasons;
- match explanations.

Search criteria should remain configurable data rather than being encoded inside collectors or job models.

### Applications — future boundary

Responsibility: track what the user does with an opportunity.

Expected concepts include:

- application records;
- application state/history;
- notes;
- document versions;
- follow-ups;
- submission evidence.

This should remain separate from `JobMatch`. A job can match strongly without being applied to, and one job can be evaluated under multiple profiles.

### Candidate profile/documents — future boundary

Responsibility: hold verified candidate facts and reusable career material.

Expected concepts include:

- candidate profiles;
- experience and skills;
- CV variants;
- reusable answers;
- generated document artifacts;
- provenance of generated statements.

This boundary will become important before CV and cover-letter generation is introduced.

## Current pipeline

```text
SearchProfile
    │
    ├── discovery titles / locations
    │
    ▼
DiscoveryQuery Builder
    │
    ▼
SearchProvider
    │
    ▼
DiscoveryRun + DiscoveredSource
    │
    ▼
ATS Detection
    │
    ▼
Promotion → JobSource
    │
    ▼
Source Validation
    │
    ▼
Collector Registry
    │
    ├── LeverCollector
    └── GreenhouseCollector
    │
    ▼
CollectedJob
    │
    ▼
Requirement Extraction / Normalization
    │
    ▼
Fingerprint Deduplication
    │
    ├── Job
    └── JobListing
    │
    ▼
SearchRule Evaluation
    │
    ▼
JobMatch
```

## Architectural rules

### 1. Collectors normalize; they do not decide relevance

A collector may translate provider-specific fields into the canonical shape, but it must not decide whether a vacancy is useful for a particular search profile.

For example, a Lever collector may normalize `workplaceType` to `remote`, but it should not reject a role because it is not QA.

### 2. Discovery does not create jobs directly

Discovery finds candidate sources. Collection retrieves vacancies. This prevents search-provider result quality from contaminating canonical job persistence and allows discovered sources to be validated before use.

### 3. Validation establishes source health, not search relevance

A valid ATS source means the endpoint exists and can be collected from. It does not imply that the company or board will produce useful vacancies for any particular profile.

Source relevance and source health are separate signals.

### 4. Canonical data should not contain source-specific identifiers

Provider-specific IDs, raw payloads, source URLs, and application URLs belong on `JobListing`. The canonical `Job` should contain source-neutral job attributes.

### 5. Hard constraints and preferences remain distinct

A required rule can make a job ineligible. A scoring rule can only affect ranking. This distinction should remain visible in both the data model and explanations.

### 6. Missing values require explicit behavior

Rules that operate on optional structured fields must define what happens when data is unavailable. The system should not rely on Python truthiness or silent defaults for domain decisions.

### 7. External systems are accessed through adapters

Search providers and ATS collectors should be represented behind stable internal interfaces. Provider-specific request/response handling should remain at the edge of the system.

### 8. Repeated runs should be safe

Discovery, promotion, collection, and matching are recurring workflows. They should be designed to avoid duplicate logical records and to update existing records predictably.

### 9. Preserve raw evidence where useful

Normalization will improve over time. Keeping source payloads on listings and discovery evidence in the discovery domain makes it possible to debug extraction errors and reprocess data without losing provenance.

### 10. Automation must be observable

As scheduled runs are introduced, the system should record what ran, when it ran, what succeeded, what failed, and enough context to diagnose the failure. Background execution should not turn the pipeline into a black box.

## Extension strategy

### Adding a new ATS

A new ATS should normally require:

1. ATS detection support;
2. a collector implementing the common collector contract;
3. registry wiring;
4. source validation logic;
5. provider-specific normalization tests.

It should not require changes to canonical matching logic.

### Adding a new search provider

A new discovery search provider should implement the search-provider abstraction and return the common result shape. ATS detection and promotion should remain reusable.

### Adding a new career profile

A new search use case should primarily require data/configuration:

- discovery titles;
- locations;
- hard filters;
- scoring rules;
- skill keywords/aliases.

If adding a new role requires branching application code on the role name, the abstraction should be reviewed.

## Near-term architectural priorities

The next backend work should focus on reliability and data quality before introducing broad new product surfaces:

- collection-run observability;
- source relevance/quality signals;
- remote/location eligibility modeling;
- job/listing lifecycle and stale vacancy handling;
- ranking calibration using real collected jobs;
- APIs that cleanly support the future review UI.

These priorities strengthen the existing pipeline rather than bypassing it.
