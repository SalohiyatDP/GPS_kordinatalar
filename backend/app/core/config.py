"""Application configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env",
                                      extra="ignore")

    app_name: str = "Smart Coordinate & Cadastre Analyzer"
    version: str = "1.0.0"

    # SQLite database (file-based by default).
    database_url: str = "sqlite:///./cadastre.db"

    # CORS — allow the Vite dev server and same-origin by default.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Upload limits.
    max_upload_mb: int = 200


settings = Settings()
