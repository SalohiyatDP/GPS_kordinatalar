"""Export module (STEP 2 & STEP 5).

Generates XLSX, KML, KMZ, GeoJSON and PDF outputs. All functions return raw
``bytes`` so they can be streamed directly from the API.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime

import simplekml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from .normalizer import decimal_to_dms

# ---------------------------------------------------------------------------
# Unicode font registration (Cyrillic support for PDF reports)
# ---------------------------------------------------------------------------

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

try:
    _regular = os.path.join(_FONTS_DIR, "DejaVuSans.ttf")
    _bold = os.path.join(_FONTS_DIR, "DejaVuSans-Bold.ttf")
    if os.path.exists(_regular):
        pdfmetrics.registerFont(TTFont("DejaVuSans", _regular))
        FONT_NAME = "DejaVuSans"
    if os.path.exists(_bold):
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _bold))
        FONT_BOLD = "DejaVuSans-Bold"
except Exception:  # pragma: no cover - fall back to built-in fonts
    FONT_NAME = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"


# Square meters -> hectares.
def _to_ha(m2) -> float:
    try:
        return round(float(m2) / 10_000.0, 4)
    except (TypeError, ValueError):
        return 0.0

# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

_HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
_HEADER_FONT = Font(bold=True, color="FFFFFF")


def _style_header(ws, ncols: int):
    for col in range(1, ncols + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _status_uz(status: str) -> str:
    return {"Full": "Toʻliq", "Partial": "Qisman", "Vacant": "Boʻsh"}.get(
        status, status or "")


def points_to_xlsx(points: list[dict]) -> bytes:
    """points.xlsx — Nuqta raqami, Kenglik, Uzunlik, DMS."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Nuqtalar"
    headers = ["Nuqta №", "Kenglik", "Uzunlik", "DMS"]
    ws.append(headers)
    _style_header(ws, len(headers))
    for p in points:
        ws.append([
            p["point_number"],
            p["latitude"],
            p["longitude"],
            p.get("dms", ""),
        ])
    widths = [14, 16, 16, 34]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    return _wb_bytes(wb)


