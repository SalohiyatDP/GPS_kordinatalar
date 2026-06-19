"""Tests for the cadastre contour analysis module, including the
full/partial (q) business rule."""

import io
import zipfile

import geopandas as gpd
from shapely.geometry import Polygon

from app.services import cadastre
from app.services import geometry as geo


def _make_contour_layer():
    """Two adjacent square contours.

    Contour 145: x in [0,1], y in [0,1]
    Contour 146: x in [1,2], y in [0,1]
    """
    c145 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    c146 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    gdf = gpd.GeoDataFrame(
        {
            "viloyat": ["Tashkent", "Tashkent"],
            "tuman": ["Yunusabad", "Yunusabad"],
            "massiv": ["M1", "M2"],
            "kontur": ["145", "146"],
            "yer_turi": ["ekin", "ekin"],
        },
        geometry=[c145, c146],
        crs="EPSG:4326",
    )
    return cadastre._prepare_layer(gdf)


def test_column_resolution():
    layer = _make_contour_layer()
    assert layer.column_map["region"] == "viloyat"
    assert layer.column_map["district"] == "tuman"
    assert layer.column_map["massif"] == "massiv"
    assert layer.column_map["contour"] == "kontur"


def test_full_contour_no_q():
    """Polygon fully covers contour 145 -> code '145' (no q)."""
    layer = _make_contour_layer()
    # Polygon covering all of 145 and half of 146.
    poly = Polygon([(0, 0), (1.5, 0), (1.5, 1), (0, 1)])
    analysis = cadastre.analyze_polygon(layer, poly, include_geometry=False)
    by_contour = {c["contour"]: c for c in analysis.contours}

    assert by_contour["145"]["status"] == "Full"
    assert by_contour["145"]["code"] == "145"
    assert by_contour["146"]["status"] == "Partial"
    assert by_contour["146"]["code"] == "146q"
    assert by_contour["146"]["coverage_percent"] < 100


def test_summary_codes():
    layer = _make_contour_layer()
    poly = Polygon([(0, 0), (1.5, 0), (1.5, 1), (0, 1)])
    analysis = cadastre.analyze_polygon(layer, poly, include_geometry=False)
    assert analysis.summary_codes == ["145", "146q"]
    assert "145" in analysis.summary
    assert "146q" in analysis.summary


def test_point_analysis():
    layer = _make_contour_layer()
    # (lat, lon) -> point at lon=0.5 lat=0.5 is in 145; lon=1.5 in 146.
    pts = [(0.5, 0.5), (0.5, 1.5)]
    res = cadastre.analyze_points(layer, pts)
    assert res[0]["contour"] == "145"
    assert res[0]["region"] == "Tashkent"
    assert res[1]["contour"] == "146"


def test_load_from_zip(tmp_path):
    """Write a real shapefile, zip it, and load it back."""
    layer = _make_contour_layer()
    shp_dir = tmp_path / "shp"
    shp_dir.mkdir()
    shp_path = shp_dir / "kontur.shp"
    layer.gdf.to_file(shp_path)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for f in shp_dir.iterdir():
            zf.write(f, f.name)

    loaded = cadastre.load_contours_from_zip(buf.getvalue())
    assert loaded.feature_count == 2
    assert loaded.column_map["contour"] == "kontur"
