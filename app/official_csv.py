"""Import a cleaned official RBI/MoSPI CSV into Indian Macro Hub with provenance.

CSV must have `date,value` columns; dates are ISO-8601 (YYYY-MM-DD).
"""
from __future__ import annotations
import argparse, csv
from datetime import date
from pathlib import Path
from .store import Store

def main():
    p=argparse.ArgumentParser()
    p.add_argument("csv_file", type=Path); p.add_argument("--id", required=True); p.add_argument("--title", required=True)
    p.add_argument("--frequency", required=True, choices=["Monthly","Quarterly","Weekly"]); p.add_argument("--unit", required=True)
    p.add_argument("--source", required=True); p.add_argument("--source-url", required=True); p.add_argument("--category", default="Macroeconomy")
    a=p.parse_args(); points=[]
    with a.csv_file.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            date.fromisoformat(row["date"]); points.append((row["date"],float(row["value"])))
    if not points: raise SystemExit("No observations found. CSV requires date,value headers.")
    s=Store(); s.initialize(seed=False); vintage=date.today().isoformat()
    s.upsert_series({"id":a.id,"title":a.title,"description":f"Official {a.frequency.lower()} series imported from {a.source}.","category":a.category,"source":a.source,"source_url":a.source_url,"frequency":a.frequency,"unit":a.unit,"seasonal_adjustment":"As published by source","methodology":"See original source release URL and retained local input file.","updated_at":vintage,"is_demo_data":0})
    print({"series_id":a.id,"observations_added":s.add_observations(a.id,points,vintage,a.source_url)})
if __name__=="__main__": main()
