import json, pathlib, datetime as dt
from typing import Dict
_SAMPLE = pathlib.Path(__file__).with_name("sample_qb.json")
def fetch_qb(days: int = 90) -> Dict:
    horizon = dt.date.today() - dt.timedelta(days=days)
    data = json.loads(_SAMPLE.read_text())
    return {"transactions": [t for t in data if t["date"] >= str(horizon)]}