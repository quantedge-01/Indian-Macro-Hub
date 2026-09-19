# Indian Macro Hub

Indian Macro Hub is a source-aware time-series catalog for India's macroeconomy. It provides searchable series metadata, historical observations, provenance, charting, CSV exports, and a small JSON API.

The project is designed as a maintainable showcase and a foundation for production ingestion—not as a claim that every bundled value is production data. Demo seed data is clearly labelled; live connectors retain the provider URL, import date, and vintage of each observation.

## Features

- FastAPI backend with OpenAPI documentation at `/docs`
- Responsive static web UI at `/app/`
- SQLite storage with foreign keys, WAL mode, indexes, and immutable observation vintages
- World Bank and FRED connectors using public provider APIs
- Official CSV importer for approved RBI/MoSPI releases
- Search, category filtering, date ranges, vintage selection, and CSV export
- Liveness and readiness health probes for deployment
- Environment-based configuration and a non-root Docker image
- GitHub Actions checks for tests and Python compilation

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # optional; edit values for your environment
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/app/`. API documentation is available at `http://127.0.0.1:8000/docs`.

The default development mode seeds a small, clearly-labelled demo catalog. Set `SEED_DEMO_DATA=false` for an empty/live-only database.

## Docker

```bash
docker build -t indian-macro-hub .
docker run --rm -p 8000:8000 \
  -e SEED_DEMO_DATA=true \
  -v "$PWD/data:/app/data" \
  indian-macro-hub
```

For production, mount a persistent volume at `/app/data`, set `SEED_DEMO_DATA=false`, and configure `CORS_ORIGINS` only when the UI is hosted on a separate domain. SQLite is appropriate for a single-instance showcase; PostgreSQL is recommended for multi-instance or high-write deployments.

## API

```text
GET /health/live
GET /health/ready
GET /health
GET /api/v1/meta
GET /api/v1/series?q=inflation&category=Prices
GET /api/v1/series/{series_id}
GET /api/v1/series/{series_id}/observations?start=2020-01-01&end=2025-12-31
GET /api/v1/series/{series_id}/observations?vintage=2026-09-19
GET /api/v1/series/{series_id}/observations.csv
```

The default observations endpoint returns the latest available vintage for each observation date. A specific vintage can be requested when historical revision analysis is needed.

## Loading live data

### World Bank annual indicators

```bash
python3 -m app.world_bank
```

This imports India's annual inflation, real GDP growth, total reserves, and domestic credit indicators from the World Bank Indicators API. It removes demo series and records the source URL and import date.

### FRED feeds

```bash
python3 -m app.fred
```

This imports the configured monthly CPI and quarterly real GDP feeds. Review provider terms before redistribution.

### Official CSV releases

Prepare a CSV with `date,value` headers, then run:

```bash
python3 -m app.official_csv cpi_combined.csv \
  --id MOSPI-CPI-COMBINED \
  --title "CPI Combined" \
  --frequency Monthly \
  --unit "Index" \
  --source "MoSPI" \
  --source-url "https://cpi.mospi.gov.in/" \
  --category Prices
```

Each import is associated with a vintage date. Re-importing a revised value later preserves the earlier vintage rather than overwriting it.

## Data and storage

The database path defaults to `data/indian_macro_hub.db`. For backwards compatibility, an existing pre-rename `data/arthadata.db` is used automatically when the new file does not exist. Override the location with `INDIAN_MACRO_HUB_DATABASE`.

The SQLite file is intentionally excluded from Git because databases may contain large, licensed, or environment-specific data. A fresh clone therefore starts with demo data unless a database volume or live connector is supplied.

The `series` table stores definitions and provenance. The `observations` table stores values and immutable vintages with a unique `(series_id, observation_date, vintage_date)` key. See `app/store.py` for the storage contract.

## Project structure

```text
app/main.py          FastAPI app and HTTP endpoints
app/store.py         SQLite schema and query layer
app/catalog.py       Demo catalog and seed observations
app/world_bank.py    World Bank connector
app/fred.py          FRED connector
app/official_csv.py  Approved CSV importer
app/static/          Browser UI
tests/               Unit tests
Dockerfile           Production container image
```

## Verification

```bash
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

## Production roadmap

Before treating this as a public data service, add scheduled ingestion with retries and reconciliation, provider licence checks, structured logging and metrics, authentication/rate limiting for write operations, PostgreSQL plus object storage for raw releases, and a release calendar. Do not redistribute a provider's data until its terms allow it.
