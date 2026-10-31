#!/usr/bin/env python3
"""Audit free reusable aerial imagery for Trabzon Meydan.

This tool searches the public OpenAerialMap STAC catalog. It does NOT scrape
Google, Bing, Esri or other view-only imagery services. False positives from
partial bbox intersections and non-open licenses are not treated as usable.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

API = "https://api.imagery.hotosm.org/stac/search"
BBOX = [39.725, 41.001, 39.737, 41.010]
WIDER_BBOX = [39.65, 40.94, 39.86, 41.08]
OUT = Path("data/open_imagery_audit.json")
OPEN = ("CC-BY-", "CC BY ", "CC-BY-SA", "CC BY-SA", "CC0", "PUBLIC DOMAIN")


def ask(session, bbox):
    resp = session.get(API, params={
        "bbox": ",".join(map(str, bbox)),
        "collections": "openaerialmap",
        "limit": 100,
    }, timeout=(10, 60))
    resp.raise_for_status()
    data = resp.json()
    if "features" not in data:
        raise RuntimeError("STAC search returned no features property")
    return data


def image_info(item):
    p = item.get("properties") or {}
    assets = item.get("assets") or {}
    lic = str(item.get("license") or p.get("license") or "").strip()
    # STAC license can be proprietary, other or a URL; require verified
    # Commons/Creative Commons license before recommending reproduction.
    low = lic.lower().replace("_","-")
    allowed = (
        "cc-by" in low or "cc0" in low or
        "public-domain" in low or low in ("pddl", "cc-by-4.0", "cc-by-sa-4.0")
    ) and ("nc" not in low and "nd" not in low)
    imagery = [(k, v.get("href")) for k, v in assets.items()
               if isinstance(v, dict) and v.get("href")]
    return {
        "id": item.get("id"),
        "geometry_bbox": item.get("bbox"),
        "datetime": p.get("datetime") or p.get("start_datetime"),
        "license": lic or None,
        "license_clear_open": bool(allowed),
        "gsd_m": p.get("gsd") or p.get("eo:gsd"),
        "assets": imagery[:8],
        "source": next((l.get("href") for l in item.get("links", [])
                        if l.get("rel") == "self"), None),
    }


def run():
    session = requests.Session()
    session.headers["User-Agent"] = "isometrictrabzon-open-data-audit/1.0 (GitHub: receptopalak/isometrictrabzon)"
    report = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "dataset": "OpenAerialMap STAC (free open aerial imagery)",
              "pilot_bbox": BBOX, "wider_bbox": WIDER_BBOX,
              "results": {}, "errors": [], "assertions": []}
    for label, bounds in (("meydan", BBOX), ("ortahisar", WIDER_BBOX)):
        try:
            found = ask(session, bounds)
            items = found.get("features", [])
            report["results"][label] = {
                "count": len(items),
                "possibly_more": bool(found.get("links") and
                                       any(a.get("rel") == "next" for a in found["links"])),
                "items": [image_info(it) for it in items],
            }
            print("STAC_SEARCH", label, "count", len(items), flush=True)
            for i in report["results"][label]["items"]:
                print("STAC_ITEM", json.dumps(i, ensure_ascii=False), flush=True)
        except Exception as exc:
            err = label + ": " + repr(exc)
            report["errors"].append(err)
            print("STAC_ERROR", err, flush=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("REPORT_FILE", str(OUT), flush=True)
    if report["errors"]:
        print("RESULT: Coverage unknown for failed queries; do not claim no imagery.")
    else:
        print("RESULT: Verified catalog query completed; inspect item footprints and licenses.")


if __name__ == "__main__":
    run()
