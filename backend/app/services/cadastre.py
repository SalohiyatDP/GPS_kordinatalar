"""Cadastre Contour Analysis (STEP 3).

* Load a contour shapefile (delivered as a .zip with .shp/.dbf/.shx/.prj).
* Detect the CRS and reproject to WGS84 automatically.
* Point-in-contour lookup (region / district / massif / contour number).
* Polygon overlay: which contours intersect, and how much area lies inside.
* Business rule: a contour fully inside the polygon is reported as ``145``;
  a partially covered contour is reported as ``145q`` (q = qism / partial).

Spatial indexing (GeoPandas / RTree sindex) keeps this fast for very large
contour layers (100k+ polygons).
"""

from __future__ import annotations

import glob
import os
import tempfile
import zipfile
from dataclasses import dataclass, field

import geopandas as gpd
from shapely.geometry import Polygon, shape

from .geometry import area_of_geometry

WGS84 = "EPSG:4326"

# Coverage threshold (%) above which a contour counts as fully covered.
FULL_COVERAGE_THRESHOLD = 99.9

# Map logical attribute -> possible column names in the contour layer.
_ATTRIBUTE_ALIASES = {
    "region": ["viloyat", "region", "oblast", "область"],
    "district": ["tuman", "district", "rayon", "район"],
    "massif": ["massiv", "massif", "массив"],
    "contour": ["kontur", "contour", "kontur_raqami", "kontur_no", "номер", "id"],
    "land_type": ["yer_turi", "land_type", "tip"],
    "area_attr": ["maydon", "area", "maydoni", "площадь"],
}


@dataclass
class ContourLayer:
    """A loaded, WGS84 contour layer with a spatial index."""

    gdf: gpd.GeoDataFrame
    column_map: dict[str, str | None]
    original_crs: str | None

    @property
    def feature_count(self) -> int:
        return len(self.gdf)

    def attr(self, row, logical: str, default="") :
        col = self.column_map.get(logical)
        if col and col in row and row[col] is not None:
            return row[col]
        return default


def _resolve_columns(gdf: gpd.GeoDataFrame) -> dict[str, str | None]:
    lower_map = {c.lower(): c for c in gdf.columns}
    resolved: dict[str, str | None] = {}
    for logical, aliases in _ATTRIBUTE_ALIASES.items():
        found = None
        for alias in aliases:
            if alias.lower() in lower_map:
                found = lower_map[alias.lower()]
                break
        resolved[logical] = found
    return resolved


def load_contours_from_zip(zip_bytes: bytes) -> ContourLayer:
    """Load a zipped shapefile into a WGS84 ``ContourLayer``."""
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "kontur.zip")
        with open(zip_path, "wb") as fh:
            fh.write(zip_bytes)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)

        shp_files = glob.glob(os.path.join(tmp, "**", "*.shp"), recursive=True)
        if not shp_files:
            raise ValueError("No .shp file found inside the archive.")

        gdf = gpd.read_file(shp_files[0])
        return _prepare_layer(gdf)


def load_contours_from_path(path: str) -> ContourLayer:
    gdf = gpd.read_file(path)
    return _prepare_layer(gdf)


def _prepare_layer(gdf: gpd.GeoDataFrame) -> ContourLayer:
    original_crs = str(gdf.crs) if gdf.crs is not None else None

    # Detect CRS; if missing assume WGS84, otherwise reproject.
    if gdf.crs is None:
        gdf = gdf.set_crs(WGS84, allow_override=True)
    elif gdf.crs.to_string() != WGS84:
        gdf = gdf.to_crs(WGS84)

    # Keep only valid geometries; fix invalid ones.
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.buffer(0)

    # Build spatial index eagerly (RTree).
    _ = gdf.sindex

    column_map = _resolve_columns(gdf)
    return ContourLayer(gdf=gdf, column_map=column_map, original_crs=original_crs)


# ---------------------------------------------------------------------------
# Point analysis
# ---------------------------------------------------------------------------

