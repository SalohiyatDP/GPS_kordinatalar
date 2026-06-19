"""Geometry & export endpoints (STEP 2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas.models import (ExportRequest, GeometryRequest,
                                GeometryResponse)
from app.services import exporters
from app.services import geometry as geo

router = APIRouter(prefix="/api/geometry", tags=["geometry"])

_MEDIA = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "kmz": "application/vnd.google-earth.kmz",
    "kml": "application/vnd.google-earth.kml+xml",
    "geojson": "application/geo+json",
    "pdf": "application/pdf",
}


@router.post("/compute", response_model=GeometryResponse)
def compute(req: GeometryRequest):
    """Build the polygon and return area, perimeter, centroid and GeoJSON."""
    pts = [(p.latitude, p.longitude) for p in req.points]
    try:
        polygon = geo.build_polygon(pts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    area = geo.calculate_area(polygon)
    perimeter = geo.calculate_perimeter(polygon)
    lat, lon = geo.centroid(pts)
    return GeometryResponse(
        area=area.to_dict(),
        perimeter=perimeter.to_dict(),
        polygon_geojson=geo.polygon_geojson(polygon),
        centroid=[lat, lon],
    )


@router.post("/export")
def export(req: ExportRequest):
    """Export points or polygon to xlsx / kmz / kml / geojson / pdf."""
    points = [
        {"point_number": i + 1, "latitude": p.latitude, "longitude": p.longitude,
         "dms": _dms(p.latitude, p.longitude)}
        for i, p in enumerate(req.points)
    ]
    fmt = req.format.lower()
    kind = req.kind.lower()

    if fmt not in _MEDIA:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    if fmt == "xlsx":
        data = exporters.points_to_xlsx(points)
        filename = "points.xlsx"
    elif fmt == "geojson":
        polygon_gj = None
        if kind == "polygon" and len(points) >= 3:
            polygon_gj = geo.polygon_geojson(
                geo.build_polygon([(p["latitude"], p["longitude"]) for p in points]))
        data = exporters.to_geojson(points, polygon_gj)
        filename = f"{kind}.geojson"
    elif fmt in ("kmz", "kml"):
        if kind == "polygon":
            data = exporters.polygon_to_kmz(points)
        else:
            data = exporters.points_to_kmz(points)
        filename = f"{kind}.kmz"
    elif fmt == "pdf":
        polygon = geo.build_polygon([(p["latitude"], p["longitude"]) for p in points])
        area = geo.calculate_area(polygon).to_dict()
        perimeter = geo.calculate_perimeter(polygon).to_dict()
        data = exporters.to_pdf(points, area, perimeter, title="Koordinatalar hisoboti")
        filename = "report.pdf"
    else:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Unsupported format")

    return Response(
        content=data,
        media_type=_MEDIA[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _dms(lat: float, lon: float) -> str:
    from app.services.normalizer import decimal_to_dms
    return f"{decimal_to_dms(lat, True)} {decimal_to_dms(lon, False)}"
