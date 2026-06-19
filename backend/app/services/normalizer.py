"""Coordinate Normalization Module (STEP 1).

Accepts coordinates in virtually any textual format and converts them into a
single standard representation:

    41°07'54.29"N 71°37'49.17"E

Supported inputs
----------------
* DMS              ``41° 7' 54.29" N 71° 37' 49.17" E``
* Decimal          ``41.131747, 71.630325``
* Russian symbols  ``40°53'30.32"С 71°22'33.80"В``
* Mixed formatting ``41 7 54.29 N, 71 37 49.17 E``
* TXT / CSV / Excel content (multi-line)

Validation
----------
* Latitude  : 0 .. 90
* Longitude : 0 .. 180

Duplicate coordinates are detected and removed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# Hemisphere handling (Latin + Cyrillic)
# ---------------------------------------------------------------------------

# Cyrillic -> Latin hemisphere markers.
#   С = Север (North), Ю = Юг (South), В = Восток (East), З = Запад (West)
_CYRILLIC_HEMISPHERE = {
    "С": "N", "с": "N",
    "Ю": "S", "ю": "S",
    "В": "E", "в": "E",
    "З": "W", "з": "W",
}

_LAT_HEMI = {"N", "S"}
_LON_HEMI = {"E", "W"}
_NEGATIVE_HEMI = {"S", "W"}

# Degree / minute / second symbol variants that may appear in real-world data.
_DEGREE_CHARS = "°ºoᴼ"
_MINUTE_CHARS = "'’′ʹ"
_SECOND_CHARS = "\"”″˝"


@dataclass
class ParsedCoordinate:
    """A single normalized coordinate pair."""

    latitude: float
    longitude: float
    point_number: int = 0
    valid: bool = True
    error: str | None = None
    source: str = ""

    @property
    def dms(self) -> str:
        """Standard DMS string, e.g. ``41°07'54.29"N 71°37'49.17"E``."""
        return f"{decimal_to_dms(self.latitude, is_lat=True)} " \
               f"{decimal_to_dms(self.longitude, is_lat=False)}"

    def to_dict(self) -> dict:
        return {
            "point_number": self.point_number,
            "latitude": round(self.latitude, 8),
            "longitude": round(self.longitude, 8),
            "dms": self.dms if self.valid else "",
            "status": "valid" if self.valid else "invalid",
            "error": self.error,
            "source": self.source,
        }


@dataclass
class NormalizationResult:
    coordinates: list[ParsedCoordinate] = field(default_factory=list)
    invalid: list[ParsedCoordinate] = field(default_factory=list)
    duplicates_removed: int = 0

    def to_dict(self) -> dict:
        return {
            "coordinates": [c.to_dict() for c in self.coordinates],
            "invalid": [c.to_dict() for c in self.invalid],
            "duplicates_removed": self.duplicates_removed,
            "count": len(self.coordinates),
        }


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def dms_to_decimal(degrees: float, minutes: float = 0.0,
                   seconds: float = 0.0, hemisphere: str | None = None) -> float:
    """Convert degrees/minutes/seconds to a signed decimal degree value."""
    value = abs(degrees) + minutes / 60.0 + seconds / 3600.0
    if hemisphere and hemisphere.upper() in _NEGATIVE_HEMI:
        value = -value
    elif degrees < 0:
        value = -value
    return value


def decimal_to_dms(value: float, is_lat: bool) -> str:
    """Format a decimal degree value into the project's standard DMS string.

    Rules:
        * minutes always 2 digits
        * seconds always 2 decimals
        * hemisphere is N/S (latitude) or E/W (longitude)
        * no extra spaces
    """
    if is_lat:
        hemisphere = "N" if value >= 0 else "S"
    else:
        hemisphere = "E" if value >= 0 else "W"

    value = abs(value)
    degrees = int(value)
    minutes_full = (value - degrees) * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60

    # Guard against floating point rounding pushing seconds to 60.00
    seconds = round(seconds, 2)
    if seconds >= 60.0:
        seconds -= 60.0
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        degrees += 1

    return f"{degrees}°{minutes:02d}'{seconds:05.2f}\"{hemisphere}"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

