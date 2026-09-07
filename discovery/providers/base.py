from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    score: float | None = None


class SearchProvider(ABC):
    @abstractmethod
    def search(
        self,
        *,
        query: str,
        include_domains: list[str],
        max_results: int = 10,
    ) -> list[SearchResult]:
        raise NotImplementedError
