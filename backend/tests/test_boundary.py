"""Tests for the Uzbekistan territory boundary filtering."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import boundary

client = TestClient(app)


def test_is_in_uzbekistan_known_points():
    assert boundary.is_in_uzbekistan(41.31, 69.28)   # Tashkent
    assert boundary.is_in_uzbekistan(39.65, 66.96)   # Samarkand
    assert boundary.is_in_uzbekistan(42.46, 59.61)   # Nukus
    assert not boundary.is_in_uzbekistan(43.24, 76.89)  # Almaty (KZ)
    assert not boundary.is_in_uzbekistan(55.75, 37.61)  # Moscow
    assert not boundary.is_in_uzbekistan(38.56, 68.78)  # Dushanbe (TJ)


def test_normalize_filters_outside_territory():
    text = "41.31, 69.28\n43.24, 76.89"  # Tashkent (in) + Almaty (out)
    r = client.post("/api/coordinates/normalize",
                    json={"text": text, "resolve_urls": False})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["outside_territory"] == 1
    assert abs(data["coordinates"][0]["latitude"] - 41.31) < 0.01
    # the rejected point is reported in invalid with a message
    assert any("hududidan" in (c.get("error") or "") for c in data["invalid"])


def test_all_inside_no_removal():
    text = "41.31, 69.28\n39.65, 66.96"
    r = client.post("/api/coordinates/normalize",
                    json={"text": text, "resolve_urls": False})
    data = r.json()
    assert data["count"] == 2
    assert data["outside_territory"] == 0


def _eastmost_vertex():
    """Return (lon, lat) of the easternmost vertex of the original boundary."""
    import json
    import os

    from shapely.geometry import shape

    path = os.path.join(os.path.dirname(boundary.__file__), "..", "assets",
                        "uzbekistan.geojson")
    with open(path, encoding="utf-8") as fh:
        geom = shape(json.load(fh)["geometry"]).buffer(0)
    return max(geom.exterior.coords, key=lambda p: p[0])


def _shift_east_km(lon, lat, km):
    import math
    return lon + km / (111.32 * math.cos(math.radians(lat))), lat


def test_border_tolerance_accepts_points_within_3km():
    lon, lat = _eastmost_vertex()
    # 1 km east of the easternmost border point: just across the border.
    assert boundary.is_in_uzbekistan(*reversed(_shift_east_km(lon, lat, 1.0)))
    # 10 km east: well beyond the tolerance.
    assert not boundary.is_in_uzbekistan(*reversed(_shift_east_km(lon, lat, 10.0)))
