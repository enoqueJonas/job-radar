# JobRadar Roadmap

This roadmap describes product capability stages, not fixed release dates. Each stage should leave the system usable and should strengthen the next stage instead of introducing throwaway architecture.

## Stage 1 — Reliable discovery and ingestion

Goal: build a trustworthy pipeline that can find legitimate job sources and ingest vacancies repeatedly.

Capabilities:

- configurable discovery queries per search profile;
- legitimate search-provider abstraction;
- ATS detection;
- Lever and Greenhouse discovery;
- source promotion and deduplication;
- source validation and health state;
- pluggable collectors;
- normalized source-neutral jobs;
- source-specific listings and provenance;
- cross-source job fingerprinting;
- deterministic requirement extraction;
- repeatable collection commands.

Current status: active and substantially implemented.

Key next improvements:

- inspect large-scale ingestion quality across validated sources;
- improve source relevance and source-quality signals;
- improve location and remote eligibility normalization;
- make collection runs observable and auditable;
- handle job/listing lifecycle and stale vacancies cleanly.

## Stage 2 — High-quality matching

Goal: turn collected vacancies into a genuinely useful shortlist rather than a large database of jobs.

Capabilities:

- configurable hard filters and weighted preferences;
- tri-state handling for missing information;
- explainable match and rejection reasons;
- stronger experience extraction;
- skill normalization and aliases;
- title-family and role-relevance modeling;
- location and work-authorization rules;
- salary preferences where data exists;
- applicable-vs-configured scoring analysis;
- calibration using reviewed real jobs.

Exit condition: the highest-ranked jobs should consistently look relevant to the user without requiring manual search through large amounts of noise.

## Stage 3 — Opportunity review experience

Goal: replace command-line inspection with a fast workflow for reviewing opportunities.

Capabilities:

- web dashboard;
- ranked opportunity feed;
- filtering by profile, score, source, location, recency, and status;
- job detail view with extracted requirements and match explanation;
- source/listing provenance;
- mark as interested, rejected, saved, applied, or ignored;
- notes and links;
- duplicate visibility;
- basic discovery and collection health views.

The UI should consume the same domain model and APIs rather than duplicating matching logic in the frontend.

## Stage 4 — Application tracking and documents

Goal: turn JobRadar from discovery software into a complete job-search workspace.

Capabilities:

- application pipeline and status history;
- deadlines and follow-up reminders;
- CV/profile library;
- job-specific CV tailoring based on truthful source material;
- cover-letter generation;
- reusable application answers;
- exportable application packages;
- history of which document version was used for each application.

Document generation should remain traceable to verified candidate information and should not invent qualifications.

## Stage 5 — Alerts and continuous operation

Goal: make JobRadar useful without requiring the user to manually run the pipeline.

Capabilities:

- scheduled discovery;
- scheduled source validation;
- scheduled collection;
- incremental matching;
- new-opportunity notifications;
- alerts for exceptionally strong matches;
- source failure alerts;
- retry policies for transient failures;
- configurable digest frequency.

This stage should reuse observable run models rather than hiding background work inside ad-hoc tasks.

## Stage 6 — Assisted intelligence

Goal: augment deterministic matching where semantic understanding adds real value.

Potential capabilities:

- LLM-assisted requirement extraction;
- semantic title and skill matching;
- job-description summarization;
- explanation refinement;
- identification of transferable skills;
- application-question assistance;
- comparison of near-duplicate postings;
- suggested profile/rule adjustments based on reviewed outcomes.

AI output should be additive. Structured facts, source evidence, and deterministic constraints remain authoritative where possible.

## Stage 7 — Learning from outcomes

Goal: allow JobRadar to improve recommendations based on explicit user behavior and application outcomes.

Potential signals:

- jobs opened or ignored;
- saved/rejected reasons;
- applications submitted;
- recruiter responses;
- interviews;
- offers;
- source quality over time.

The system may use these signals to suggest better weights, titles, sources, and search terms, but user-defined hard constraints must remain under explicit user control.

## Stage 8 — Controlled application assistance

Goal: reduce repetitive application work after discovery, matching, and document generation are reliable.

Potential capabilities:

- pre-fill supported application forms;
- prepare answers for review;
- detect required fields and unsupported questions;
- maintain per-application audit history;
- require user approval before consequential submission actions unless explicitly configured otherwise.

This is intentionally late in the roadmap. Automating poor matches faster would not improve the product.

## Cross-cutting engineering priorities

Every stage should preserve these qualities:

- configurable domain behavior;
- source provenance;
- explainability;
- idempotent ingestion where possible;
- tests around business rules;
- observable pipeline runs;
- clean separation between discovery, ingestion, matching, and application workflows;
- ability to add new ATS/search providers without rewriting core models;
- privacy-conscious handling of candidate information.
