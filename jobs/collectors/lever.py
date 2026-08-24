from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

from .base import BaseCollector, CollectedJob


class CollectorConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class LeverConfig:
    site: str
    company: str
    region: str = "global"
    timeout_seconds: int = 20

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "LeverConfig":
        site = str(config.get("site", "")).strip()
        company = str(config.get("company", "")).strip()
        region = str(config.get("region", "global")).strip().lower()

        if not site:
            raise CollectorConfigurationError("Lever source config requires 'site'.")
        if not company:
            raise CollectorConfigurationError("Lever source config requires 'company'.")
        if region not in {"global", "eu"}:
            raise CollectorConfigurationError(
                "Lever source config 'region' must be 'global' or 'eu'."
            )

        return cls(
            site=site,
            company=company,
            region=region,
            timeout_seconds=int(config.get("timeout_seconds", 20)),
        )


class LeverCollector(BaseCollector):
    """Collect public postings from one configured Lever company site."""

    def __init__(self, config: dict[str, Any], session: requests.Session | None = None):
        self.config = LeverConfig.from_dict(config)
        self.session = session or requests.Session()

    @property
    def base_url(self) -> str:
        host = "api.eu.lever.co" if self.config.region == "eu" else "api.lever.co"
        return f"https://{host}/v0/postings/{self.config.site}"

    def collect(self) -> list[CollectedJob]:
        response = self.session.get(
            self.base_url,
            params={"mode": "json"},
            headers={
                "Accept": "application/json",
                "User-Agent": "JobRadar/0.2 (+personal-job-discovery)",
            },
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Unexpected Lever response: expected a list of postings.")

        return [self._normalize(item) for item in payload]

    def _normalize(self, item: dict[str, Any]) -> CollectedJob:
        categories = item.get("categories") or {}
        workplace_type = self._normalize_workplace_type(item.get("workplaceType"))
        description = self._description_text(item)

        return CollectedJob(
            external_id=str(item["id"]),
            title=str(item.get("text") or "").strip(),
            company=self.config.company,
            url=str(item.get("hostedUrl") or item.get("applyUrl") or "").strip(),
            apply_url=str(item.get("applyUrl") or "").strip(),
            description=description,
            location_text=str(categories.get("location") or "").strip(),
            remote_type=workplace_type,
            country_code=str(item.get("country") or "").upper().strip(),
            employment_type=str(categories.get("commitment") or "").strip(),
            team=str(categories.get("team") or "").strip(),
            department=str(categories.get("department") or "").strip(),
            raw_payload=item,
        )

    @staticmethod
    def _normalize_workplace_type(value: Any) -> str:
        mapping = {
            "remote": "remote",
            "hybrid": "hybrid",
            "on-site": "onsite",
            "onsite": "onsite",
            "unspecified": "unknown",
            None: "unknown",
            "": "unknown",
        }
        return mapping.get(str(value).strip().lower() if value is not None else None, "unknown")

    @staticmethod
    def _description_text(item: dict[str, Any]) -> str:
        pieces: list[str] = []

        primary = item.get("descriptionPlain")
        if primary:
            pieces.append(str(primary).strip())
        else:
            html = item.get("description") or ""
            if html:
                pieces.append(BeautifulSoup(str(html), "html.parser").get_text(" ", strip=True))

        for extra_list in item.get("lists") or []:
            heading = str(extra_list.get("text") or "").strip()
            content = BeautifulSoup(
                str(extra_list.get("content") or ""), "html.parser"
            ).get_text(" ", strip=True)
            section = ": ".join(x for x in (heading, content) if x)
            if section:
                pieces.append(section)

        additional = item.get("additionalPlain")
        if additional:
            pieces.append(str(additional).strip())
        elif item.get("additional"):
            pieces.append(
                BeautifulSoup(
                    str(item["additional"]), "html.parser"
                ).get_text(" ", strip=True)
            )

        return "\n\n".join(piece for piece in pieces if piece)
