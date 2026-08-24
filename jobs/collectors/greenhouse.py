from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

from .base import BaseCollector, CollectedJob


class GreenhouseConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class GreenhouseConfig:
    board_token: str
    company: str
    timeout_seconds: int = 20

    @classmethod
    def from_dict(
        cls,
        config: dict[str, Any],
    ) -> "GreenhouseConfig":
        board_token = str(
            config.get("board_token", "")
        ).strip()

        company = str(
            config.get("company", "")
        ).strip()

        if not board_token:
            raise GreenhouseConfigurationError(
                "Greenhouse source config requires "
                "'board_token'."
            )

        if not company:
            raise GreenhouseConfigurationError(
                "Greenhouse source config requires "
                "'company'."
            )

        return cls(
            board_token=board_token,
            company=company,
            timeout_seconds=int(
                config.get(
                    "timeout_seconds",
                    20,
                )
            ),
        )


class GreenhouseCollector(BaseCollector):
    def __init__(
        self,
        config: dict[str, Any],
        session: requests.Session | None = None,
    ):
        self.config = (
            GreenhouseConfig.from_dict(
                config
            )
        )

        self.session = (
            session
            or requests.Session()
        )

    @property
    def base_url(self) -> str:
        return (
            "https://boards-api.greenhouse.io"
            "/v1/boards/"
            f"{self.config.board_token}/jobs"
        )

    def collect(self) -> list[CollectedJob]:
        response = self.session.get(
            self.base_url,
            params={
                "content": "true",
            },
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "JobRadar/0.3 "
                    "(+personal-job-discovery)"
                ),
            },
            timeout=(
                self.config.timeout_seconds
            ),
        )

        response.raise_for_status()

        payload = response.json()

        jobs = payload.get("jobs")

        if not isinstance(jobs, list):
            raise ValueError(
                "Unexpected Greenhouse response: "
                "expected a 'jobs' list."
            )

        return [
            self._normalize(item)
            for item in jobs
        ]

    def _normalize(
        self,
        item: dict[str, Any],
    ) -> CollectedJob:
        location = (
            item.get("location")
            or {}
        )

        location_text = str(
            location.get("name")
            or ""
        ).strip()

        absolute_url = str(
            item.get("absolute_url")
            or ""
        ).strip()

        return CollectedJob(
            external_id=str(
                item["id"]
            ),
            title=str(
                item.get("title")
                or ""
            ).strip(),
            company=self.config.company,
            url=absolute_url,
            apply_url=absolute_url,
            description=(
                self._description_text(
                    item
                )
            ),
            location_text=location_text,
            remote_type=(
                self._detect_remote_type(
                    location_text
                )
            ),
            department=(
                self._department_text(
                    item
                )
            ),
            raw_payload=item,
        )

    @staticmethod
    def _description_text(
        item: dict[str, Any],
    ) -> str:
        content = str(
            item.get("content")
            or ""
        )

        if not content:
            return ""

        return BeautifulSoup(
            content,
            "html.parser",
        ).get_text(
            "\n",
            strip=True,
        )

    @staticmethod
    def _department_text(
        item: dict[str, Any],
    ) -> str:
        departments = (
            item.get("departments")
            or []
        )

        names = [
            str(
                department.get("name")
                or ""
            ).strip()
            for department
            in departments
        ]

        return ", ".join(
            name
            for name in names
            if name
        )

    @staticmethod
    def _detect_remote_type(
        location_text: str,
    ) -> str:
        value = location_text.casefold()

        if "hybrid" in value:
            return "hybrid"

        if (
            "remote" in value
            or "work from home" in value
        ):
            return "remote"

        if location_text.strip():
            return "onsite"

        return "unknown"
