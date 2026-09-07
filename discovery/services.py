from __future__ import annotations

from discovery.detectors.ats import (
    detect_ats,
)
from discovery.models import (
    DiscoveredSource,
    DiscoveryRun,
)
from searches.models import SearchProfile
from django.utils import timezone

from discovery.query_builder import (
    build_discovery_queries,
)
from discovery.providers.base import (
    SearchProvider,
)


def create_discovery_run(
    profile: SearchProfile,
    queries: list[str],
) -> DiscoveryRun:
    return DiscoveryRun.objects.create(
        profile=profile,
        queries=queries,
    )


def register_discovered_url(
    *,
    run: DiscoveryRun,
    url: str,
    company_name: str = "",
) -> DiscoveredSource:
    detected = detect_ats(
        url
    )

    if detected is None:
        return DiscoveredSource.objects.create(
            run=run,
            url=url,
            provider=(
                DiscoveredSource
                .Provider
                .UNKNOWN
            ),
            provider_identifier="",
            provider_region="",
            company_name=company_name,
            confidence=0,
            status=(
                DiscoveredSource
                .Status
                .INVALID
            ),
        )

    return DiscoveredSource.objects.create(
        run=run,
        url=url,
        provider=detected.provider,
        provider_identifier=(
            detected.identifier
        ),
        provider_region=(
            detected.region or ""
        ),
        company_name=company_name,
        confidence=detected.confidence,
    )


def run_discovery(
    *,
    profile: SearchProfile,
    provider: SearchProvider,
    max_results_per_query: int = 10,
) -> DiscoveryRun:
    planned_queries = (
        build_discovery_queries(
            profile
        )
    )

    run = DiscoveryRun.objects.create(
        profile=profile,
        status=(
            DiscoveryRun.Status.RUNNING
        ),
        started_at=timezone.now(),
        queries=[
            {
                "query": item.query,
                "include_domains": (
                    item.include_domains
                ),
            }
            for item in planned_queries
        ],
    )

    seen_urls: set[str] = set()

    try:
        for planned in planned_queries:
            results = provider.search(
                query=planned.query,
                include_domains=(
                    planned.include_domains
                ),
                max_results=(
                    max_results_per_query
                ),
            )

            for result in results:
                if not result.url:
                    continue

                if result.url in seen_urls:
                    continue

                seen_urls.add(
                    result.url
                )

                detected = detect_ats(
                    result.url
                )

                if detected is None:
                    continue

                DiscoveredSource.objects.create(
                    run=run,
                    url=result.url,
                    provider=(
                        detected.provider
                    ),
                    provider_identifier=(
                        detected.identifier
                    ),
                    provider_region=(
                        detected.region or ""
                    ),
                    company_name="",
                    confidence=(
                        result.score
                        if result.score
                        is not None
                        else detected.confidence
                    ),
                )

        run.status = (
            DiscoveryRun.Status.COMPLETED
        )

        run.finished_at = (
            timezone.now()
        )

        run.save(
            update_fields=[
                "status",
                "finished_at",
            ]
        )

    except Exception as exc:
        run.status = (
            DiscoveryRun.Status.FAILED
        )

        run.finished_at = (
            timezone.now()
        )

        run.error_message = str(exc)

        run.save(
            update_fields=[
                "status",
                "finished_at",
                "error_message",
            ]
        )

        raise

    return run
