"""Full end-to-end API integration test using FastAPI TestClient."""

import io
import zipfile

import geopandas as gpd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from app.main import app

client = TestClient(app)


def _build_contour_zip() -> bytes:
    c145 = Polygon([(69.0, 41.0), (69.01, 41.0), (69.01, 41.01), (69.0, 41.01)])
    c146 = Polygon([(69.01, 41.0), (69.02, 41.0), (69.02, 41.01), (69.01, 41.01)])
    gdf = gpd.GeoDataFrame(
        {
            "viloyat": ["Tashkent", "Tashkent"],
            "tuman": ["Yunusabad", "Yunusabad"],
            "massiv": ["M1", "M2"],
            "kontur": ["145", "146"],
        },
        geometry=[c145, c146],
        crs="EPSG:4326",
    )
    import tempfile, os
    buf = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "kontur.shp")
        gdf.to_file(path)
        with zipfile.ZipFile(buf, "w") as zf:
            for f in os.listdir(tmp):
                zf.write(os.path.join(tmp, f), f)
    return buf.getvalue()


def test_full_workflow():
    # 1. Normalize mixed-format coordinates.
    text = (
        "41 0 0 N, 69 0 0 E\n"
        "41.01, 69.0\n"
        "41.01, 69.015\n"
        "41.0, 69.015\n"
        "41.01, 69.0"  # duplicate of line 2
    )
    r = client.post("/api/coordinates/normalize",
                    json={"text": text, "resolve_urls": False})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 4
    assert data["duplicates_removed"] == 1
    points = [{"latitude": p["latitude"], "longitude": p["longitude"]}
              for p in data["coordinates"]]

    # 2. Compute geometry.
    g = client.post("/api/geometry/compute", json={"points": points})
    assert g.status_code == 200
    geo = g.json()
    assert geo["area"]["square_meters"] > 0
    assert geo["perimeter"]["meters"] > 0

    # 3. Export polygon KMZ.
    e = client.post("/api/geometry/export",
                    json={"points": points, "format": "kmz", "kind": "polygon"})
    assert e.status_code == 200
    assert e.content[:2] == b"PK"

    # 4. Upload contour shapefile.
    zip_bytes = _build_contour_zip()
    u = client.post("/api/cadastre/upload",
                    files={"file": ("kontur.zip", zip_bytes, "application/zip")})
    assert u.status_code == 200, u.text
    layer_id = u.json()["layer_id"]
    assert u.json()["feature_count"] == 2
    assert u.json()["columns"]["contour"] == "kontur"

    # 5. Analyze polygon overlay.
    a = client.post("/api/cadastre/analyze-polygon",
                    json={"layer_id": layer_id, "points": points,
                          "include_geometry": True})
    assert a.status_code == 200, a.text
    analysis = a.json()
    codes = analysis["summary_codes"]
    assert "145" in codes  # fully covered contour
    # 146 partially covered -> ends with q
    assert any(c.endswith("q") for c in codes)

    # 6. Generate Analysis.pdf report.
    contours_no_geom = [{k: v for k, v in c.items() if k != "geometry"}
                        for c in analysis["contours"]]
    rep = client.post("/api/reports/generate",
                      json={"name": "Test", "points": points,
                            "contours": contours_no_geom,
                            "summary": analysis["summary"], "format": "pdf"})
    assert rep.status_code == 200, rep.text
    assert rep.content[:4] == b"%PDF"

    # 7. Generate Analysis.xlsx report.
    rep2 = client.post("/api/reports/generate",
                       json={"name": "Test", "points": points,
                             "contours": contours_no_geom,
                             "summary": analysis["summary"], "format": "xlsx"})
    assert rep2.status_code == 200
    assert rep2.content[:2] == b"PK"


def test_project_persistence():
    payload = {"name": "Proj1", "points": [{"point_number": 1}], "area": {"sotix": 5}}
    c = client.post("/api/projects", json=payload)
    assert c.status_code == 200
    pid = c.json()["id"]
    g = client.get(f"/api/projects/{pid}")
    assert g.status_code == 200
    assert g.json()["name"] == "Proj1"
    d = client.delete(f"/api/projects/{pid}")
    assert d.json()["deleted"] is True
