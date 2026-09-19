from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .store import store

app = FastAPI(title="Indian Macro Hub API", version="0.1.0", description="A searchable India macroeconomic time-series catalog.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@app.on_event("startup")
def prepare_database():
    store.initialize()


def require_series(series_id: str):
    series = store.get_series(series_id)
    if not series:
        raise HTTPException(404, detail=f"Unknown series '{series_id}'.")
    return series


@app.get("/health")
def health():
    catalog = store.list_series()
    return {"status": "ok", "catalog_series": len(catalog), "data_mode": "demo_seed" if any(item["is_demo_data"] for item in catalog) else "live"}


@app.get("/api/v1/series")
def list_series(q: str | None = Query(None, min_length=1), category: str | None = None):
    matched = store.list_series(q, category)
    return {"count": len(matched), "data": matched}


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
