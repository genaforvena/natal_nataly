"""
Birth data collection module.

Implements LLM-free parsing for step-by-step birth data collection:
- parse_date(text)  → YYYY-MM-DD string or None
- parse_time(text)  → HH:MM string or None
- geocode_place(text) → {"lat", "lng", "location"} dict or None (async, uses Nominatim)
"""

import os
import re
import logging
from datetime import date as _date
import httpx

logger = logging.getLogger(__name__)

# Nominatim requires a descriptive User-Agent with a contact address.
# Operators should set NOMINATIM_USER_AGENT in their environment, e.g.:
#   NOMINATIM_USER_AGENT="NatalNatalyBot/1.0 (+https://example.com; admin@example.com)"
_NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "NatalNatalyBot/1.0 (+https://github.com/genaforvena/natal_nataly)"
)

# Month name mapping (English + Russian abbreviated)
_MONTH_NAMES = {
    # English
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    # Russian
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
    "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def parse_date(text: str) -> str | None:
    """
    Parse a date from plain text without LLM involvement.

    Handles:
    - YYYY-MM-DD  (ISO)
    - DD.MM.YYYY  (European dot-separated)
    - DD/MM/YYYY  (European slash-separated)
    - DD MM YYYY  (space-separated with numeric month)
    - D Month YYYY / Month D, YYYY  (text month, English or Russian)

    Returns:
        "YYYY-MM-DD" string or None if no recognisable date found.
    """
    text = text.strip()

    # 1. ISO: YYYY-MM-DD
    m = re.search(r'\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b', text)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"

    # 2. DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY (day first)
    m = re.search(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b', text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"

    # 3. DD MM YYYY (all numbers, space-separated)
    m = re.search(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b', text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"

    # 4. Text month: "15 May 1990", "May 15, 1990", "15 мая 1990", "15 мая 1990 года"
    m = re.search(
        r'\b(\d{1,2})\s+([а-яёА-ЯЁa-zA-Z]+)\s+(\d{4})\b',
        text, re.IGNORECASE
    )
    if m:
        day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        month = _MONTH_NAMES.get(month_str)
        if month and _valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"

    m = re.search(
        r'\b([а-яёА-ЯЁa-zA-Z]+)\s+(\d{1,2})[,\s]+(\d{4})\b',
        text, re.IGNORECASE
    )
    if m:
        month_str, day, year = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        month = _MONTH_NAMES.get(month_str)
        if month and _valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"

    logger.debug(f"parse_date: no recognisable date in: {text!r}")
    return None


def parse_time(text: str) -> str | None:
    """
    Parse a birth time from plain text without LLM involvement.

    Handles:
    - HH:MM (24-hour or 12-hour)
    - H:MM
    - HH MM (space-separated)
    - 12-hour with AM/PM suffix

    Returns:
        "HH:MM" string (24-hour) or None.
    """
    text = text.strip()

    # HH:MM[:SS] optionally followed by AM/PM
    m = re.search(
        r'\b(\d{1,2}):(\d{2})(?::\d{2})?\s*(am|pm)?\b',
        text, re.IGNORECASE
    )
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        ampm = (m.group(3) or "").lower()
        hour = _apply_ampm(hour, ampm)
        if _valid_time(hour, minute):
            return f"{hour:02d}:{minute:02d}"

    # HH MM with optional am/pm, but only when NOT followed by more digits
    # (avoids matching "15 05 1990" as 15:05 instead of a date)
    m = re.search(
        r'\b(\d{1,2})\s+(\d{2})\s*(am|pm)?\b(?!\s*\d)',
        text, re.IGNORECASE
    )
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        ampm = (m.group(3) or "").lower()
        hour = _apply_ampm(hour, ampm)
        if _valid_time(hour, minute):
            return f"{hour:02d}:{minute:02d}"

    logger.debug(f"parse_time: no recognisable time in: {text!r}")
    return None


async def geocode_place(text: str) -> dict | None:
    """
    Geocode a place name to lat/lng using the Nominatim (OpenStreetMap) API.

    Args:
        text: Place name string, e.g. "Moscow", "New York, USA", "Нижний Новгород"

    Returns:
        {"lat": float, "lng": float, "location": str} or None if not found.
    """
    text = text.strip()
    if not text:
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": text,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    headers = {
        # Nominatim usage policy requires a descriptive User-Agent with contact info.
        # Configure via NOMINATIM_USER_AGENT environment variable.
        "User-Agent": _NOMINATIM_USER_AGENT
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()

        if not results:
            logger.info(f"geocode_place: no results for {text!r}")
            return None

        result = results[0]
        lat = float(result["lat"])
        lng = float(result["lon"])
        display_name = result.get("display_name", text)
        # Use first two components of the display name (e.g., "Moscow, Russia") to
        # preserve enough context for disambiguation while keeping the label readable.
        parts = [p.strip() for p in display_name.split(",") if p.strip()]
        location_short = ", ".join(parts[:2]) if len(parts) >= 2 else parts[0] if parts else text

        logger.info(f"geocode_place: {text!r} → lat={lat}, lng={lng}, name={location_short!r}")
        return {"lat": lat, "lng": lng, "location": location_short}

    except Exception as e:
        logger.exception(f"geocode_place error for {text!r}: {e}")
        return None


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _valid_date(year: int, month: int, day: int) -> bool:
    """Return True only if (year, month, day) form a real calendar date."""
    if year < 1800:
        return False
    try:
        _date(year, month, day)
        return True
    except ValueError:
        return False


def _valid_time(hour: int, minute: int) -> bool:
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _apply_ampm(hour: int, ampm: str) -> int:
    """
    Convert a 12-hour clock hour to 24-hour.
    In 12-hour notation valid hours are 1–12.
    Returns -1 to signal invalid input when ampm is given but hour is out of range.
    """
    if ampm:
        if not (1 <= hour <= 12):
            return -1  # Signal invalid 12-hour input
        if ampm == "pm" and hour != 12:
            return hour + 12
        if ampm == "am" and hour == 12:
            return 0
    return hour
