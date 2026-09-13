# JobRadar Product Vision

## Mission

JobRadar exists to reduce the effort, noise, and inconsistency involved in finding relevant job opportunities.

The product should continuously discover vacancies from legitimate public sources, normalize them into a common model, evaluate them against configurable candidate profiles, and surface the strongest opportunities with clear explanations of why they match.

The long-term goal is not to build a QA-only job scraper. It is to build a configurable personal job-search platform that can support different roles, experience levels, locations, skills, and career goals without hardcoding one user's current search criteria into the application.

## Problem

Job searching is fragmented across company career pages, applicant tracking systems, job boards, and search engines. Relevant roles are easy to miss, the same vacancy may appear in multiple places, and filtering by title alone produces a large amount of noise.

A useful system therefore needs to solve several distinct problems:

1. discover where jobs are published;
2. collect jobs reliably from those sources;
3. normalize inconsistent source data;
4. deduplicate the same vacancy across sources;
5. extract useful requirements from free-form job descriptions;
6. determine whether a job is eligible for a candidate;
7. rank eligible jobs by relevance;
8. explain the ranking rather than returning an opaque score;
9. retain enough history to support tracking, analytics, and later automation.

## Product principles

### Configurable, not hardcoded

JobRadar must model search intent as data. Role titles, locations, skills, experience limits, exclusions, preferences, and scoring weights belong in configurable profiles and rules rather than application-specific conditionals.

A QA profile is one configuration of JobRadar, not the definition of JobRadar.

### Discovery and ingestion are separate concerns

Finding an employer or ATS endpoint is different from collecting vacancies from a known source. The discovery subsystem identifies candidate sources. The jobs subsystem validates, collects, normalizes, and persists jobs from registered sources.

Keeping these responsibilities separate allows new discovery providers and new ATS collectors to evolve independently.

### Canonical jobs are source-neutral

A vacancy can be exposed by more than one source. JobRadar should therefore maintain a canonical `Job` and separate source-specific `JobListing` records.

This supports cross-source deduplication, source provenance, and future source-quality analysis without duplicating the logical vacancy.

### Eligibility before ranking

A high relevance score should never override a hard constraint. Required filters such as experience limits or explicit exclusions determine eligibility first. Scoring rules rank jobs only after those constraints are considered.

### Explain every match

A useful recommendation should answer both:

- why the job matched;
- why the job was rejected.

Matching should remain inspectable and deterministic while the product is establishing reliable rules and data. More advanced statistical or LLM-assisted matching may augment this later, but should not remove traceability.

### Unknown is not the same as false

Missing information must be represented explicitly. If a posting does not expose a required attribute, the system should not silently assume either that the requirement is satisfied or violated.

This principle applies to matching, source validation, requirement extraction, and future enrichment stages.

### Prefer legitimate, stable integrations

JobRadar should prefer public ATS APIs, documented feeds, permitted search providers, and other legitimate interfaces. The architecture should not depend on scraping platforms that prohibit automated access.

### Build the pipeline before automating applications

Application automation is downstream of discovery and matching quality. JobRadar should first become trustworthy at finding, normalizing, deduplicating, filtering, and ranking jobs before attempting automatic submissions.

## Core product loop

The intended product loop is:

```text
Search Profile
    ↓
Source Discovery
    ↓
Candidate ATS / Job Sources
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
    ↓
Review / Track / Apply
    ↓
Feedback and Search Refinement
```

Each stage should remain observable so failures and weak matches can be traced back to their origin.

## Current target user

The first real profile is focused on remote QA and software-testing opportunities for a candidate based in Mozambique, with configurable experience constraints and preferences for areas such as API testing, payments, fintech, and related QA work.

This profile is intentionally being used as the proving ground for the platform. The data model and architecture must continue to support other search profiles without requiring QA-specific code changes.

## What success looks like

A mature JobRadar should allow a user to define one or more search profiles and then answer, with minimal manual hunting:

- What relevant jobs appeared recently?
- Which of them am I realistically eligible for?
- Which are the strongest matches and why?
- Where was each vacancy discovered?
- Have I already seen or applied to this job?
- Which sources consistently produce useful opportunities?
- Which skills or requirements repeatedly prevent otherwise strong matches?

The system should eventually move the user from manually searching dozens of websites toward reviewing a curated, explainable opportunity feed.

## Deliberate non-goals for the current phase

The current phase does not aim to provide:

- automatic job applications;
- automatic CV fabrication or uncontrolled rewriting;
- opaque AI-only ranking;
- broad web scraping as the primary discovery strategy;
- a production-scale multi-tenant SaaS platform;
- perfect semantic understanding of every job description.

Those may become future capabilities where appropriate, but they should not distort the foundations being built now.

## Long-term direction

Once discovery and matching are reliable, JobRadar can evolve into a broader job-search operating system with application tracking, profile-specific CV generation, job-specific cover letters, alerts, analytics, learning from user decisions, and carefully controlled application assistance.

The long-term differentiator should remain the same: a transparent pipeline that discovers opportunities broadly but evaluates them according to the user's actual career constraints and goals.