def analysis_to_xlsx(points: list[dict], area: dict, perimeter: dict,
                     contours: list[dict] | None = None,
                     summary: str = "", id_label: str = "Kontur") -> bytes:
    """Analysis.xlsx — toʻliq kadastr hisobot kitobi (bir nechta varaq)."""
    wb = Workbook()

    ws = wb.active
    ws.title = "Koordinatalar"
    headers = ["Nuqta №", "Kenglik", "Uzunlik", "DMS"]
    ws.append(headers)
    _style_header(ws, len(headers))
    for p in points:
        ws.append([p["point_number"], p["latitude"], p["longitude"], p.get("dms", "")])
    for i, w in enumerate([14, 16, 16, 34], start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    ws2 = wb.create_sheet("Xulosa")
    ws2.append(["Koʻrsatkich", "Qiymat"])
    _style_header(ws2, 2)
    ws2.append(["Maydon (m²)", area.get("square_meters")])
    ws2.append(["Maydon (gektar)", area.get("hectares")])
    ws2.append(["Maydon (km²)", area.get("square_kilometers")])
    ws2.append(["Maydon (sotix)", area.get("sotix")])
    ws2.append(["Perimetr (m)", perimeter.get("meters")])
    ws2.append(["Perimetr (km)", perimeter.get("kilometers")])
    ws2.append(["Yaratilgan", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")])
    if summary:
        ws2.append(["Xulosa", summary])
    ws2.column_dimensions["A"].width = 22
    ws2.column_dimensions["B"].width = 50

    if contours:
        ws3 = wb.create_sheet("Tahlil")
        c_headers = [id_label, "Viloyat", "Tuman", "Massiv", "MFY",
                     "Maydon (ga)", "Kesishuv (ga)", "Qamrov %", "Holat"]
        ws3.append(c_headers)
        _style_header(ws3, len(c_headers))
        for c in contours:
            ws3.append([
                c.get("code") or c.get("contour"),
                c.get("region"),
                c.get("district"),
                c.get("massif"),
                c.get("mfy"),
                _to_ha(c.get("contour_area")),
                _to_ha(c.get("intersection_area")),
                c.get("coverage_percent"),
                _status_uz(c.get("status")),
            ])
        for i, w in enumerate([16, 16, 16, 16, 16, 14, 14, 12, 10], start=1):
            ws3.column_dimensions[ws3.cell(row=1, column=i).column_letter].width = w

    return _wb_bytes(wb)


def _wb_bytes(wb: Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# KML / KMZ
# ---------------------------------------------------------------------------

def _kml_to_kmz_bytes(kml: simplekml.Kml) -> bytes:
    """Package a simplekml document into in-memory KMZ (zip) bytes."""
    kml_str = kml.kml()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_str)
    return buf.getvalue()

def points_to_kmz(points: list[dict]) -> bytes:
    """KMZ with one placemark per point."""
    kml = simplekml.Kml()
    for p in points:
        pnt = kml.newpoint(name=str(p["point_number"]))
        pnt.coords = [(p["longitude"], p["latitude"])]
        pnt.description = (
            f"Point {p['point_number']}\n"
            f"{p.get('dms', '')}\n"
            f"{p['latitude']}, {p['longitude']}"
        )
    return _kml_to_kmz_bytes(kml)


def polygon_to_kmz(points: list[dict], name: str = "Polygon") -> bytes:
    """polygon.kmz — closed polygon compatible with Google Earth."""
    kml = simplekml.Kml()
    ring = [(p["longitude"], p["latitude"]) for p in points]
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    pol = kml.newpolygon(name=name, outerboundaryis=ring)
    pol.style.linestyle.color = simplekml.Color.red
    pol.style.linestyle.width = 3
    pol.style.polystyle.color = simplekml.Color.changealphaint(80, simplekml.Color.red)
    # Add points too for reference.
    for p in points:
        pnt = kml.newpoint(name=str(p["point_number"]))
        pnt.coords = [(p["longitude"], p["latitude"])]
    return _kml_to_kmz_bytes(kml)


def analysis_to_kmz(points: list[dict], contours: list[dict] | None = None) -> bytes:
    """Analysis.kmz — polygon + points + contour intersections colored."""
    kml = simplekml.Kml()
    # User polygon (red).
    ring = [(p["longitude"], p["latitude"]) for p in points]
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    if len(ring) >= 4:
        pol = kml.newpolygon(name="User Polygon", outerboundaryis=ring)
        pol.style.linestyle.color = simplekml.Color.red
        pol.style.linestyle.width = 3
        pol.style.polystyle.color = simplekml.Color.changealphaint(60, simplekml.Color.red)

    pts_folder = kml.newfolder(name="Points")
    for p in points:
        pnt = pts_folder.newpoint(name=str(p["point_number"]))
        pnt.coords = [(p["longitude"], p["latitude"])]

    if contours:
        c_folder = kml.newfolder(name="Contours")
        for c in contours:
            geojson = c.get("geometry")
            if not geojson:
                continue
            full = c.get("status") == "Full"
            vacant = c.get("status") == "Vacant"
            if full:
                color = simplekml.Color.green
            elif vacant:
                color = simplekml.Color.orange
            else:
                color = simplekml.Color.yellow
            label = str(c.get("code") or c.get("contour") or "")
            ha = (c.get("intersection_area") or 0) / 10_000.0
            cov = c.get("coverage_percent") or 0
            holat = "To'liq" if full else ("Bo'sh" if vacant else "Qisman")
            desc = (
                f"Kontur: {label}\n"
                f"Viloyat: {c.get('region') or '-'}\n"
                f"Tuman: {c.get('district') or '-'}\n"
                f"Massiv: {c.get('massif') or '-'}\n"
                f"MFY: {c.get('mfy') or '-'}\n"
                f"Kesishuv: {ha:.4f} ga\n"
                f"Qamrov: {cov:.1f}%\n"
                f"Holat: {holat}"
            )
            for j, ring_coords in enumerate(_iter_polygon_rings(geojson)):
                cpol = c_folder.newpolygon(
                    name=label if j == 0 else f"{label} ({j + 1})",
                    outerboundaryis=ring_coords,
                    description=desc,
                )
                cpol.style.polystyle.color = simplekml.Color.changealphaint(120, color)
                cpol.style.linestyle.color = color
                cpol.style.linestyle.width = 2
    return _kml_to_kmz_bytes(kml)


def _iter_polygon_rings(geojson: dict):
    gtype = geojson.get("type")
    coords = geojson.get("coordinates", [])
    if gtype == "Polygon":
        if coords:
            yield [(x, y) for x, y in coords[0]]
    elif gtype == "MultiPolygon":
        for poly in coords:
            if poly:
                yield [(x, y) for x, y in poly[0]]


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

def to_geojson(points: list[dict], polygon_geojson: dict | None = None,
               contours: list[dict] | None = None) -> bytes:
    features = []
    for p in points:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p["longitude"], p["latitude"]]},
            "properties": {"point_number": p["point_number"], "dms": p.get("dms", "")},
        })
    if polygon_geojson:
        features.append({
            "type": "Feature",
            "geometry": polygon_geojson,
            "properties": {"name": "User Polygon"},
        })
    if contours:
        for c in contours:
            if c.get("geometry"):
                features.append({
                    "type": "Feature",
                    "geometry": c["geometry"],
                    "properties": {k: v for k, v in c.items() if k != "geometry"},
                })
    fc = {"type": "FeatureCollection", "features": features}
    return json.dumps(fc, ensure_ascii=False, indent=2).encode("utf-8")


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def to_pdf(points: list[dict], area: dict, perimeter: dict,
           contours: list[dict] | None = None,
           summary: str = "", title: str = "Kadastr tahlil hisoboti",
           map_image_png: bytes | None = None, id_label: str = "Kontur") -> bytes:
    """Analysis.pdf — koordinatalar jadvali, maydon, perimetr, xarita va tahlil."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm,
                            bottomMargin=1.5 * cm, leftMargin=1.5 * cm,
                            rightMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    # Apply the Unicode (Cyrillic-capable) font to all used styles.
    for _name in ("Title", "Normal", "Heading2"):
        styles[_name].fontName = FONT_BOLD if _name in ("Title", "Heading2") else FONT_NAME
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Paragraph(
        f"Yaratilgan: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"]))
    elements.append(Spacer(1, 0.4 * cm))

    if map_image_png:
        try:
            img = Image(io.BytesIO(map_image_png))
            img._restrictSize(17 * cm, 9 * cm)
            elements.append(img)
            elements.append(Spacer(1, 0.4 * cm))
        except Exception:
            pass

    # Coordinate table.
    elements.append(Paragraph("Koordinatalar", styles["Heading2"]))
    data = [["#", "Kenglik", "Uzunlik", "DMS"]]
    for p in points:
        data.append([
            str(p["point_number"]),
            f"{p['latitude']:.6f}",
            f"{p['longitude']:.6f}",
            p.get("dms", ""),
        ])
    table = Table(data, hAlign="LEFT", colWidths=[1.2 * cm, 3.2 * cm, 3.2 * cm, 7 * cm])
    table.setStyle(_table_style())
    elements.append(table)
    elements.append(Spacer(1, 0.4 * cm))

    # Area & perimeter.
    elements.append(Paragraph("Geometriya", styles["Heading2"]))
    geo = [
        ["Maydon (m²)", f"{area.get('square_meters', 0):,.2f}"],
        ["Maydon (gektar)", f"{area.get('hectares', 0):,.4f}"],
        ["Maydon (km²)", f"{area.get('square_kilometers', 0):,.6f}"],
        ["Maydon (sotix)", f"{area.get('sotix', 0):,.2f}"],
        ["Perimetr (m)", f"{perimeter.get('meters', 0):,.2f}"],
        ["Perimetr (km)", f"{perimeter.get('kilometers', 0):,.4f}"],
    ]
    gtable = Table(geo, hAlign="LEFT", colWidths=[6 * cm, 8 * cm])
    gtable.setStyle(_table_style())
    elements.append(gtable)
    elements.append(Spacer(1, 0.4 * cm))

    if contours:
        elements.append(Paragraph("Tahlil natijalari", styles["Heading2"]))
        cdata = [[id_label, "Viloyat", "Tuman", "Massiv", "MFY",
                  "Maydon (ga)", "Kesishuv (ga)", "Qamrov %", "Holat"]]
        for c in contours:
            cdata.append([
                str(c.get("code") or c.get("contour", "")),
                str(c.get("region", "")),
                str(c.get("district", "")),
                str(c.get("massif", "")),
                str(c.get("mfy", "")),
                f"{_to_ha(c.get('contour_area')):,.4f}",
                f"{_to_ha(c.get('intersection_area')):,.4f}",
                f"{c.get('coverage_percent', 0):.1f}",
                _status_uz(c.get("status", "")),
            ])
        ctable = Table(cdata, hAlign="LEFT")
        ctable.setStyle(_table_style())
        elements.append(ctable)
        elements.append(Spacer(1, 0.4 * cm))

    if summary:
        elements.append(Paragraph("Xulosa", styles["Heading2"]))
        elements.append(Paragraph(summary, styles["Normal"]))

    doc.build(elements)
    return buf.getvalue()


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3F8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
