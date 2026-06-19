"""Smart Coordinate & Cadastre Analyzer — FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import cadastre, coordinates, geometry, projects, reports
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
    description=(
        "Professional cadastral GIS analysis system: coordinate normalization, "
        "polygon geometry, GIS exports (XLSX/KML/KMZ/PDF/GeoJSON), and cadastre "
        "contour intersection analysis."
    ),
)

# Ensure tables exist even when the app object is used without the ASGI
# lifespan (e.g. some test clients / scripts).
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.version}


app.include_router(coordinates.router)
app.include_router(geometry.router)
app.include_router(cadastre.router)
app.include_router(reports.router)
app.include_router(projects.router)
