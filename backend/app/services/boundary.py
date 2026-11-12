"""Uzbekistan territory boundary check.

Coordinates outside the national territory are rejected on input. A simplified
WGS84 polygon of Uzbekistan, expanded outward by ``BUFFER_M`` metres (3 km) so
that points just across the border are still accepted, is bundled in
``app/assets/uzbekistan_buffered.geojson`` and queried with a prepared Shapely
geometry for fast repeated point-in-polygon tests. The buffered file is generated
by ``scripts/build_buffered_boundary.py``; the frontend uses the same geometry in
``frontend/src/assets/uzbekistan_buffered.json``.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache

from shapely.geometry import Point, shape
from shapely.prepared import prep

# Border tolerance: points up to BUFFER_M outside the national boundary are accepted.
BUFFER_M = 3000.0

_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "uzbekistan_buffered.geojson")

OUTSIDE_MESSAGE = "Oʻzbekiston hududidan tashqarida"


@lru_cache(maxsize=1)
def _prepared():
    try:
        with open(_PATH, encoding="utf-8") as fh:
            gj = json.load(fh)
        geom = shape(gj["geometry"]).buffer(0)
        return prep(geom)
    except Exception:
        return None


def is_in_uzbekistan(lat: float, lon: float) -> bool:
    """Return True if (lat, lon) lies within Uzbekistan.

    If the boundary file is unavailable, returns True (fail-open) so the app
    keeps working rather than rejecting everything.
    """
    prepared = _prepared()
    if prepared is None:
        return True
    try:
        return prepared.contains(Point(lon, lat))
    except Exception:
        return True
