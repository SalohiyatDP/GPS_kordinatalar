"""NGIS (open.ngis.uz) live cadastral intersection analysis.

Queries the public UZKAD ArcGIS FeatureServer layers for parcels intersecting
the user's polygon bounding box, then reuses the standard polygon-overlay logic
(coverage %, full/partial, vacant land) from :mod:`cadastre`.

Note: db.ngis.uz is reachable from within Uzbekistan. The query runs on the
server side, so there is no browser CORS issue.
"""

from __future__ import annotations

import geopandas as gpd
import httpx
import pandas as pd

from . import cadastre
from . import geometry as geo

NGIS_BASE = "https://db.ngis.uz/db/rest/services/UZKAD"

# Service id -> Uzbek label (also the displayed land-type / layer name).
NGIS_LABELS: dict[str, str] = {
    "TURAR_UZKAD_DB16": "Turar-joy yerlar",
    "NOTURAR_UZKAD_DB16": "Noturar yerlar",
    "AGR_ONLY_UZKAD_DB16": "Qishloq xoʻjaligi yerlar",
    "FOREST_UZKAD_DB16": "Oʻrmon yerlar",
    "WATER_UZKAD_DB16": "Suv yerlar",
    "AVTOYUL_UZKAD_DB16": "Avtoyoʻl yerlar",
    "DZY_UZKAD_DB16": "Davlat zaxira yerlar",
    "MUHOFAZA_UZKAD_DB16": "Muhofaza yerlar",
    "MAHALLA_UZKAD_DB16": "Mahalla",
}


def _query_service(service: str, bounds: tuple[float, float, float, float],
                   timeout: float) -> dict:
    """Query one FeatureServer layer for features intersecting the bbox."""
    minx, miny, maxx, maxy = bounds
    url = f"{NGIS_BASE}/{service}/FeatureServer/0/query"
    params = {
        "f": "geojson",
        "where": "1=1",
        "outFields": "cadastral_number,property_kind,id",
        "geometry": f"{minx},{miny},{maxx},{maxy}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "true",
        "resultRecordCount": "3000",
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def analyze_ngis(points: list[tuple[float, float]], services: list[str],
                 include_geometry: bool = True, compute_vacant: bool = True,
                 timeout: float = 40.0) -> cadastre.PolygonAnalysis:
    """Analyze polygon intersection against the selected live NGIS layers."""
    polygon = geo.build_polygon(points)
    bounds = polygon.bounds  # (minx, miny, maxx, maxy) in lon/lat

    frames: list[gpd.GeoDataFrame] = []
    for service in services:
        label = NGIS_LABELS.get(service, service)
        gj = _query_service(service, bounds, timeout)
        feats = (gj or {}).get("features") or []
        if not feats:
            continue
        gdf = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        if gdf.empty:
            continue
        # Tag every feature with its land-type / layer label.
        gdf["yer_turi"] = label
        frames.append(gdf)

    if not frames:
        return cadastre.PolygonAnalysis(
            contours=[],
            summary="Tanlangan NGIS qatlamlarida poligon bilan kesishuvchi "
                    "uchastka topilmadi.",
            summary_codes=[],
        )

    combined = pd.concat(frames, ignore_index=True)
    gdf = gpd.GeoDataFrame(combined, geometry="geometry", crs="EPSG:4326")
    layer = cadastre._prepare_layer(gdf)
    return cadastre.analyze_polygon(
        layer, polygon, include_geometry=include_geometry,
        id_field="cadastral", append_q=False, compute_vacant=compute_vacant)
