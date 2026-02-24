"""
Astro Service - Unified astrology calculation interface.

Provides a stable, unified API over chart_builder.py and transit_builder.py.
All existing implementations are preserved in their original modules; this
module re-exports them under a clean, minimal API.

Public API:
    generate_natal_chart(birth_data: dict) -> dict
    calculate_transit(natal_chart_json: dict, transit_date: datetime) -> dict
    format_transit_text(transits: dict) -> str
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from src.services.chart_builder import build_natal_chart_text_and_json
from src.services.transit_builder import build_transits, format_transits_for_llm

logger = logging.getLogger(__name__)


def generate_natal_chart(birth_data: dict) -> dict:
    """
    Generate a natal chart from birth data.

    Args:
        birth_data: dict with keys dob (YYYY-MM-DD), time (HH:MM), lat, lng,
                    and optional location / country.

    Returns:
        Chart dict in the standardised "old format" compatible with LLM prompts.
    """
    dob = birth_data["dob"]
    time = birth_data["time"]
    lat = birth_data["lat"]
    lng = birth_data["lng"]

    year, month, day = map(int, dob.split("-"))
    hour, minute = map(int, time.split(":"))

    result = build_natal_chart_text_and_json(
        name="User",
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lng=lng,
        city=birth_data.get("location", "Unknown"),
        nation=birth_data.get("country", "Unknown"),
    )

    chart_json = result["chart_json"]

    # Convert to the "old format" expected by LLM prompts
    planets_old = {}
    for planet in chart_json["planets"]:
        planets_old[planet["name"]] = {
            "sign": planet["sign"],
            "deg": planet["position"],
            "house": planet["house"],
            "retrograde": planet["retrograde"],
        }

    planets_old["Ascendant"] = {
        "sign": chart_json["angles"]["asc"]["sign"],
        "deg": chart_json["angles"]["asc"]["position"],
        "house": 1,
        "retrograde": False,
    }

    houses_old = {}
    for house in chart_json["houses"]:
        houses_old[str(house["number"])] = {
            "sign": house["sign"],
            "deg": house["position"],
        }

    aspects_old = [
        {
            "from": asp["planet1"],
            "to": asp["planet2"],
            "type": asp["aspect"],
            "orb": asp["orb"],
            "applying": asp["applying"],
        }
        for asp in chart_json["aspects"]
    ]

    original_input = (
        f"DOB: {dob}, Time: {time}, Lat: {lat}, Lng: {lng}"
    )

    from datetime import timezone
    chart = {
        "planets": planets_old,
        "houses": houses_old,
        "aspects": aspects_old,
        "source": "generated",
        "original_input": original_input,
        "engine_version": chart_json["meta"]["engine"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "_kerykeion_data": chart_json,
        "_text_export": result["text_export"],
    }

    logger.info("Natal chart generated via astro_service")
    return chart


async def generate_natal_chart_async(birth_data: dict) -> dict:
    """Async wrapper for generate_natal_chart."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_natal_chart, birth_data)


def calculate_transit(
    natal_chart_json: dict, transit_date: datetime
) -> Dict[str, Any]:
    """
    Calculate planetary transits for a given date.

    Args:
        natal_chart_json: User's natal chart (old format).
        transit_date:     Target date/time (UTC-aware datetime).

    Returns:
        Transit dict with planet positions and aspects to natal chart.
    """
    return build_transits(natal_chart_json, transit_date)


def format_transit_text(transits: Dict[str, Any]) -> str:
    """
    Format transit data as readable text for LLM prompts.

    Args:
        transits: Output from calculate_transit().

    Returns:
        Formatted string.
    """
    return format_transits_for_llm(transits)
