#!/usr/bin/env python3
"""Small, non-invasive audit of freely licensed KartaView street photos.

Never persist photo binaries. Reports counts and a few metadata keys only.
"""
import json
from pathlib import Path
import requests
from datetime import datetime, timezone

BASE = "https://api.openstreetcam.org/2.0/photo/"
PLACES = {
    "meydan": (41.0052, 39.7309),
    "uzun_sokak": (41.0040, 39.7280),
}
OUT = Path("data/open_street_photo_audit.json")

def scan():
    r = {"checked_at": datetime.now(timezone.utc).isoformat(),
         "source": "KartaView / OpenStreetCam",
         "license_reference": "https://kartaview.org/terms",
         "results": {}, "errors": []}
    session = requests.Session()
    session.headers["User-Agent"] = "IsometricTrabzon/1.0 (open-data audit)"
    for name, (lat, lon) in PLACES.items():
        try:
            result = session.get(BASE, params={
                "lat": lat, "lng": lon, "radius": 500,
                "page": 1, "itemsPerPage": 20
            }, timeout=(10, 30))
            result.raise_for_status()
            body = result.json()
            items = body.get("result") or body.get("data") or {}
            if isinstance(items, dict):
                total = items.get("total") or items.get("totalItems") or items.get("totalRecords")
                records = items.get("data") or items.get("photos") or items.get("items") or []
            elif isinstance(items, list):
                total = len(items); records = items
            else:
                total = None; records = []
            if not isinstance(records, list):
                records = []
            r["results"][name] = {"total_reported": total,
                                  "returned": len(records),
                                  "sample_ids": [p.get("id") for p in records[:5] if isinstance(p, dict)],
                                  "response_keys": list(body.keys())[:10],
                                  "result_keys": list(items.keys())[:10] if isinstance(items, dict) else []}
            print("STREET_PHOTO", name, json.dumps(r["results"][name]), flush=True)
        except Exception as e:
            print("STREET_ERROR", name, repr(e), flush=True)
            r["errors"].append({"area":name,"error":str(e)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STREET_REPORT", OUT, flush=True)

if __name__ == "__main__":
    scan()
