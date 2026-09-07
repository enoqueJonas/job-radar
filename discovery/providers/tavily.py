from __future__ import annotations

import os

from tavily import TavilyClient

from .base import (
    SearchProvider,
    SearchResult,
)


class TavilyConfigurationError(
    ValueError
):
    pass


class TavilySearchProvider(
    SearchProvider
):
    def __init__(
        self,
        api_key: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.getenv(
                "TAVILY_API_KEY"
            )
        )

        if not self.api_key:
            raise TavilyConfigurationError(
                "TAVILY_API_KEY is required."
            )

        self.client = TavilyClient(
            api_key=self.api_key
        )

    def search(
        self,
        *,
        query: str,
        include_domains: list[str],
        max_results: int = 10,
    ) -> list[SearchResult]:
        response = self.client.search(
            query=query,
            search_depth="basic",
            include_domains=(
                include_domains
            ),
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )

        results = (
            response.get("results")
            or []
        )

        normalized: list[
            SearchResult
        ] = []

        for result in results:
            normalized.append(
                SearchResult(
                    title=str(
                        result.get(
                            "title",
                            "",
                        )
                    ).strip(),
                    url=str(
                        result.get(
                            "url",
                            "",
                        )
                    ).strip(),
                    snippet=str(
                        result.get(
                            "content",
                            "",
                        )
                    ).strip(),
                    score=(
                        float(
                            result["score"]
                        )
                        if result.get(
                            "score"
                        )
                        is not None
                        else None
                    ),
                )
            )

        return normalized
