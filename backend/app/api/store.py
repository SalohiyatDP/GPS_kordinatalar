"""In-memory store for uploaded contour layers.

Loading a large shapefile is expensive, so we keep the parsed ``ContourLayer``
in memory keyed by an upload id and reuse it across analysis requests.
"""

from __future__ import annotations

import threading
import uuid

from app.services.cadastre import ContourLayer

_LOCK = threading.Lock()
_LAYERS: dict[str, ContourLayer] = {}


def store_layer(layer: ContourLayer) -> str:
    layer_id = uuid.uuid4().hex
    with _LOCK:
        _LAYERS[layer_id] = layer
    return layer_id


def get_layer(layer_id: str) -> ContourLayer | None:
    with _LOCK:
        return _LAYERS.get(layer_id)


def drop_layer(layer_id: str) -> bool:
    with _LOCK:
        return _LAYERS.pop(layer_id, None) is not None
