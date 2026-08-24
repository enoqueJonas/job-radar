from .base import BaseCollector
from .demo import DemoCollector
from .lever import LeverCollector
from .greenhouse import (
    GreenhouseCollector,
)


class UnsupportedCollectorError(ValueError):
    pass


def build_collector(source) -> BaseCollector:
    config = source.config or {}
    provider = str(config.get("provider", "")).strip().lower()

    if provider == "lever":
        return LeverCollector(config)

    if provider == "greenhouse":
        return GreenhouseCollector(
            config
        )

    if provider == "demo" or source.name.casefold() == "demo":
        return DemoCollector()

    raise UnsupportedCollectorError(
        f"No collector registered for source '{source.name}' "
        f"(provider={provider!r})."
    )
