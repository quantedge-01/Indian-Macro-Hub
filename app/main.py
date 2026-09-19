from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .store import store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.initialize(seed=settings.seed_demo_data)
    yield


app = FastAPI(
    title="Indian Macro Hub API",
    version="1.0.0",
    description="A searchable India macroeconomic time-series catalog.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/health/live", include_in_schema=False)
def liveness():
    return {"status": "ok"}


def require_series(series_id: str):
    series = store.get_series(series_id)
    if not series:
        raise HTTPException(404, detail=f"Unknown series '{series_id}'.")
    return series


@app.get("/health")
def health():
    catalog = store.list_series()
    return {
        "status": "ok" if catalog else "degraded",
        "environment": settings.environment,
        "database": str(store.path),
        "catalog_series": len(catalog),
        "data_mode": "empty" if not catalog else ("demo_seed" if any(item["is_demo_data"] for item in catalog) else "live"),
    }


@app.get("/health/ready", include_in_schema=False)
def readiness():
    """Readiness probe: the service is ready only after the catalog is queryable."""
    catalog = store.list_series()
    if not catalog:
        raise HTTPException(503, detail="Database is reachable but contains no series.")
    return {"status": "ready", "catalog_series": len(catalog)}


@app.get("/api/v1/series")
def list_series(q: str | None = Query(None, min_length=1), category: str | None = None):
    matched = store.list_series(q, category)
    return {"count": len(matched), "data": matched}


@app.get("/api/v1/meta")
def metadata():
    return {"name": "Indian Macro Hub", "version": app.version, "environment": settings.environment}


@app.get("/api/v1/series/{series_id}")
def series_detail(series_id: str):
    return {"data": require_series(series_id)}


@app.get("/api/v1/series/{series_id}/observations")
def observations(series_id: str, start: date | None = None, end: date | None = None, vintage: date | None = None):
    series = require_series(series_id)
    if start and end and start > end:
        raise HTTPException(422, detail="start must be on or before end")
    return {"series_id": series["id"], "unit": series["unit"], "is_demo_data": series["is_demo_data"], "data": store.observations(series["id"], start, end, vintage)}


@app.get("/api/v1/series/{series_id}/observations.csv")
def observations_csv(series_id: str, start: date | None = None, end: date | None = None):
    series = require_series(series_id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["series_id", "date", "value", "unit"])
    writer.writeheader()
    for row in store.observations(series["id"], start, end):
        writer.writerow({"series_id": series["id"], "date": row["date"], "value": row["value"], "unit": series["unit"]})
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{series["id"]}.csv"'})


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/app/")


app.mount("/app", StaticFiles(directory="app/static", html=True), name="app")
