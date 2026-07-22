"""Optional geocoding via OpenStreetMap Nominatim (free tier, no API key)."""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

_USER_AGENT = "HireHub/1.0 (local job finder; cohort project)"


def geocode_location(location: str) -> tuple[float, float] | None:
    """Return (latitude, longitude) for a location string, or None if lookup fails."""
    query = (location or "").strip()
    if not query:
        return None

    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            rows = json.loads(response.read().decode())
        if not rows:
            return None
        return float(rows[0]["lat"]), float(rows[0]["lon"])
    except (urllib.error.URLError, ValueError, KeyError, IndexError) as exc:
        logger.debug("Geocoding failed for %r: %s", query, exc)
        return None