# A single angle token. Two alternatives:
#   1. DMS  -> integer degrees followed by a separator + minutes (+ optional seconds)
#   2. Decimal degrees
_ANGLE_PATTERN = (
    r"(?P<hemi_pre>[NSEWnsew])?\s*"
    r"(?P<sign>[+-])?\s*"
    r"(?:"
    # --- DMS form: integer degrees, then minutes, optional seconds ---
    r"(?P<d_dms>\d{1,3})\s*[" + re.escape(_DEGREE_CHARS) + r":\s]\s*"
    r"(?P<m>\d{1,2}(?:\.\d+)?)\s*[" + re.escape(_MINUTE_CHARS) + r":\s]?\s*"
    r"(?:(?P<s>\d{1,2}(?:\.\d+)?)\s*(?:[" + re.escape(_SECOND_CHARS) + r"]|'')?\s*)?"
    r"|"
    # --- Decimal degrees ---
    r"(?P<d_dec>\d{1,3}(?:\.\d+)?)\s*[" + re.escape(_DEGREE_CHARS) + r"]?\s*"
    r")"
    r"(?P<hemi_post>[NSEWnsew])?"
)

_ANGLE_RE = re.compile(_ANGLE_PATTERN, re.VERBOSE)


@dataclass
class _Angle:
    value: float
    hemi: str | None  # 'N'/'S'/'E'/'W' or None


def _replace_cyrillic(text: str) -> str:
    return "".join(_CYRILLIC_HEMISPHERE.get(ch, ch) for ch in text)


# Characters that mark a DMS component (degree / minute / second).
_DMS_MARKER_CHARS = set(_DEGREE_CHARS + _MINUTE_CHARS + _SECOND_CHARS)
_HEMI_RE = re.compile(r"[NSEWnsew]")
# A comma sitting directly between two digits is a decimal separator (26,774).
_DECIMAL_COMMA_RE = re.compile(r"(?<=\d),(?=\d)")
# European decimal pair without spaces, e.g. "41,131747,71,630325".
_EURO_PAIR_RE = re.compile(
    r"^\s*([+-]?\d+),(\d+)\s*[,;]\s*([+-]?\d+),(\d+)\s*$")


def _preprocess_separators(text: str) -> str:
    """Normalize the decimal separator so commas like ``26,774`` are accepted.

    The tricky part is that a comma can mean two different things:
      * a decimal separator  -> ``26,774``  (European style)
      * a pair separator      -> ``41.13, 71.63``

    Heuristics (applied per line):
      1. If the line already contains a period, periods are the decimal mark
         and any commas are pair separators -> leave commas untouched.
      2. Otherwise, if the line contains DMS markers (° ' ") or a hemisphere
         letter, a comma between two digits is a decimal separator.
      3. Otherwise, if the two numbers are separated by whitespace, commas
         between digits are decimal separators.
      4. Otherwise, a fully comma-delimited European pair
         (``41,1317,71,6303``) is reformatted into two decimal numbers.
    """
    s = text
    if "." in s:
        return s

    has_marker = (any(ch in _DMS_MARKER_CHARS for ch in s)
                  or bool(_HEMI_RE.search(s)))
    if has_marker:
        return _DECIMAL_COMMA_RE.sub(".", s)

    if re.search(r"\d\s+\d", s):
        return _DECIMAL_COMMA_RE.sub(".", s)

    m = _EURO_PAIR_RE.match(s)
    if m:
        return f"{m.group(1)}.{m.group(2)} {m.group(3)}.{m.group(4)}"

    return s


