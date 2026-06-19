"""Tests for robust column resolution against real (truncated, Uzbek) shapefile
field names like the user's kontur.shp."""

import geopandas as gpd
from shapely.geometry import Polygon

from app.services import cadastre


# Real-world style columns (DBF truncates field names to 10 chars).
REAL_COLUMNS = [
    "FID", "Kontur_raq", "Umumiy_may", "Haydalma_t", "Haydalma_1",
    "Dehqon_maj", "Boglar_ega", "Uzumzor_ma", "Tutzor", "Buz_yer_ot",
    "Tomorqa", "Urmonzor", "Ariq_kanal", "Kol", "Tuproq", "MFY", "Massiv",
    "Maxsus", "Tuman", "Viloyat", "Yagona_kon", "Dol_konta",
    "SHAPE_Leng", "SHAPE_Area",
]


def _make_real_layer():
    c1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    c2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
    data = {col: ["", ""] for col in REAL_COLUMNS}
    data["Kontur_raq"] = [307.0, 38.0]   # numeric contour numbers
    data["Viloyat"] = ["Farg'ona", "Farg'ona"]
    data["Tuman"] = ["Quvasoy", "Quvasoy"]
    data["MFY"] = ["Navbahor", "Navbahor"]
    data["Massiv"] = ["Sharq", "Sharq"]
    data["Umumiy_may"] = [2.27, 0.85]
    gdf = gpd.GeoDataFrame(data, geometry=[c1, c2], crs="EPSG:4326")
    return cadastre._prepare_layer(gdf)


def test_resolves_truncated_uzbek_columns():
    layer = _make_real_layer()
    cm = layer.column_map
    assert cm["contour"] == "Kontur_raq"
    assert cm["region"] == "Viloyat"
    assert cm["district"] == "Tuman"
    assert cm["massif"] == "Massiv"
    assert cm["mfy"] == "MFY"
    assert cm["area_attr"] == "Umumiy_may"


def test_numeric_contour_rendered_without_decimal():
    layer = _make_real_layer()
    # Polygon fully covering contour 307 and partially covering 38.
    poly = Polygon([(0, 0), (1.5, 0), (1.5, 1), (0, 1)])
    analysis = cadastre.analyze_polygon(layer, poly, include_geometry=False)
    by = {c["contour"]: c for c in analysis.contours}
    assert "307" in by                       # not "307.0"
    assert by["307"]["code"] == "307"        # full
    assert by["307"]["region"] == "Farg'ona"
    assert by["307"]["massif"] == "Sharq"
    assert by["307"]["mfy"] == "Navbahor"
    assert by["38"]["code"] == "38q"         # partial
    assert analysis.summary_codes == ["38q", "307"]


def test_point_analysis_real_columns():
    layer = _make_real_layer()
    res = cadastre.analyze_points(layer, [(0.5, 0.5)])
    assert res[0]["contour"] == "307"
    assert res[0]["district"] == "Quvasoy"


def test_fallback_to_yagona_kon_when_no_kontur():
    """If there's no Kontur_* column, fall back to Yagona_kon."""
    cols = [c for c in REAL_COLUMNS if not c.startswith("Kontur")]
    c1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    data = {col: [""] for col in cols}
    data["Yagona_kon"] = ["A-12"]
    gdf = gpd.GeoDataFrame(data, geometry=[c1], crs="EPSG:4326")
    layer = cadastre._prepare_layer(gdf)
    assert layer.column_map["contour"] == "Yagona_kon"



def test_uzkad_cadastral_and_vacant():
    """UZKAD: intersect by cadastral_ number and report vacant (boʻsh) land."""
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    p2 = Polygon([(1, 0), (1.5, 0), (1.5, 1), (1, 1)])
    gdf = gpd.GeoDataFrame(
        {
            "cadastral_": ["06:09:01:001", "06:09:01:002"],
            "Viloyat": ["Namangan", "Namangan"],
            "Tuman": ["Kosonsoy", "Kosonsoy"],
        },
        geometry=[p1, p2], crs="EPSG:4326",
    )
    layer = cadastre._prepare_layer(gdf)
    assert layer.column_map["cadastral"] == "cadastral_"

    # Polygon spans x[0,2]; parcels cover [0,1.5] -> vacant is x[1.5,2] (25%).
    poly = Polygon([(0, 0), (2, 0), (2, 1), (0, 1)])
    res = cadastre.analyze_polygon(
        layer, poly, include_geometry=False,
        id_field="cadastral", append_q=False, compute_vacant=True)

    codes = [c["code"] for c in res.contours]
    assert "06:09:01:001" in codes
    assert "06:09:01:002" in codes
    # No "q" suffix for cadastral numbers.
    assert all(not c.endswith("q") for c in codes if c != "Boʻsh")
    vacant = [c for c in res.contours if c["status"] == "Vacant"]
    assert len(vacant) == 1
    assert abs(vacant[0]["coverage_percent"] - 25.0) < 1.0
    assert "kadastr" in res.summary.lower()
    assert "ga" in res.summary


def test_no_vacant_when_fully_covered():
    p1 = Polygon([(0, 0), (2, 0), (2, 1), (0, 1)])
    gdf = gpd.GeoDataFrame({"cadastral_": ["X-1"]}, geometry=[p1], crs="EPSG:4326")
    layer = cadastre._prepare_layer(gdf)
    poly = Polygon([(0.2, 0.2), (1.0, 0.2), (1.0, 0.8), (0.2, 0.8)])
    res = cadastre.analyze_polygon(
        layer, poly, include_geometry=False,
        id_field="cadastral", append_q=False, compute_vacant=True)
    assert not any(c["status"] == "Vacant" for c in res.contours)
