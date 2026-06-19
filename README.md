# Smart Coordinate & Cadastre Analyzer

A professional, GIS-grade web application for processing coordinates, generating
polygons, exporting GIS files, and analyzing cadastral contours. Built for
cadastre specialists, GIS engineers, land-management organizations, surveyors,
and government agencies.

> Languages: **Uzbek** (default), **Russian**, **English**.

---

## ✨ Features

| Step | Capability |
|------|------------|
| **1. Normalization** | Parse coordinates from DMS, decimal, Russian Cyrillic (`С/Ю/В/З`), mixed formats, map URLs (Google / Yandex / 2GIS), and TXT/CSV/XLSX files. Standardize to `41°07'54.29"N 71°37'49.17"E`, validate ranges, remove duplicates. |
| **2. Geometry & Export** | Editable, reorderable point table → polygon generation → geodesic area (m² / hectares / km² / sotix) & perimeter (m / km). Export **XLSX, KML, KMZ, GeoJSON, PDF**. |
| **3. Cadastre Analysis** | Upload `kontur.zip` shapefile, auto-detect & reproject CRS, point-in-contour lookup, polygon overlay/intersection with coverage %, and the **full / partial (`q`)** business rule. |
| **4. Interactive Map** | Leaflet GIS map: points (blue), polygon (red), full contours (green), partial contours (yellow); zoom, layer switch, base/satellite. |
| **5. Reports** | One-click `Analysis.xlsx`, `Analysis.pdf`, `Analysis.kmz`, `Analysis.geojson`. |

### The full / partial business rule

```
coverage_percent = intersection_area / contour_area × 100
coverage ≥ 99.9%  →  "145"   (Full)
coverage  < 99.9% →  "145q"  (Partial — q = qism)
```

Example summary: *“The polygon intersects: 145, 146q, 147, 148q.”*

---

## 🧱 Tech Stack

**Frontend:** React 19 · TypeScript · Vite · Tailwind CSS · Leaflet · React Query · Zustand
**Backend:** Python · FastAPI · GeoPandas · Shapely · PyProj · Fiona · Pyogrio · RTree
**Exports:** openpyxl (XLSX) · simplekml (KML/KMZ) · ReportLab (PDF) · GeoJSON
**Database:** SQLite (SQLAlchemy 2.0)

---

## 🚀 Quick Start (Docker)

```bash
docker compose up --build
```

- Frontend: <http://localhost:8080>
- Backend API + Swagger docs: <http://localhost:8000/docs>

## 🛠️ Local Development

See [docs/INSTALL.md](docs/INSTALL.md) for full instructions.

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

---

## 🧪 Tests

```bash
cd backend && source .venv/bin/activate
pytest -q          # 30 tests: normalization, geometry, exports, cadastre, full API
```

---

## 📚 Documentation

- [Installation Guide](docs/INSTALL.md)
- [API Reference](docs/API.md)
- [Database Schema](docs/DATABASE.md)

---

## 📈 Performance

Designed for large datasets (100k+ contour polygons, 10k+ coordinates) using
GeoPandas/RTree spatial indexing for overlay operations and geometry simplification
for map rendering.
