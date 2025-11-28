from fastapi import APIRouter, HTTPException, Query
import requests
import csv
import io
from typing import List, Dict, Optional


router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


def _fetch_google_sheet_csv(sheet_id: str, sheet_name: Optional[str] = None) -> List[Dict[str, str]]:
    # Prefer gviz CSV API which works for viewable sheets; otherwise try export endpoint
    if not sheet_name:
        sheet_name = "Sheet1"
    gviz_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    resp = requests.get(gviz_url, timeout=20)
    if resp.status_code != 200:
        alt_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet={sheet_name}"
        resp = requests.get(alt_url, timeout=20)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Unable to fetch Google Sheet CSV")
    content = resp.content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


@router.get("/foster")
def get_foster_forecasts(sheet_id: str = Query(..., description="Google Sheet ID"), sheet: str | None = Query(None)):
    rows = _fetch_google_sheet_csv(sheet_id, sheet)
    # Basic normalization: try to pick common columns; pass-through otherwise
    # Attempt to map a subset to stable keys when present
    normalized: List[Dict[str, str]] = []
    for r in rows:
        normalized.append({
            "player": r.get("Player") or r.get("PLAYER") or r.get("player") or "",
            "pos": r.get("Pos") or r.get("Position") or "",
            "team": r.get("Team") or r.get("TEAM") or "",
            "gp": r.get("GP") or r.get("Games") or "",
            "g": r.get("G") or r.get("Goals") or "",
            "a": r.get("A") or r.get("Assists") or "",
            "pts": r.get("PTS") or r.get("Points") or "",
            # keep original row for any other consumer fields
            "_row": r,
        })
    return {"count": len(rows), "rows": normalized}


