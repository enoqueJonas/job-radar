from __future__ import annotations

from dataclasses import dataclass

import requests
from django.utils import timezone

from jobs.models import JobSource


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error: str = ""
    retryable: bool = False


def validate_source(
    source: JobSource,
    *,
    timeout_seconds: int = 15,
) -> ValidationResult:
    config = source.config or {}

    provider = str(
        config.get("provider", "")
    ).strip().lower()

    try:
        if provider == "lever":
            result = _validate_lever(
                config,
                timeout_seconds,
            )

        elif provider == "greenhouse":
            result = _validate_greenhouse(
                config,
                timeout_seconds,
            )

        else:
            result = ValidationResult(
                valid=False,
                error=(
                    f"Unsupported provider: "
                    f"{provider!r}"
                ),
            )

    except requests.RequestException as exc:
        result = ValidationResult(
            valid=False,
            error=str(exc),
            retryable=True,
        )

    source.last_validated_at = timezone.now()

    if result.valid:
        source.validation_status = (
            JobSource.ValidationStatus.VALID
        )
    elif result.retryable:
        source.validation_status = (
            JobSource.ValidationStatus.UNKNOWN
        )
    else:
        source.validation_status = (
            JobSource.ValidationStatus.INVALID
        )

    source.validation_error = result.error
    source.enabled = result.valid

    source.save(
        update_fields=[
            "last_validated_at",
            "validation_status",
            "validation_error",
            "enabled",
        ]
    )

    return result


def _is_retryable_status(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def _validate_lever(
    config: dict,
    timeout_seconds: int,
) -> ValidationResult:
    site = str(
        config.get("site", "")
    ).strip()

    region = str(
        config.get(
            "region",
            "global",
        )
    ).strip().lower()

    if not site:
        return ValidationResult(
            False,
            "Missing Lever site.",
        )

    host = (
        "api.eu.lever.co"
        if region == "eu"
        else "api.lever.co"
    )

    url = (
        f"https://{host}"
        f"/v0/postings/{site}"
    )

    response = requests.get(
        url,
        params={"mode": "json"},
        timeout=timeout_seconds,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "JobRadar/0.3 "
                "(+source-validation)"
            ),
        },
    )

    if response.status_code != 200:
        return ValidationResult(
            False,
            f"HTTP {response.status_code}",
            retryable=_is_retryable_status(
                response.status_code
            ),
        )

    payload = response.json()

    if not isinstance(payload, list):
        return ValidationResult(
            False,
            "Unexpected Lever payload.",
        )

    return ValidationResult(True)


def _validate_greenhouse(
    config: dict,
    timeout_seconds: int,
) -> ValidationResult:
    token = str(
        config.get(
            "board_token",
            "",
        )
    ).strip()

    if not token:
        return ValidationResult(
            False,
            "Missing Greenhouse board token.",
        )

    url = (
        "https://boards-api."
        "greenhouse.io/v1/boards/"
        f"{token}/jobs"
    )

    response = requests.get(
        url,
        params={"content": "false"},
        timeout=timeout_seconds,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "JobRadar/0.3 "
                "(+source-validation)"
            ),
        },
    )

    if response.status_code != 200:
        return ValidationResult(
            False,
            f"HTTP {response.status_code}",
            retryable=_is_retryable_status(
                response.status_code
            ),
        )

    payload = response.json()

    if not isinstance(
        payload.get("jobs"),
        list,
    ):
        return ValidationResult(
            False,
            "Unexpected Greenhouse payload.",
        )

    return ValidationResult(True)
