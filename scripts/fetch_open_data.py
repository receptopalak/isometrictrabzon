#!/usr/bin/env python3
"""Download open Trabzon Meydan 3D prototype data: OSM ways + Mapzen Terrarium."""
import datetime as dt
import io
import json
import math
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BBOX = (39.725, 41.001, 39.737, 41.010)  # west, south, east, north
OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]
HEADERS = {"User-Agent": "IsometricTrabzon/0.1 (open-map demonstration; https://github.com/receptopalak/isometrictrabzon)"}


def make_geojson(elements, origin):
    features = []
    counts = {"building": 0, "road": 0, "park_or_water": 0}
    for e in elements:
        if e.get("type") != "way":
            continue
        ring = e.get("geometry", [])
        coords = [[p["lon"], p["lat"]] for p in ring if "lon" in p and "lat" in p]
        tags = e.get("tags", {})
        if len(coords) < 2:
            continue
        if tags.get("building") and tags["building"] != "no" and len(coords) >= 4 and coords[0] == coords[-1]:
            geom = {"type": "Polygon", "coordinates": [coords]}
            typ = "building"
        elif tags.get("highway"):
            geom = {"type": "LineString", "coordinates": coords}
            typ = "road"
        elif len(coords) >= 4 and coords[0] == coords[-1] and (
            tags.get("leisure") == "park" or tags.get("natural") == "water" or
            tags.get("landuse") in ("grass", "forest", "meadow")
        ):
            geom = {"type": "Polygon", "coordinates": [coords]}
            typ = "park_or_water"
        else:
            continue
        features.append({"type": "Feature", "id": "osm-way-" + str(e["id"]),
                         "properties": {"source": "OpenStreetMap", "osm_id": e["id"], **tags},
                         "geometry": geom})
        counts[typ] += 1
    if counts["building"] < 1:
        raise RuntimeError("OSM sorgusu bina döndürmedi; boş veri yayımlanmıyor.")
    return {"type": "FeatureCollection",
            "properties": {"bbox": BBOX, "source": origin,
                           "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "counts": counts,
                           "notes": "OSM bina/yol way kayıtları. Multipolygon ilişkiler dahil değildir."},
            "features": features}


def from_overpass(session):
    w, s, e, n = BBOX
    area = f"{s},{w},{n},{e}"
    query = (f'[out:json][timeout:90];('
             f'way["building"]({area});way["highway"]({area});'
             f'way["leisure"="park"]({area});way["landuse"~"^(grass|forest|meadow)$"]({area});'
             f'way["natural"="water"]({area}););out geom;')
    for endpoint in OVERPASS:
        try:
            print("Overpass:", endpoint, flush=True)
            r = session.post(endpoint, data={"data": query}, timeout=(15, 115))
            r.raise_for_status()
            return make_geojson(r.json()["elements"], "OpenStreetMap / " + endpoint)
        except (requests.RequestException, ValueError, KeyError, RuntimeError) as exc:
            print("UYARI:", exc, flush=True)
            time.sleep(1)
    return None


def from_osm_api(session):
    """Small-bbox fallback: one OSM API map request, never use for bulk downloads."""
    w, s, e, n = BBOX
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}"
    print("OSM API fallback:", url, flush=True)
    r = session.get(url, timeout=(15, 90))
    r.raise_for_status()
    root = ET.fromstring(r.content)
    nodes = {node.attrib["id"]: (float(node.attrib["lon"]), float(node.attrib["lat"]))
             for node in root.findall("node")}
    ways = []
    for way in root.findall("way"):
        tags = {t.attrib["k"]: t.attrib["v"] for t in way.findall("tag")}
        if not any(k in tags for k in ("building", "highway", "leisure", "landuse", "natural")):
            continue
        geom = []
        for node in way.findall("nd"):
            if node.attrib["ref"] in nodes:
                lon, lat = nodes[node.attrib["ref"]]
                geom.append({"lon": lon, "lat": lat})
        ways.append({"type": "way", "id": int(way.attrib["id"]), "tags": tags, "geometry": geom})
    return make_geojson(ways, "OpenStreetMap / OSM API")


def tile_xy(lon, lat, zoom):
    x = ((lon + 180) / 360) * (2 ** zoom)
    lat = max(-85.0511, min(85.0511, lat))
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * (2 ** zoom)
    return x, y


def fetch_terrain(session, size=33, zoom=13):
    w, s, e, n = BBOX
    cache = {}
    def sample(lon, lat):
        x, y = tile_xy(lon, lat, zoom)
        tx, ty = math.floor(x), math.floor(y)
        key = (tx, ty)
        if key not in cache:
            url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{tx}/{ty}.png"
            r = session.get(url, timeout=(15, 50))
            r.raise_for_status()
            cache[key] = Image.open(io.BytesIO(r.content)).convert("RGB")
        red, green, blue = cache[key].getpixel((
            max(0, min(255, int((x - tx) * 256))),
            max(0, min(255, int((y - ty) * 256)))))
        return round(red * 256 + green + blue / 256 - 32768, 2)
    values = [[sample(w + (e-w)*col/(size-1), n - (n-s)*row/(size-1))
               for col in range(size)] for row in range(size)]
    heights = [h for row in values for h in row]
    return {"bbox": BBOX, "source": "Mapzen Terrain Tiles / AWS Open Data",
            "attribution": "https://github.com/tilezen/joerd/blob/master/docs/attribution.md",
            "width": size, "height": size, "zoom": zoom,
            "min_m": min(heights), "max_m": max(heights), "values_m": values}


def main():
    DATA.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    osm = from_overpass(session)
    if osm is None:
        osm = from_osm_api(session)
    (DATA / "trabzon.geojson").write_text(json.dumps(osm, ensure_ascii=False), encoding="utf-8")
    print("OSM:", osm["properties"]["counts"], flush=True)
    try:
        dem = fetch_terrain(session)
        (DATA / "terrain.json").write_text(json.dumps(dem), encoding="utf-8")
        print("Arazi kotları:", dem["min_m"], dem["max_m"], flush=True)
    except Exception as exc:
        print("UYARI: DEM okunamadı, düz zeminle çalışacak:", exc, flush=True)
        (DATA / "terrain.json").unlink(missing_ok=True)
    print("GeoJSON hazır:", DATA / "trabzon.geojson")


if __name__ == "__main__":
    main()