def analyze_points(layer: ContourLayer,
                   points: list[tuple[float, float]]) -> list[dict]:
    """For each (lat, lon) point, find the containing contour's attributes."""
    from shapely.geometry import Point

    results = []
    sindex = layer.gdf.sindex
    for i, (lat, lon) in enumerate(points, start=1):
        pt = Point(lon, lat)
        match = None
        for idx in sindex.intersection(pt.bounds):
            row = layer.gdf.iloc[idx]
            if row.geometry.contains(pt):
                match = row
                break
        if match is not None:
            results.append({
                "point_number": i,
                "latitude": lat,
                "longitude": lon,
                "region": _val(layer.attr(match, "region")),
                "district": _val(layer.attr(match, "district")),
                "massif": _val(layer.attr(match, "massif")),
                "contour": _val(layer.attr(match, "contour")),
            })
        else:
            results.append({
                "point_number": i,
                "latitude": lat,
                "longitude": lon,
                "region": None, "district": None,
                "massif": None, "contour": None,
            })
    return results


# ---------------------------------------------------------------------------
# Polygon overlay analysis
# ---------------------------------------------------------------------------

@dataclass
class PolygonAnalysis:
    contours: list[dict] = field(default_factory=list)
    summary: str = ""
    summary_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "contours": self.contours,
            "summary": self.summary,
            "summary_codes": self.summary_codes,
        }


def analyze_polygon(layer: ContourLayer, polygon: Polygon,
                    include_geometry: bool = True) -> PolygonAnalysis:
    """Overlay the user polygon on the contour layer.

    Returns, per intersecting contour: attributes, contour area, intersection
    area, coverage %, status (Full/Partial) and the display code (e.g. 145 or
    145q).
    """
    sindex = layer.gdf.sindex
    candidate_idx = list(sindex.intersection(polygon.bounds))

    rows: list[dict] = []
    codes: list[str] = []

    for idx in candidate_idx:
        row = layer.gdf.iloc[idx]
        geom = row.geometry
        if not geom.intersects(polygon):
            continue
        inter = geom.intersection(polygon)
        if inter.is_empty:
            continue

        contour_area = area_of_geometry(geom)
        inter_area = area_of_geometry(inter)
        if contour_area <= 0:
            continue

        coverage = inter_area / contour_area * 100.0
        is_full = coverage >= FULL_COVERAGE_THRESHOLD

        contour_no = _val(layer.attr(row, "contour"))
        code = _format_code(contour_no, is_full)
        codes.append(code)

        entry = {
            "contour": contour_no,
            "code": code,
            "region": _val(layer.attr(row, "region")),
            "district": _val(layer.attr(row, "district")),
            "massif": _val(layer.attr(row, "massif")),
            "land_type": _val(layer.attr(row, "land_type")),
            "contour_area": round(contour_area, 2),
            "intersection_area": round(inter_area, 2),
            "coverage_percent": round(coverage, 2),
            "status": "Full" if is_full else "Partial",
        }
        if include_geometry:
            import json

            from shapely.geometry import mapping
            entry["geometry"] = mapping(inter)
        rows.append(entry)

    # Order contours by contour number where possible.
    rows.sort(key=lambda r: _sort_key(r["contour"]))
    codes = [r["code"] for r in rows]

    summary = _build_summary(codes)
    return PolygonAnalysis(contours=rows, summary=summary, summary_codes=codes)


def _format_code(contour_no, is_full: bool) -> str:
    base = "" if contour_no is None else str(contour_no)
    return base if is_full else f"{base}q"


def _build_summary(codes: list[str]) -> str:
    if not codes:
        return "The polygon does not intersect any contour."
    joined = ", ".join(codes)
    return (
        f"The polygon intersects: {joined}. "
        f'Where "q" means only part of the contour lies within the polygon.'
    )


def _val(v):
    if v is None or v == "":
        return None
    return v


def _sort_key(contour_no):
    try:
        return (0, float(str(contour_no)))
    except (ValueError, TypeError):
        return (1, str(contour_no))
