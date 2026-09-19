"""Import current India monthly CPI and quarterly GDP from FRED source feeds."""
import csv
from datetime import date
from io import StringIO
from urllib.request import urlopen
from .store import Store

SERIES=[("FRED-IND-CPI-M","CPALTT01INM657N","India CPI — all items","Monthly","Index 2020=100","OECD via FRED"),("FRED-IND-REAL-GDP-Q","NGDPRNSAXDCINQ","India real GDP","Quarterly","Millions of domestic currency","IMF via FRED")]
def sync():
 s=Store();s.initialize(seed=False);v=date.today().isoformat();out={}
 for sid,code,title,freq,unit,source in SERIES:
  url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
  with urlopen(url,timeout=30) as r: rows=csv.DictReader(StringIO(r.read().decode()))
  pts=[(x["DATE"],float(x[code])) for x in rows if x[code] not in (".","")]
  s.upsert_series({"id":sid,"title":title,"description":f"{freq} India series.","category":"Prices" if freq=="Monthly" else "National accounts","source":source,"source_url":url,"frequency":freq,"unit":unit,"seasonal_adjustment":"Not seasonally adjusted","methodology":"Provider metadata at source URL.","updated_at":v,"is_demo_data":0})
  out[sid]=s.add_observations(sid,pts,v,url)
 return out
if __name__=="__main__": print(sync())
