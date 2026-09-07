from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from discovery.models import (
    DiscoveredSource,
    DiscoveryRun,
)
from jobs.models import JobSource


@dataclass
class PromotionResult:
    created: int = 0
    existing: int = 0
    ignored: int = 0


def _source_name(
    *,
    provider: str,
    identifier: str,
) -> str:
    label = {
        "lever": "Lever",
        "greenhouse": "Greenhouse",
    }.get(
        provider,
        provider.title(),
    )

    return (
        f"{identifier} ({label})"
    )


def _find_existing_source(
    *,
    provider: str,
    identifier: str,
):
    sources = JobSource.objects.filter(
        config__provider=provider,
    )

    if provider == "lever":
        return sources.filter(
            config__site=identifier,
        ).first()

    if provider == "greenhouse":
        return sources.filter(
            config__board_token=identifier,
        ).first()

    return None


@transaction.atomic
def promote_discovered_sources(
    run: DiscoveryRun,
) -> PromotionResult:
    result = PromotionResult()

    discovered = (
        run.sources
        .exclude(
            provider=(
                DiscoveredSource
                .Provider
                .UNKNOWN
            )
        )
        .exclude(
            provider_identifier=""
        )
        .order_by(
            "provider",
            "provider_identifier",
        )
    )

    seen: set[
        tuple[str, str]
    ] = set()

    for item in discovered:
        key = (
            item.provider,
            item.provider_identifier,
        )

        if key in seen:
            continue

        seen.add(key)

        existing = _find_existing_source(
            provider=item.provider,
            identifier=(
                item.provider_identifier
            ),
        )

        if existing is not None:
            result.existing += 1

            run.sources.filter(
                provider=item.provider,
                provider_identifier=(
                    item.provider_identifier
                ),
            ).update(
                status=(
                    DiscoveredSource
                    .Status
                    .REGISTERED
                )
            )

            continue

        if item.provider == "lever":
            region = (
                item.provider_region
                or "global"
            )

            base_host = (
                "https://jobs.eu.lever.co/"
                if region == "eu"
                else "https://jobs.lever.co/"
            )

            config = {
                "provider": "lever",
                "site": (
                    item.provider_identifier
                ),
                "company": (
                    item.company_name
                    or item.provider_identifier
                ),
                "region": region,
            }

            base_url = (
                base_host
                + item.provider_identifier
            )

        elif (
            item.provider
            == "greenhouse"
        ):
            config = {
                "provider": "greenhouse",
                "board_token": (
                    item.provider_identifier
                ),
                "company": (
                    item.company_name
                    or item.provider_identifier
                ),
            }

            base_url = (
                "https://job-boards."
                "greenhouse.io/"
                + item.provider_identifier
            )

        else:
            result.ignored += 1
            continue

        JobSource.objects.create(
            name=_source_name(
                provider=item.provider,
                identifier=(
                    item.provider_identifier
                ),
            ),
            kind=JobSource.Kind.ATS,
            enabled=False,
            base_url=base_url,
            config=config,
        )

        run.sources.filter(
            provider=item.provider,
            provider_identifier=(
                item.provider_identifier
            ),
        ).update(
            status=(
                DiscoveredSource
                .Status
                .REGISTERED
            )
        )

        result.created += 1

    return result
