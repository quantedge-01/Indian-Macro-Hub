"""Personal-use import of real India macro data from the World Bank Indicators API."""
from __future__ import annotations

import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from .store import Store

BASE_URL = "https://api.worldbank.org/v2/country/IND/indicator"
SERIES = (
    {"id": "WB-CPI-INFLATION", "indicator": "FP.CPI.TOTL.ZG", "title": "Inflation, consumer prices", "description": "Annual consumer-price inflation for India.", "category": "Prices", "unit": "Percent, annual"},
    {"id": "WB-REAL-GDP-GROWTH", "indicator": "NY.GDP.MKTP.KD.ZG", "title": "GDP growth (annual %)", "description": "Annual growth rate of real GDP for India.", "category": "National accounts", "unit": "Percent, annual"},
    {"id": "WB-TOTAL-RESERVES", "indicator": "FI.RES.TOTL.CD", "title": "Total reserves (includes gold)", "description": "Total reserve assets for India, including gold.", "category": "External sector", "unit": "Current USD"},
    {"id": "WB-DOMESTIC-CREDIT", "indicator": "FS.AST.PRVT.GD.ZS", "title": "Domestic credit to private sector", "description": "Domestic credit to the private sector, as a share of GDP.", "category": "Banking", "unit": "Percent of GDP"},
)


def fetch_indicator(indicator: str) -> tuple[str, list[tuple[str, float]]]:
    url = f"{BASE_URL}/{indicator}?{urlencode({'format': 'json', 'per_page': 100})}"
    with urlopen(url, timeout=30) as response:  # nosec B310: fixed HTTPS public API
        payload = json.load(response)
    rows = payload[1] if len(payload) > 1 else []
    points = sorted((f"{row['date']}-01-01", float(row["value"])) for row in rows if row.get("value") is not None)
    return url, points


def sync(database: str | None = None) -> dict[str, int]:
    store = Store(database)
    store.initialize(seed=False)
    store.remove_demo_series()
    vintage = date.today().isoformat()
    result = {}
    for definition in SERIES:
        url, points = fetch_indicator(definition["indicator"])
        store.upsert_series({
            **definition, "source": "World Bank Open Data", "source_url": url, "frequency": "Annual",
            "seasonal_adjustment": "Not seasonally adjusted", "methodology": "Published World Bank indicator for India; definitions are available at the source URL.",
            "updated_at": vintage, "is_demo_data": 0,
        })
        result[definition["id"]] = store.add_observations(definition["id"], points, vintage, url)
    return result


if __name__ == "__main__":
    print(sync())
