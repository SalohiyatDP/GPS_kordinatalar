"""Pydantic request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NormalizeRequest(BaseModel):
    text: str = Field(..., description="Free-form coordinate text, CSV, or URLs")
    resolve_urls: bool = Field(True, description="Resolve map URLs to coordinates")


class PointModel(BaseModel):
    point_number: int
    latitude: float
    longitude: float
    dms: str = ""
    status: str = "valid"
    error: str | None = None


class NormalizeResponse(BaseModel):
    coordinates: list[dict]
    invalid: list[dict]
    duplicates_removed: int
    count: int
    outside_territory: int = 0


class PointInput(BaseModel):
    latitude: float
    longitude: float


class GeometryRequest(BaseModel):
    points: list[PointInput] = Field(..., min_length=3)


class GeometryResponse(BaseModel):
    area: dict
    perimeter: dict
    polygon_geojson: dict
    centroid: list[float]


class ExportRequest(BaseModel):
    points: list[PointInput]
    format: str = Field("xlsx", description="xlsx|kmz|kml|geojson|pdf")
    kind: str = Field("points", description="points|polygon")


class ContourEntry(BaseModel):
    contour: str | int | None = None
    code: str | None = None
    region: str | None = None
    district: str | None = None
    massif: str | None = None
    mfy: str | None = None
    land_type: str | None = None
    contour_area: float = 0
    intersection_area: float = 0
    coverage_percent: float = 0
    status: str = ""


class ReportRequest(BaseModel):
    name: str = "Kadastr tahlili"
    points: list[PointInput]
    contours: list[dict] = []
    summary: str = ""
    format: str = Field("pdf", description="xlsx|pdf|kmz|geojson")
    map_image_base64: str | None = None
    id_label: str = Field("Kontur", description="Tahlil ustuni sarlavhasi: Kontur yoki Kadastr")


class ProjectCreate(BaseModel):
    name: str = "Untitled"
    points: list[dict] = []
    area: dict = {}
    perimeter: dict = {}
    analysis: dict = {}
