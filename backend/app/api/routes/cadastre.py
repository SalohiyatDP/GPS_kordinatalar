"""Cadastre contour analysis endpoints (STEP 3)."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.api import store
from app.services import cadastre
from app.services import geometry as geo

router = APIRouter(prefix="/api/cadastre", tags=["cadastre"])


class PointPair(BaseModel):
    latitude: float
    longitude: float


class AnalyzeRequest(BaseModel):
    layer_id: str
    points: list[PointPair]
    include_geometry: bool = True


@router.post("/upload")
async def upload_contours(file: UploadFile = File(...)):
    """Upload kontur.zip (shapefile) and load it into memory."""
    raw = await file.read()
    try:
        layer = cadastre.load_contours_from_zip(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to load shapefile: {exc}")

    layer_id = store.store_layer(layer)
    bounds = layer.gdf.total_bounds.tolist()  # [minx, miny, maxx, maxy]
    return {
        "layer_id": layer_id,
        "feature_count": layer.feature_count,
        "original_crs": layer.original_crs,
        "columns": layer.column_map,
        "bounds": bounds,
    }


@router.post("/analyze-points")
def analyze_points(req: AnalyzeRequest):
    layer = store.get_layer(req.layer_id)
    if layer is None:
        raise HTTPException(status_code=404, detail="Layer not found. Upload again.")
    pts = [(p.latitude, p.longitude) for p in req.points]
    return {"points": cadastre.analyze_points(layer, pts)}


@router.post("/analyze-polygon")
def analyze_polygon(req: AnalyzeRequest):
    layer = store.get_layer(req.layer_id)
    if layer is None:
        raise HTTPException(status_code=404, detail="Layer not found. Upload again.")
    pts = [(p.latitude, p.longitude) for p in req.points]
    if len(pts) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 points.")
    polygon = geo.build_polygon(pts)
    analysis = cadastre.analyze_polygon(layer, polygon,
                                        include_geometry=req.include_geometry)
    return analysis.to_dict()


@router.get("/layer/{layer_id}/geojson")
def layer_geojson(layer_id: str, simplify: float = 0.0):
    """Return the contour layer as GeoJSON for map display (optionally simplified)."""
    layer = store.get_layer(layer_id)
    if layer is None:
        raise HTTPException(status_code=404, detail="Layer not found.")
    gdf = layer.gdf
    if simplify > 0:
        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.simplify(simplify, preserve_topology=True)
    import json
    return json.loads(gdf.to_json())


@router.delete("/layer/{layer_id}")
def delete_layer(layer_id: str):
    ok = store.drop_layer(layer_id)
    return {"deleted": ok}
