"""URL Resolver (STEP 1).

Extract coordinates from Google Maps / Yandex Maps / 2GIS links, including
shortened links that need redirect resolution.
"""

from __future__ import annotations

import re

import httpx

# Common coordinate patterns found in map URLs.
_PATTERNS = [
    # Google Maps: .../@41.131747,71.630325,15z
    re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)"),
    # Google: ?q=41.13,71.63  or  ?ll=41.13,71.63 or daddr / saddr / center
    re.compile(r"[?&](?:q|ll|center|destination|daddr|saddr)=(-?\d+\.\d+),\s*(-?\d+\.\d+)"),
    # Google place data: !3d41.131747!4d71.630325
    re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)"),
    # Yandex: ?ll=71.63,41.13  (NOTE: yandex uses lon,lat order — handled below)
    # 2GIS: .../71.630325,41.131747  (lon,lat)
]

# Yandex / 2GIS use longitude,latitude order in some parameters.
_LONLAT_PATTERNS = [
    re.compile(r"[?&]ll=(-?\d+\.\d+),\s*(-?\d+\.\d+)"),      # yandex ll=lon,lat
    re.compile(r"2gis\.[^/]+/.*?/(-?\d+\.\d+),(-?\d+\.\d+)"),  # 2gis lon,lat
]

_URL_RE = re.compile(r"https?://\S+")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def is_url(text: str) -> bool:
    return bool(_URL_RE.search(text.strip()))


def extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(text)


def _match_latlon(url: str) -> tuple[float, float] | None:
    for pat in _PATTERNS:
        m = pat.search(url)
        if m:
            return float(m.group(1)), float(m.group(2))
    is_yandex = "yandex." in url
    is_2gis = "2gis." in url
    if is_yandex or is_2gis:
        for pat in _LONLAT_PATTERNS:
            m = pat.search(url)
            if m:
                lon, lat = float(m.group(1)), float(m.group(2))
                return lat, lon
    return None


async def resolve_url(url: str, *, timeout: float = 10.0) -> tuple[float, float] | None:
    """Resolve a map URL to a (lat, lon) pair.

    Follows redirects (needed for shortened links such as maps.app.goo.gl)
    and inspects both the final URL and the response body.
    """
    url = url.strip()

    # First, try the URL as-is (no network needed for full links).
    direct = _match_latlon(url)
    if direct is not None:
        return direct

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout,
                                     headers=_HEADERS) as client:
            resp = await client.get(url)
            final_url = str(resp.url)
            found = _match_latlon(final_url)
            if found is not None:
                return found
            # Some providers embed coordinates in the page body / meta tags.
            body = resp.text[:200_000]
            found = _match_latlon(body)
            if found is not None:
                return found
    except (httpx.HTTPError, ValueError):
        return None
    return None


async def resolve_text(text: str) -> list[tuple[float, float]]:
    """Resolve every URL found in a block of text."""
    results: list[tuple[float, float]] = []
    for url in extract_urls(text):
        coord = await resolve_url(url)
        if coord is not None:
            results.append(coord)
    return results
