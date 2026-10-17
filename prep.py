import json, re, requests
from datetime import date

LAYERS = {
    "public":  "https://gisweb.miamidade.gov/arcgis/rest/services/MD_Emaps/MapServer/25/query",
    "private": "https://gisweb.miamidade.gov/ArcGIS/rest/services/MD_LandInformation/MapServer/56/query",
}
GRADE = {"PK": -1, "K": 0, "KG": 0}

def g(props, *keys):
    low = {k.lower(): v for k, v in props.items()}
    for k in keys:
        v = low.get(k.lower())
        if v not in (None, ""):
            return v
    return None

def grade_range(text):
    if not text:
        return None, None
    parts = re.findall(r"PK|KG|K|\d{1,2}", str(text).upper())
    nums = [GRADE.get(p, int(p) if p.isdigit() else None) for p in parts]
    nums = [n for n in nums if n is not None]
    return (min(nums), max(nums)) if nums else (None, None)

def fetch(url):
    params = {"where": "1=1", "outFields": "*", "f": "geojson", "outSR": 4326}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()["features"]

schools = []
for kind, url in LAYERS.items():
    for i, f in enumerate(fetch(url)):
        p, geom = f["properties"], f.get("geometry") or {}
        coords = geom.get("coordinates") or [g(p, "LON"), g(p, "LAT")]
        lo, hi = grade_range(g(p, "GRADES", "GRDLEVEL"))
        schools.append({
            "id": f"{kind}-{i}",
            "name": g(p, "NAME"),
            "type": kind,
            "grade_min": lo, "grade_max": hi,
            "lon": coords[0], "lat": coords[1],
            "address": g(p, "ADDRESS"),
            "city": g(p, "CITY"),
            "zip": g(p, "ZIPCODE", "ZIP"),
            "enrollment": g(p, "ENROLLMNT"),
            "website": g(p, "WEBSITE"),
            "phone": g(p, "PHONE"),
            "source": url.rsplit("/query", 1)[0],
            "pulled": str(date.today()),
        })

json.dump(schools, open("schools.json", "w"), indent=1)
print(len(schools), "schools saved")
