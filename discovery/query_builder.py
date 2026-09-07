from __future__ import annotations

from dataclasses import dataclass

from searches.models import SearchProfile


SUPPORTED_DOMAINS = [
    "jobs.lever.co",
    "jobs.eu.lever.co",
    "job-boards.greenhouse.io",
    "boards.greenhouse.io",
]


@dataclass(frozen=True)
class DiscoveryQuery:
    query: str
    include_domains: list[str]


def build_discovery_queries(
    profile: SearchProfile,
) -> list[DiscoveryQuery]:
    titles = [
        str(title).strip()
        for title in profile.discovery_titles
        if str(title).strip()
    ]

    primary_titles = {
        str(title).strip()
        for title in profile.discovery_primary_titles
        if str(title).strip()
    }

    locations = [
        str(location).strip()
        for location in profile.discovery_locations
        if str(location).strip()
    ]

    queries: list[DiscoveryQuery] = []

    for title in titles:
        queries.append(
            DiscoveryQuery(
                query=f'"{title}"',
                include_domains=SUPPORTED_DOMAINS,
            )
        )

        if title not in primary_titles:
            continue

        for location in locations:
            queries.append(
                DiscoveryQuery(
                    query=(
                        f'"{title}" '
                        f'"{location}"'
                    ),
                    include_domains=SUPPORTED_DOMAINS,
                )
            )

    return queries
