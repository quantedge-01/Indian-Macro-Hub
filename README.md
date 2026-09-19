# Indian Macro Hub

An India-focused FRED-style macroeconomic time-series MVP: searchable catalog, provenance-rich series pages, charting, CSV download and an API. Data is persisted locally in SQLite, with an immutable observation-vintage model.

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/app/`. Interactive API documentation is at `/docs`.

## API

- `GET /api/v1/series?q=inflation`
- `GET /api/v1/series/{series_id}`
- `GET /api/v1/series/{series_id}/observations?start=2026-01-01`
- `GET /api/v1/series/{series_id}/observations.csv`

## Load real data (personal use)

The initial live connector imports real annual India indicators from the World Bank's public Indicators API. It removes the bundled demo series, writes observation vintages to SQLite, and can be safely rerun to add later source revisions:

```bash
python3 -m app.world_bank
```

The data remains attributed to its source on every series page. RBI/MoSPI connectors should be added separately using their approved download channels.

## Import official high-frequency releases

Download an official table, make a two-column CSV headed `date,value`, then import it with immutable vintage tracking. Example for MoSPI monthly CPI:

```bash
python3 -m app.official_csv cpi_combined.csv --id MOSPI-CPI-COMBINED --title "CPI Combined" --frequency Monthly --unit "Index" --source "MoSPI" --source-url "https://cpi.mospi.gov.in/" --category Prices
```

Use `Weekly` for RBI FX reserves and `Quarterly` for MoSPI GDP. Every import retains the source URL and import date; repeated imports add later vintages without overwriting previous ones.

## Important data boundary

The included values are **demo seed data**, identified in every API response and UI. They are for exercising the product only. Before public release, replace `app/catalog.py` observations with verified source connectors and retain source URL, release date, definition, revision/vintage and licence for every observation.

`app/ingestion.py` is the intentionally small contract for those connectors. It must only use source channels whose access and redistribution terms have been cleared.

## Suggested production sequence

1. Add an ingestion interface and one official-source connector at a time (RBI then MoSPI).
2. Store observations and immutable vintages in PostgreSQL; keep raw source files in object storage.
3. Add a release calendar, observability and automated reconciliation against source totals.
4. Obtain redistribution rights before offering exchange or commercial data.
