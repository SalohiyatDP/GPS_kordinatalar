# API Reference

Base URL: `/api`. Interactive Swagger UI is available at `/docs` and ReDoc at
`/redoc`.

All request/response bodies are JSON unless noted. File uploads use
`multipart/form-data`. Export endpoints return binary files with a
`Content-Disposition` attachment header.

---

## Health

### `GET /api/health`
Returns service status.
```json
{ "status": "ok", "app": "Smart Coordinate & Cadastre Analyzer", "version": "1.0.0" }
```

---

## Step 1 — Coordinates

### `POST /api/coordinates/normalize`
Normalize free-form text, CSV rows, or map URLs.

**Request**
```json
{ "text": "41 7 54.29 N, 71 37 49.17 E\n41.131747, 71.630325", "resolve_urls": true }
```

**Response**
```json
{
  "coordinates": [
    { "point_number": 1, "latitude": 41.131747, "longitude": 71.630325,
      "dms": "41°07'54.29\"N 71°37'49.17\"E", "status": "valid", "error": null }
  ],
  "invalid": [],
  "duplicates_removed": 0,
  "count": 1
}
```

### `POST /api/coordinates/upload`
`multipart/form-data` with a `file` field (`.txt`, `.csv`, `.xlsx`). Same
response shape as `/normalize`.

---

## Step 2 — Geometry & Export

### `POST /api/geometry/compute`
**Request**
```json
{ "points": [ { "latitude": 41.0, "longitude": 71.0 }, ... ] }   // ≥ 3 points
```
**Response**
```json
{
  "area": { "square_meters": 0, "hectares": 0, "square_kilometers": 0, "sotix": 0 },
  "perimeter": { "meters": 0, "kilometers": 0 },
  "polygon_geojson": { "type": "Polygon", "coordinates": [...] },
  "centroid": [lat, lon]
}
```

### `POST /api/geometry/export`
**Request**
```json
{ "points": [...], "format": "xlsx|kmz|kml|geojson|pdf", "kind": "points|polygon" }
```
Returns the binary file (`points.xlsx`, `polygon.kmz`, …).

---

## Step 3 — Cadastre

### `POST /api/cadastre/upload`
`multipart/form-data` with a `file` field = `kontur.zip` (zipped shapefile).
```json
{ "layer_id": "abc...", "feature_count": 1234, "original_crs": "EPSG:32642",
  "columns": { "region": "viloyat", "district": "tuman", "contour": "kontur", ... },
  "bounds": [minx, miny, maxx, maxy] }
```

### `POST /api/cadastre/analyze-polygon`
```json
{ "layer_id": "abc...", "points": [...], "include_geometry": true }
```
**Response**
```json
{
  "contours": [
    { "contour": "145", "code": "145", "region": "...", "district": "...",
      "massif": "...", "contour_area": 0, "intersection_area": 0,
      "coverage_percent": 100.0, "status": "Full", "geometry": { ... } }
  ],
  "summary": "The polygon intersects: 145, 146q. ...",
  "summary_codes": ["145", "146q"]
}
```

### `POST /api/cadastre/analyze-points`
Same request body; returns the containing contour attributes per point.

### `GET /api/cadastre/layer/{layer_id}/geojson?simplify=0.0002`
Returns the (optionally simplified) contour layer as GeoJSON for map display.

### `DELETE /api/cadastre/layer/{layer_id}`
Frees the in-memory layer.

---

## Step 5 — Reports

### `POST /api/reports/generate`
```json
{ "name": "Cadastre Analysis", "points": [...], "contours": [...],
  "summary": "...", "format": "xlsx|pdf|kmz|geojson", "map_image_base64": null }
```
Returns `Analysis.{ext}` as a binary download.

---

## Projects (persistence)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/projects` | Create/save a project |
| `GET`  | `/api/projects` | List projects |
| `GET`  | `/api/projects/{id}` | Get a project |
| `DELETE` | `/api/projects/{id}` | Delete a project |
