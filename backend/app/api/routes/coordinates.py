"""Coordinate normalization endpoints (STEP 1)."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, File, UploadFile

from app.schemas.models import NormalizeRequest, NormalizeResponse
from app.services import normalizer as nz
from app.services import url_resolver

router = APIRouter(prefix="/api/coordinates", tags=["coordinates"])


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize(req: NormalizeRequest):
    """Normalize free-form text, CSV rows, or map URLs into standard coords."""
    text = req.text or ""
    extra_pairs: list[tuple[float, float]] = []

    if req.resolve_urls and url_resolver.is_url(text):
        extra_pairs = await url_resolver.resolve_text(text)

    result = nz.normalize_text(text)

    if extra_pairs:
        # Merge URL-resolved coordinates, re-running duplicate detection.
        merged = [(c.latitude, c.longitude) for c in result.coordinates] + extra_pairs
        result = nz.normalize_pairs(merged)

    return result.to_dict()


@router.post("/upload", response_model=NormalizeResponse)
async def upload_file(file: UploadFile = File(...)):
    """Normalize coordinates from an uploaded TXT / CSV / XLSX file."""
    raw = await file.read()
    name = (file.filename or "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        text = _xlsx_to_text(raw)
    else:
        text = raw.decode("utf-8", errors="replace")
        # Normalize CSV delimiters to a parser-friendly form.
        text = _csv_to_text(text)

    result = nz.normalize_text(text)
    return result.to_dict()


def _csv_to_text(text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t")
    except csv.Error:
        return text
    out_lines = []
    reader = csv.reader(io.StringIO(text), dialect)
    for row in reader:
        out_lines.append(" ".join(cell.strip() for cell in row if cell.strip()))
    return "\n".join(out_lines)


def _xlsx_to_text(raw: bytes) -> str:
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    lines = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            if cells:
                lines.append(" ".join(cells))
    return "\n".join(lines)