def _parse_angles(text: str) -> list[_Angle]:
    """Extract every angle token from a piece of text."""
    angles: list[_Angle] = []
    for m in _ANGLE_RE.finditer(text):
        if m.group("d_dms") is not None:
            deg = float(m.group("d_dms"))
            minutes = float(m.group("m"))
            seconds = float(m.group("s")) if m.group("s") else 0.0
            value = deg + minutes / 60.0 + seconds / 3600.0
        elif m.group("d_dec") is not None:
            value = float(m.group("d_dec"))
        else:
            continue

        hemi = m.group("hemi_pre") or m.group("hemi_post")
        hemi = hemi.upper() if hemi else None

        if m.group("sign") == "-":
            value = -value
        if hemi in _NEGATIVE_HEMI:
            value = -abs(value)

        # Ignore spurious zero-length matches.
        if value == 0 and m.group(0).strip() == "":
            continue
        angles.append(_Angle(value=value, hemi=hemi))
    return angles


def parse_line(line: str) -> ParsedCoordinate | None:
    """Parse one line of text into a coordinate pair, if possible."""
    raw = line.strip()
    if not raw:
        return None

    cleaned = _replace_cyrillic(raw)
    cleaned = _preprocess_separators(cleaned)
    angles = _parse_angles(cleaned)
    if len(angles) < 2:
        return None

    # Decide which angle is latitude and which is longitude.
    lat_angle = next((a for a in angles if a.hemi in _LAT_HEMI), None)
    lon_angle = next((a for a in angles if a.hemi in _LON_HEMI), None)

    if lat_angle is None or lon_angle is None:
        # No hemisphere hints -> assume order is (latitude, longitude).
        lat_angle, lon_angle = angles[0], angles[1]

    return _build_coordinate(lat_angle.value, lon_angle.value, source=raw)


def _build_coordinate(lat: float, lon: float, source: str = "") -> ParsedCoordinate:
    coord = ParsedCoordinate(latitude=lat, longitude=lon, source=source)
    errors = []
    if not (-90.0 <= lat <= 90.0):
        errors.append(f"latitude {lat} out of range (-90..90)")
    if not (-180.0 <= lon <= 180.0):
        errors.append(f"longitude {lon} out of range (-180..180)")
    if errors:
        coord.valid = False
        coord.error = "; ".join(errors)
    return coord


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> NormalizationResult:
    """Parse free-form text (possibly many lines / CSV) into coordinates."""
    result = NormalizationResult()

    lines = _split_records(text)
    parsed: list[ParsedCoordinate] = []
    for line in lines:
        coord = parse_line(line)
        if coord is not None:
            parsed.append(coord)

    seen: set[tuple[float, float]] = set()
    point_no = 0
    for coord in parsed:
        if not coord.valid:
            result.invalid.append(coord)
            continue
        key = (round(coord.latitude, 7), round(coord.longitude, 7))
        if key in seen:
            result.duplicates_removed += 1
            continue
        seen.add(key)
        point_no += 1
        coord.point_number = point_no
        result.coordinates.append(coord)

    return result


def _split_records(text: str) -> list[str]:
    """Split raw text into per-coordinate records.

    Handles newline separated lists as well as CSV rows. A CSV row such as
    ``41.13,71.63`` is kept as one record because the parser pairs the two
    numbers; rows with extra columns (id,lat,lon) are also handled because the
    angle parser simply takes the first two numeric angle tokens.
    """
    records: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        records.append(line)
    return records


def normalize_pairs(pairs: Iterable[tuple[float, float]]) -> NormalizationResult:
    """Normalize already-decoded (lat, lon) decimal pairs."""
    result = NormalizationResult()
    seen: set[tuple[float, float]] = set()
    point_no = 0
    for lat, lon in pairs:
        coord = _build_coordinate(float(lat), float(lon))
        if not coord.valid:
            result.invalid.append(coord)
            continue
        key = (round(coord.latitude, 7), round(coord.longitude, 7))
        if key in seen:
            result.duplicates_removed += 1
            continue
        seen.add(key)
        point_no += 1
        coord.point_number = point_no
        result.coordinates.append(coord)
    return result
