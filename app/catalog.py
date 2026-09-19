from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal


@dataclass(frozen=True)
class Series:
    id: str
    title: str
    description: str
    category: str
    source: str
    source_url: str
    frequency: Literal["Monthly", "Quarterly", "Annual"]
    unit: str
    seasonal_adjustment: str
    methodology: str
    updated_at: str
    is_demo_data: bool = True


SERIES: tuple[Series, ...] = (
    Series("IN-CPI-HEADLINE", "Consumer Price Index — Headline Inflation", "All-India CPI inflation, year-on-year.", "Prices", "MoSPI", "https://www.mospi.gov.in/", "Monthly", "Percent, YoY", "Not seasonally adjusted", "Percentage change in the consumer price index from the same month a year earlier.", "2026-09-01"),
    Series("IN-REPO-RATE", "Policy Repo Rate", "RBI policy repo rate.", "Monetary policy", "Reserve Bank of India", "https://data.rbi.org.in/", "Monthly", "Percent per annum", "Not applicable", "The policy rate at which RBI lends short-term funds against government securities.", "2026-09-01"),
    Series("IN-BANK-CREDIT", "Scheduled Commercial Bank Credit", "Outstanding non-food bank credit.", "Banking", "Reserve Bank of India", "https://data.rbi.org.in/", "Monthly", "₹ lakh crore", "Not seasonally adjusted", "Outstanding credit reported by scheduled commercial banks.", "2026-09-01"),
    Series("IN-FOREX-RESERVES", "Foreign Exchange Reserves", "India's foreign-exchange reserves.", "External sector", "Reserve Bank of India", "https://data.rbi.org.in/", "Monthly", "USD billion", "Not seasonally adjusted", "Official reserve assets reported by RBI.", "2026-09-01"),
    Series("IN-REAL-GDP", "Real GDP Growth", "Real gross domestic product growth, year-on-year.", "National accounts", "MoSPI", "https://www.mospi.gov.in/", "Quarterly", "Percent, YoY", "Seasonally adjusted where released", "Change in real GDP from the comparable previous-year period.", "2026-09-01"),
)

# Local MVP seed observations. Replace through source connectors before any public use.
OBSERVATIONS: dict[str, list[tuple[str, float]]] = {
    "IN-CPI-HEADLINE": [("2025-10-01", 1.5), ("2025-11-01", 0.7), ("2025-12-01", 2.1), ("2026-01-01", 2.3), ("2026-02-01", 3.2), ("2026-03-01", 3.4), ("2026-04-01", 3.6), ("2026-05-01", 3.8)],
    "IN-REPO-RATE": [("2025-10-01", 5.50), ("2025-11-01", 5.50), ("2025-12-01", 5.25), ("2026-01-01", 5.25), ("2026-02-01", 5.25), ("2026-03-01", 5.25), ("2026-04-01", 5.25), ("2026-05-01", 5.25)],
    "IN-BANK-CREDIT": [("2025-10-01", 181.2), ("2025-11-01", 183.0), ("2025-12-01", 185.6), ("2026-01-01", 187.4), ("2026-02-01", 189.1), ("2026-03-01", 191.8), ("2026-04-01", 193.0), ("2026-05-01", 195.4)],
    "IN-FOREX-RESERVES": [("2025-10-01", 688.2), ("2025-11-01", 694.5), ("2025-12-01", 701.1), ("2026-01-01", 695.8), ("2026-02-01", 702.3), ("2026-03-01", 709.0), ("2026-04-01", 715.7), ("2026-05-01", 721.4)],
    "IN-REAL-GDP": [("2024-07-01", 6.5), ("2024-10-01", 6.2), ("2025-01-01", 6.8), ("2025-04-01", 7.0), ("2025-07-01", 6.7), ("2025-10-01", 6.9)],
}


def series_dict(series: Series) -> dict:
    data = asdict(series)
    points = OBSERVATIONS[series.id]
    data["observation_count"] = len(points)
    data["latest_observation"] = {"date": points[-1][0], "value": points[-1][1]}
    return data


def get_series(series_id: str) -> Series | None:
    return next((item for item in SERIES if item.id == series_id), None)


def filter_observations(series_id: str, start: date | None, end: date | None) -> list[dict]:
    results = []
    for observation_date, value in OBSERVATIONS[series_id]:
        parsed = date.fromisoformat(observation_date)
        if (start is None or parsed >= start) and (end is None or parsed <= end):
            results.append({"date": observation_date, "value": value})
    return results
