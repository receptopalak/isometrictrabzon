#!/usr/bin/env python3
"""Use georeferenced and curated freely licensed REAL photographs from Wikimedia Commons.

No unlicensed satellite imagery is downloaded or redistributed. Photos are
hotlinked from Wikimedia thumbnail URLs, with individual author/source/license.
Photos without verified coordinates appear only in the gallery, not on map pins.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "photos.json"
API = "https://commons.wikimedia.org/w/api.php"
CENTER_LAT, CENTER_LON = 41.0052, 39.7309
BBOX = (39.725, 41.001, 39.737, 41.010)

# Files individually checked on Wikimedia Commons, not geotagged by assumption.
CURATED = [
    "File:Trabzon,AtatürkAlani.jpg",
    "File:Trabzon Meydan Park (1).jpg",
    "File:Trabzon Meydan Park (3).jpg",
    "File:Trabzon Meydan Park (4).jpg",
    "File:Trabzon Meydan 2.jpg",
    "File:Ataturk statue, Trabzon Meydan.jpg",
    "File:Trabzon Meydan Parkı Atatürk Heykeli 0005.jpg",
]
LICENSE_PREFIXES = ("CC BY", "CC-BY", "PUBLIC DOMAIN", "CC0", "PD-")
HEADERS = {
    "User-Agent": "IsometricTrabzon/0.2 (https://github.com/receptopalak/isometrictrabzon; Wikimedia Commons photo viewer)",
    "Accept": "application/json",
}


def clean(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", value).strip()


def get(session, params):
    p = {"action": "query", "format": "json", "formatversion": "2", **params}
    r = session.get(API, params=p, timeout=(15, 50))
    r.raise_for_status()
    payload = r.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    return payload.get("query", {}).get("pages", [])


def photo(page, *, nearby=False):
    if page.get("ns") != 6 or page.get("missing"):
        return None
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return None
    meta = info.get("extmetadata", {})
    val = lambda k: meta.get(k, {}).get("value", "")
    license_name = clean(val("LicenseShortName"))
    if not any(license_name.upper().startswith(allowed) for allowed in LICENSE_PREFIXES):
        return None
    license_url = val("LicenseUrl") or "https://commons.wikimedia.org/wiki/Commons:Licensing"
    thumb = info.get("thumburl")
    if not thumb or not thumb.startswith("https://upload.wikimedia.org/"):
        return None
    title = page.get("title") or ""
    coord = next((c for c in page.get("coordinates", [])
                  if c.get("globe", "earth") == "earth"), None)
    lat, lon = (float(coord["lat"]), float(coord["lon"])) if coord else (None, None)
    if lat is not None and not (BBOX[1]-0.005 <= lat <= BBOX[3]+0.005 and BBOX[0]-0.005 <= lon <= BBOX[2]+0.005):
        coord = None
        lat = lon = None
    author = clean(val("Artist") or val("Attribution") or val("Credit") or "Wikimedia Commons katkıcısı")
    if len(author) > 180:
        author = author[:177] + "..."
    return {
        "id": str(page.get("pageid") or title),
        "title": title.removeprefix("File:").rsplit(".", 1)[0].replace("_", " "),
        "author": author,
        "license": license_name,
        "license_url": license_url,
        "url": info.get("descriptionurl") or "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_")),
        "image": thumb,
        "lat": lat, "lon": lon,
        "geotagged": coord is not None,
        "area": "Trabzon Meydan ve çevresi" if nearby else "Trabzon Meydan — doğrulanmış fotoğraf",
        "source": "Wikimedia Commons",
        "date": (info.get("timestamp") or "")[:10],
    }


def collect():
    session = requests.Session()
    session.headers.update(HEADERS)
    results = {}
    failures = []
    try:
        # Geosearch returns images with actual *file* geotags. Do not invent coords.
        pages = get(session, {
            "generator": "geosearch",
            "ggscoord": f"{CENTER_LAT}|{CENTER_LON}",
            "ggsradius": "1400",
            "ggsnamespace": "6",
            "ggsprimary": "all",
            "ggslimit": "100",
            "prop": "imageinfo|coordinates",
            "iiprop": "url|extmetadata|timestamp",
            "iiurlwidth": "900",
        })
        for p in pages:
            item = photo(p, nearby=True)
            if item and item["geotagged"]:
                results[p["title"]] = item
        print(f"Geotagged CC-licensed Commons images: {len(results)}", flush=True)
    except Exception as exc:
        failures.append("Geo search: " + str(exc))

    try:
        pages = get(session, {
            "titles": "|".join(CURATED),
            "prop": "imageinfo|coordinates",
            "iiprop": "url|extmetadata|timestamp",
            "iiurlwidth": "900",
        })
        for p in pages:
            item = photo(p, nearby=False)
            if item:
                results.setdefault(p["title"], item)
    except Exception as exc:
        failures.append("Curated Commons metadata: " + str(exc))

    if not results:
        # Explicitly verified Wikimedia Commons originals, with source and licence.
        # These lack independently verified coordinates; they are gallery-only.
        seeds = [
            ("Trabzon,AtatürkAlani.jpg", "Bertramz", "CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/"),
            ("Trabzon Meydan Park (1).jpg", "Radosław Botev", "CC BY 3.0 PL", "https://creativecommons.org/licenses/by/3.0/pl/"),
            ("Trabzon Meydan Park (3).jpg", "Radosław Botev", "CC BY 3.0 PL", "https://creativecommons.org/licenses/by/3.0/pl/"),
            ("Trabzon Meydan Park (4).jpg", "Radosław Botev", "CC BY 3.0 PL", "https://creativecommons.org/licenses/by/3.0/pl/"),
            ("Trabzon Meydan 2.jpg", "edkohler", "CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"),
            ("Ataturk statue, Trabzon Meydan.jpg", "PlanetKorriban", "CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/"),
            ("Trabzon Meydan Parkı Atatürk Heykeli 0005.jpg", "Dosseman", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
        ]
        for filename, author, license_name, license_url in seeds:
            title = "File:" + filename
            results[title] = {
                "id": title,
                "title": filename.rsplit(".", 1)[0],
                "author": author,
                "license": license_name,
                "license_url": license_url,
                "url": "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_")),
                "image": "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/" + quote(filename.replace(" ", "_")) + "&width=900",
                "lat": None, "lon": None, "geotagged": False,
                "area": "Trabzon Meydan — doğrulanmış fotoğraf",
                "source": "Wikimedia Commons",
                "date": "",
            }
        print("Using individually verified licensed photo fallback.", flush=True)
    ordered = sorted(results.values(), key=lambda p: (not p["geotagged"], p["title"].lower()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "type": "real_location_photographs",
        "data_source": "Wikimedia Commons",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(ordered),
        "geotagged_count": sum(bool(p["geotagged"]) for p in ordered),
        "disclaimer": "These are real photographs, NOT photogrammetric facade textures. Do not infer each photograph depicts the nearest building.",
        "photos": ordered[:80],
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wikimedia images:", result["count"], "geo:", result["geotagged_count"], flush=True)
    for error in failures:
        print("Warning:", error, flush=True)
    if not ordered:
        print("No Wikimedia photos available; geometry site may still publish without photo overlay.", flush=True)


if __name__ == "__main__":
    collect()
