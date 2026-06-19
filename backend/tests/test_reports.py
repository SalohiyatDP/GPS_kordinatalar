"""Tests for report exports: contour codes (q), hectares, Cyrillic font, KMZ."""

import io
import zipfile

from openpyxl import load_workbook

from app.services import exporters as ex

POINTS = [
    {"point_number": 1, "latitude": 41.0, "longitude": 71.0, "dms": ""},
    {"point_number": 2, "latitude": 41.0, "longitude": 71.01, "dms": ""},
    {"point_number": 3, "latitude": 41.01, "longitude": 71.01, "dms": ""},
]
AREA = {"square_meters": 1000, "hectares": 0.1, "square_kilometers": 1e-6, "sotix": 10}
PERI = {"meters": 400, "kilometers": 0.4}
CONTOURS = [
    {
        "contour": "20", "code": "20q", "region": "Наманган",
        "district": "Косонсой", "massif": "Ободон 2 уч", "mfy": "Хонқўрғон",
        "contour_area": 267301.89, "intersection_area": 54199.36,
        "coverage_percent": 20.28, "status": "Partial",
        "geometry": {"type": "Polygon", "coordinates":
                     [[[71, 41], [71.005, 41], [71.005, 41.005], [71, 41.005], [71, 41]]]},
    },
]


def test_cyrillic_font_bundled_and_registered():
    assert ex.FONT_NAME == "DejaVuSans"
    assert ex.FONT_BOLD == "DejaVuSans-Bold"


def test_xlsx_uses_code_and_hectares():
    data = ex.analysis_to_xlsx(POINTS, AREA, PERI, CONTOURS, "20q")
    wb = load_workbook(io.BytesIO(data))
    ws = wb["Contours"]
    headers = [c.value for c in ws[1]]
    assert "Contour Area (ha)" in headers
    assert "Intersection Area (ha)" in headers
    row = [c.value for c in ws[2]]
    assert row[0] == "20q"                       # code with q
    # 267301.89 m² -> 26.7302 ha
    ha_idx = headers.index("Contour Area (ha)")
    assert abs(row[ha_idx] - 26.7302) < 0.01


def test_pdf_generated():
    data = ex.to_pdf(POINTS, AREA, PERI, CONTOURS, "20q", title="Кадастр")
    assert data[:4] == b"%PDF"


def test_kmz_separate_contours_with_code():
    data = ex.analysis_to_kmz(POINTS, CONTOURS)
    assert data[:2] == b"PK"
    doc = zipfile.ZipFile(io.BytesIO(data)).read("doc.kml").decode("utf-8")
    assert "20q" in doc
    assert "Qisman" in doc          # status in description
    assert "<Folder" in doc         # contours grouped in a folder
