from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class CollectedJob:
    external_id: str
    title: str
    company: str
    url: str
    apply_url: str = ""
    description: str = ""
    location_text: str = ""
    remote_type: str = "unknown"
    posted_at: datetime | None = None
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    skills: list[str] = field(default_factory=list)
    country_code: str = ""
    employment_type: str = ""
    team: str = ""
    department: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> list[CollectedJob]:
        raise NotImplementedError
