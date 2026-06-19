"""Geometry module (STEP 2).

Builds a polygon from an ordered list of coordinates and computes geodesic
area and perimeter (accurate on the WGS84 ellipsoid, suitable for large areas).
"""

from __future__ import annotations

from dataclasses import dataclass

from pyproj import Geod
from shapely.geometry import LineString, Point, Polygon, mapping

_GEOD = Geod(ellps="WGS84")

# Unit conversions from square meters.
_SOTIX = 100.0        # 1 sotix (sotka) = 100 m²
_HECTARE = 10_000.0
_SQKM = 1_000_000.0


@dataclass
class AreaResult:
    square_meters: float
    hectares: float
    square_kilometers: float
    sotix: float

    def to_dict(self) -> dict:
        return {
            "square_meters": round(self.square_meters, 2),
            "hectares": round(self.hectares, 4),
            "square_kilometers": round(self.square_kilometers, 6),
            "sotix": round(self.sotix, 2),
        }


@dataclass
class PerimeterResult:
    meters: float
    kilometers: float

    def to_dict(self) -> dict:
        return {
            "meters": round(self.meters, 2),
            "kilometers": round(self.kilometers, 4),
        }


def build_polygon(points: list[tuple[float, float]]) -> Polygon:
    """Build a polygon from ordered (lat, lon) points.

    The polygon is closed automatically (1 -> 2 -> ... -> n -> 1).
    Shapely uses (x, y) = (lon, lat) ordering.
    """
    if len(points) < 3:
        raise ValueError("A polygon requires at least 3 points.")
    ring = [(lon, lat) for lat, lon in points]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return Polygon(ring)


def build_linestring(points: list[tuple[float, float]]) -> LineString:
    return LineString([(lon, lat) for lat, lon in points])


def calculate_area(polygon: Polygon) -> AreaResult:
    """Geodesic area of a polygon in multiple units."""
    area_m2, _ = _GEOD.geometry_area_perimeter(polygon)
    area_m2 = abs(area_m2)
    return AreaResult(
        square_meters=area_m2,
        hectares=area_m2 / _HECTARE,
        square_kilometers=area_m2 / _SQKM,
        sotix=area_m2 / _SOTIX,
    )


def calculate_perimeter(polygon: Polygon) -> PerimeterResult:
    """Geodesic perimeter of a polygon."""
    _, perimeter_m = _GEOD.geometry_area_perimeter(polygon)
    perimeter_m = abs(perimeter_m)
    return PerimeterResult(meters=perimeter_m, kilometers=perimeter_m / 1000.0)


def area_of_geometry(geom) -> float:
    """Absolute geodesic area in m² for any (multi)polygon geometry."""
    if geom.is_empty:
        return 0.0
    area_m2, _ = _GEOD.geometry_area_perimeter(geom)
    return abs(area_m2)


def polygon_geojson(polygon: Polygon) -> dict:
    return mapping(polygon)


def centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Return (lat, lon) centroid of the points."""
    if not points:
        return (0.0, 0.0)
    poly_points = [Point(lon, lat) for lat, lon in points]
    xs = sum(p.x for p in poly_points) / len(poly_points)
    ys = sum(p.y for p in poly_points) / len(poly_points)
    return (ys, xs)
