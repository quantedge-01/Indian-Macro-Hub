"""Contracts used by verified source connectors; no web scraping belongs here."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ObservationInput:
    series_id: str
    observation_date: date
    value: float
    vintage_date: date
    source_release_url: str


class SourceConnector:
    """Each provider must implement this using its permitted API/download channel."""
    provider: str

    def fetch(self, series_id: str, since: date | None = None) -> list[ObservationInput]:
        raise NotImplementedError
