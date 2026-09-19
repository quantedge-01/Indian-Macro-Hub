"""Small, dependency-free storage layer with immutable observation vintages."""
from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from .catalog import OBSERVATIONS, SERIES

DEFAULT_DB = Path(__file__).parent.parent / "data" / "indian_macro_hub.db"


class Store:
    def __init__(self, database: str | Path | None = None):
        self.path = Path(database or os.getenv("INDIAN_MACRO_HUB_DATABASE", DEFAULT_DB))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connection(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self, seed: bool = True) -> None:
        with self.connection() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS series (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
                  category TEXT NOT NULL, source TEXT NOT NULL, source_url TEXT NOT NULL,
                  frequency TEXT NOT NULL, unit TEXT NOT NULL, seasonal_adjustment TEXT NOT NULL,
                  methodology TEXT NOT NULL, updated_at TEXT NOT NULL, is_demo_data INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS observations (
                  id INTEGER PRIMARY KEY, series_id TEXT NOT NULL REFERENCES series(id),
                  observation_date TEXT NOT NULL, value REAL NOT NULL, vintage_date TEXT NOT NULL,
                  source_release_url TEXT, ingested_at TEXT NOT NULL,
                  UNIQUE(series_id, observation_date, vintage_date)
                );
                CREATE INDEX IF NOT EXISTS observations_lookup ON observations(series_id, observation_date, vintage_date DESC);
            """)
            if seed and not con.execute("SELECT 1 FROM series LIMIT 1").fetchone():
                for item in SERIES:
                    con.execute("""INSERT INTO series VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (item.id, item.title, item.description, item.category, item.source, item.source_url,
                          item.frequency, item.unit, item.seasonal_adjustment, item.methodology,
                          item.updated_at, int(item.is_demo_data)))
                    for observed_on, value in OBSERVATIONS[item.id]:
                        con.execute("""INSERT INTO observations
                          (series_id, observation_date, value, vintage_date, ingested_at)
                          VALUES (?, ?, ?, ?, ?)""", (item.id, observed_on, value, item.updated_at, self._now()))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def list_series(self, query: str | None = None, category: str | None = None) -> list[dict]:
        clauses, args = [], []
        if query:
            clauses.append("(lower(id || ' ' || title || ' ' || description || ' ' || category || ' ' || source) LIKE ?)")
            args.append(f"%{query.lower().strip()}%")
        if category:
            clauses.append("lower(category) = ?")
            args.append(category.casefold())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as con:
            rows = con.execute(f"SELECT * FROM series {where} ORDER BY title", args).fetchall()
            return [self._series_dict(con, row) for row in rows]

    def get_series(self, series_id: str) -> dict | None:
        with self.connection() as con:
            row = con.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone()
            return self._series_dict(con, row) if row else None

    def _series_dict(self, con, row) -> dict:
        latest = con.execute("""SELECT observation_date, value FROM observations
            WHERE series_id = ? AND vintage_date = (SELECT MAX(vintage_date) FROM observations o2 WHERE o2.series_id = observations.series_id AND o2.observation_date = observations.observation_date)
            ORDER BY observation_date DESC LIMIT 1""", (row["id"],)).fetchone()
        total = con.execute("SELECT COUNT(DISTINCT observation_date) FROM observations WHERE series_id = ?", (row["id"],)).fetchone()[0]
        result = dict(row)
        result["is_demo_data"] = bool(result["is_demo_data"])
        result["observation_count"] = total
        result["latest_observation"] = {"date": latest["observation_date"], "value": latest["value"]} if latest else None
        return result

    def observations(self, series_id: str, start: date | None = None, end: date | None = None, vintage: date | None = None) -> list[dict]:
        clauses, args = ["series_id = ?"], [series_id]
        if start: clauses.append("observation_date >= ?"); args.append(start.isoformat())
        if end: clauses.append("observation_date <= ?"); args.append(end.isoformat())
        if vintage:
            clauses.append("vintage_date = ?"); args.append(vintage.isoformat())
        elif not vintage:
            clauses.append("vintage_date = (SELECT MAX(o2.vintage_date) FROM observations o2 WHERE o2.series_id = observations.series_id AND o2.observation_date = observations.observation_date)")
        with self.connection() as con:
            return [dict(row) for row in con.execute(f"SELECT observation_date AS date, value, vintage_date FROM observations WHERE {' AND '.join(clauses)} ORDER BY observation_date", args)]

    def remove_demo_series(self) -> None:
        with self.connection() as con:
            con.execute("DELETE FROM observations WHERE series_id IN (SELECT id FROM series WHERE is_demo_data = 1)")
            con.execute("DELETE FROM series WHERE is_demo_data = 1")

    def upsert_series(self, item: dict) -> None:
        columns = ("id", "title", "description", "category", "source", "source_url", "frequency", "unit", "seasonal_adjustment", "methodology", "updated_at", "is_demo_data")
        values = tuple(item[column] for column in columns)
        with self.connection() as con:
            con.execute(f"""INSERT INTO series ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})
            ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description,
            category=excluded.category, source=excluded.source, source_url=excluded.source_url,
            frequency=excluded.frequency, unit=excluded.unit, seasonal_adjustment=excluded.seasonal_adjustment,
            methodology=excluded.methodology, updated_at=excluded.updated_at, is_demo_data=excluded.is_demo_data""", values)

    def add_observations(self, series_id: str, points: list[tuple[str, float]], vintage_date: str, source_release_url: str) -> int:
        with self.connection() as con:
            before = con.total_changes
            con.executemany("""INSERT OR IGNORE INTO observations
              (series_id, observation_date, value, vintage_date, source_release_url, ingested_at)
              VALUES (?, ?, ?, ?, ?, ?)""", [(series_id, observed_on, value, vintage_date, source_release_url, self._now()) for observed_on, value in points])
            return con.total_changes - before


store = Store()
