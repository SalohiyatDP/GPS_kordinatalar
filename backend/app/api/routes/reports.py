"""Automatic cadastre report generator endpoints (STEP 5)."""

from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas.models import ReportRequest
from app.services import exporters
from app.services import geometry as geo
from app.services.normalizer import decimal_to_dms

router = APIRouter(prefix="/api/reports", tags=["reports"])

_MEDIA = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
    "kmz": "application/vnd.google-earth.kmz",
    "geojson": "application/geo+json",
}


@router.post("/generate")
def generate(req: ReportRequest):
    """Generate Analysis.{xlsx|pdf|kmz|geojson} combining geometry + contours."""
    fmt = req.format.lower()
    if fmt not in _MEDIA:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")
    if len(req.points) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 points.")

    points = [
        {"point_number": i + 1, "latitude": p.latitude, "longitude": p.longitude,
         "dms": f"{decimal_to_dms(p.latitude, True)} {decimal_to_dms(p.longitude, False)}"}
        for i, p in enumerate(req.points)
    ]
    pts = [(p["latitude"], p["longitude"]) for p in points]
    polygon = geo.build_polygon(pts)
    area = geo.calculate_area(polygon).to_dict()
    perimeter = geo.calculate_perimeter(polygon).to_dict()

    if fmt == "xlsx":
        data = exporters.analysis_to_xlsx(points, area, perimeter,
                                          req.contours, req.summary, req.id_label,
                                          secondary=req.secondary)
        filename = "Analysis.xlsx"
    elif fmt == "pdf":
        map_png = None
        if req.map_image_base64:
            try:
                b64 = req.map_image_base64.split(",")[-1]
                map_png = base64.b64decode(b64)
            except Exception:
                map_png = None
        data = exporters.to_pdf(points, area, perimeter, req.contours,
                                req.summary, title=req.name, map_image_png=map_png,
                                id_label=req.id_label, secondary=req.secondary)
        filename = "Analysis.pdf"
    elif fmt == "kmz":
        data = exporters.analysis_to_kmz(points, req.contours)
        filename = "Analysis.kmz"
    else:  # geojson
        data = exporters.to_geojson(points, geo.polygon_geojson(polygon), req.contours)
        filename = "Analysis.geojson"

    return Response(
        content=data,
        media_type=_MEDIA[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
