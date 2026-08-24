from django.db import transaction
from django.utils import timezone

from jobs.deduplication.fingerprints import (
    build_job_fingerprint,
)
from jobs.extractors.requirements import (
    EXTRACTION_VERSION,
    enrich_collected_job,
)

from .models import (
    Job,
    JobListing,
    JobSource,
    SkillKeyword,
)


@transaction.atomic
def persist_collected_jobs(
    source: JobSource,
    collected_jobs,
):
    skill_keywords = list(
        SkillKeyword.objects.filter(
            enabled=True
        )
    )

    persisted = []

    for item in collected_jobs:
        item, extracted_requirements = (
            enrich_collected_job(
                item,
                skill_keywords,
            )
        )

        fingerprint = build_job_fingerprint(
            company=item.company,
            title=item.title,
            location=item.location_text,
        )

        job = (
            Job.objects
            .filter(
                fingerprint=fingerprint,
            )
            .first()
        )

        if job is None:
            job = Job.objects.create(
                fingerprint=fingerprint,
                title=item.title,
                company=item.company,
                description=item.description,
                location_text=item.location_text,
                remote_type=item.remote_type,
                posted_at=item.posted_at,
                min_years_experience=(
                    item.min_years_experience
                ),
                max_years_experience=(
                    item.max_years_experience
                ),
                skills=item.skills,
                extracted_requirements=(
                    extracted_requirements
                ),
                extraction_version=(
                    EXTRACTION_VERSION
                ),
                country_code=item.country_code,
                employment_type=(
                    item.employment_type
                ),
                team=item.team,
                department=item.department,
                active=True,
            )

        else:
            changed = False

            if (
                not job.description
                and item.description
            ):
                job.description = (
                    item.description
                )
                changed = True

            if (
                job.remote_type
                == Job.RemoteType.UNKNOWN
                and item.remote_type
                != Job.RemoteType.UNKNOWN
            ):
                job.remote_type = (
                    item.remote_type
                )
                changed = True

            if (
                job.min_years_experience
                is None
                and item.min_years_experience
                is not None
            ):
                job.min_years_experience = (
                    item.min_years_experience
                )
                changed = True

            if (
                job.max_years_experience
                is None
                and item.max_years_experience
                is not None
            ):
                job.max_years_experience = (
                    item.max_years_experience
                )
                changed = True

            if (
                not job.skills
                and item.skills
            ):
                job.skills = item.skills
                changed = True

            if (
                not job.extracted_requirements
                and extracted_requirements
            ):
                job.extracted_requirements = (
                    extracted_requirements
                )
                job.extraction_version = (
                    EXTRACTION_VERSION
                )
                changed = True

            if not job.active:
                job.active = True
                changed = True

            if changed:
                job.save()

        JobListing.objects.update_or_create(
            source=source,
            external_id=item.external_id,
            defaults={
                "job": job,
                "url": item.url,
                "apply_url": item.apply_url,
                "raw_payload": (
                    item.raw_payload
                ),
                "active": True,
            },
        )

        persisted.append(job)

    return persisted
