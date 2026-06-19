# Installation Guide

## Prerequisites

- **[Python 3.10–3.13](https://www.python.org/downloads/)**
- **[Node.js 18+](https://nodejs.org/en/download)** (20/22 recommended)
- (Optional) **[Docker](https://www.docker.com/products/docker-desktop)** + Docker Compose

The Python GIS dependencies (GeoPandas, Shapely, PyProj, Fiona, Pyogrio) ship as
prebuilt wheels, so no system GDAL installation is normally required.

> **Windows one-click:** double-click **`start.bat`** in the project root. It
> creates the backend virtual environment, installs dependencies for both
> backend and frontend, starts both servers, and opens the browser
> automatically.

---

## Option A — Docker (recommended)

```bash
git clone https://github.com/SalohiyatDP/GPS_kordinatalar.git
cd GPS_kordinatalar
docker compose up --build
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:8080        |
| API      | http://localhost:8000        |
| Swagger  | http://localhost:8000/docs   |

The SQLite database is persisted in the `cadastre-data` Docker volume.

---

## Option B — Manual

### 1. Backend

**Linux / macOS:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Windows (PowerShell)** — run each command on its own line (`&&` is not supported):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> If PowerShell blocks the activation script ("running scripts is disabled"),
> run this once for the current session, then activate again:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

Configuration is via environment variables (prefix `APP_`) or a `.env` file:

```env
APP_DATABASE_URL=sqlite:///./cadastre.db
APP_MAX_UPLOAD_MB=200
APP_CORS_ORIGINS=["http://localhost:5173"]
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev          # development (http://localhost:5173)
npm run build        # production bundle in dist/
npm run preview      # preview the production build
```

During development Vite proxies `/api` → `http://localhost:8000`.

---

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Troubleshooting

- **Shapefile upload fails** — ensure the `.zip` contains `.shp`, `.dbf`, `.shx`
  and ideally `.prj` (for CRS detection).
- **Coordinates not detected** — check the input contains valid lat (0–90) and
  lon (0–180); invalid rows are reported separately in the response.
- **Map tiles blank** — the app uses public OSM/Esri tiles and requires internet
  access from the browser.
