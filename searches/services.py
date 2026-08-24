from jobs.models import Job
from .matcher import evaluate_job
from .models import JobMatch, SearchProfile


def evaluate_profile(profile: SearchProfile):
    matches = []
    for job in Job.objects.filter(
        active=True
    ):
        result = evaluate_job(job, profile)
        match, _ = JobMatch.objects.update_or_create(
            profile=profile,
            job=job,
            defaults={
                "eligible": result.eligible,
                "score": result.score,
                "matched_weight": result.matched_weight,
                "possible_weight": result.possible_weight,
                "reasons": result.reasons,
                "rejection_reasons": result.rejection_reasons,
            },
        )
        matches.append(match)
    return matches
