"""Tests for geometry and export modules."""

from app.services import exporters
from app.services import geometry as geo


# A ~1km square near Tashkent (approx).
SQUARE = [
    (41.000000, 71.000000),
    (41.000000, 71.011900),  # ~1 km east
    (41.009000, 71.011900),  # ~1 km north
    (41.009000, 71.000000),
]


def test_build_polygon_closes_ring():
    poly = geo.build_polygon(SQUARE)
    assert poly.is_valid
    # exterior should be closed (n+1 coords)
    assert list(poly.exterior.coords)[0] == list(poly.exterior.coords)[-1]


def test_area_units_consistent():
    poly = geo.build_polygon(SQUARE)
    area = geo.calculate_area(poly)
    assert area.square_meters > 0
    assert abs(area.hectares - area.square_meters / 10_000) < 1e-6
    assert abs(area.sotix - area.square_meters / 100) < 1e-6
    assert abs(area.square_kilometers - area.square_meters / 1_000_000) < 1e-9
    # Roughly 1 km^2 -> ~100 hectares
    assert 80 < area.hectares < 120


def test_perimeter_positive():
    poly = geo.build_polygon(SQUARE)
    per = geo.calculate_perimeter(poly)
    assert per.meters > 0
    assert abs(per.kilometers - per.meters / 1000) < 1e-9


def test_min_points():
    try:
        geo.build_polygon([(0, 0), (1, 1)])
        assert False, "should raise"
    except ValueError:
        pass


def _points():
    return [
        {"point_number": i + 1, "latitude": lat, "longitude": lon,
         "dms": ""}
        for i, (lat, lon) in enumerate(SQUARE)
    ]


def test_xlsx_export():
    data = exporters.points_to_xlsx(_points())
    assert data[:2] == b"PK"  # xlsx is a zip


def test_kmz_export():
    data = exporters.polygon_to_kmz(_points())
    assert data[:2] == b"PK"  # kmz is a zip


def test_geojson_export():
    poly = geo.polygon_geojson(geo.build_polygon(SQUARE))
    data = exporters.to_geojson(_points(), poly)
    assert b"FeatureCollection" in data


def test_pdf_export():
    poly = geo.build_polygon(SQUARE)
    data = exporters.to_pdf(_points(), geo.calculate_area(poly).to_dict(),
                            geo.calculate_perimeter(poly).to_dict())
    assert data[:4] == b"%PDF"
