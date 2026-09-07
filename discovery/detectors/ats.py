from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class DetectedATS:
    provider: str
    identifier: str
    region: str | None = None
    confidence: float = 1.0


def detect_ats(
    url: str,
) -> DetectedATS | None:
    parsed = urlparse(url)

    host = (
        parsed.netloc
        .casefold()
        .split(":")[0]
    )

    parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if host == "jobs.lever.co":
        if not parts:
            return None

        return DetectedATS(
            provider="lever",
            identifier=parts[0],
            region="global",
        )

    if host == "jobs.eu.lever.co":
        if not parts:
            return None

        return DetectedATS(
            provider="lever",
            identifier=parts[0],
            region="eu",
        )

    if host in {
        "boards.greenhouse.io",
        "job-boards.greenhouse.io",
    }:
        if not parts:
            return None

        return DetectedATS(
            provider="greenhouse",
            identifier=parts[0],
        )

    return None
