"""
Natal chart generation using Kerykeion library with Swiss Ephemeris backend.

This module provides a standardized interface for generating natal charts
with both text export (AstroSeek-compatible format) and structured JSON data.
"""

import logging
from typing import Dict, Any, Optional
from kerykeion import AstrologicalSubject, NatalAspects
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

# Initialize TimezoneFinder once at module level for better performance
_timezone_finder = TimezoneFinder()

# Zodiac signs for reference
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Sign abbreviation to full name mapping
SIGN_MAP = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"
}


def deg_to_dms(x: float) -> str:
    """
    Convert decimal degrees to degrees and minutes format.
    
    Args:
        x: Decimal degree value
    
    Returns:
        String in format "DD°MM'"
    """
    d = int(x)
    m = int((x - d) * 60)
    return f"{d}°{m:02d}'"


def house_suffix(n: int) -> str:
    """
    Get the ordinal suffix for house numbers (1st, 2nd, 3rd, etc.)
    
    Args:
        n: House number
    
    Returns:
        Ordinal suffix (st, nd, rd, th)
    """
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def parse_house_name(house_str: str) -> int:
    """
    Parse house name like 'First_House' to house number.
    
    Args:
        house_str: House name (e.g., "First_House", "Tenth_House")
    
    Returns:
        House number (1-12)
    """
    house_names = {
        "First_House": 1, "Second_House": 2, "Third_House": 3,
        "Fourth_House": 4, "Fifth_House": 5, "Sixth_House": 6,
        "Seventh_House": 7, "Eighth_House": 8, "Ninth_House": 9,
        "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
    }
    return house_names.get(house_str, 1)


def build_natal_chart_text_and_json(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lng: float,
    city: str = "Unknown",
    nation: str = "Unknown",
    tz_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate natal chart using Kerykeion with both text export and JSON data.
    
    Args:
        name: Name for the chart (can be "User" or actual name)
        year: Birth year
        month: Birth month (1-12)
        day: Birth day
        hour: Birth hour (0-23)
        minute: Birth minute (0-59)
        lat: Birth latitude
        lng: Birth longitude
        city: Birth city name (optional, defaults to "Unknown")
        nation: Birth country/nation name (optional, defaults to "Unknown")
        tz_str: Timezone string (e.g., "America/New_York"). If None, will be determined from coordinates.
    
    Returns:
        Dictionary with:
            - text_export: AstroSeek-compatible text format
            - chart_json: Structured JSON with planets, houses, aspects, angles, metadata
    
    Raises:
        Exception: If chart generation fails
    """
    logger.info(f"Building natal chart using Kerykeion for {city}, {nation} ({lat}, {lng})")
    
    try:
        # Determine timezone if not provided
        if tz_str is None:
            tz_str = _timezone_finder.timezone_at(lat=lat, lng=lng)
            if tz_str is None:
                tz_str = "UTC"  # Fallback to UTC if timezone can't be determined
                logger.warning(f"Could not determine timezone for {lat}, {lng}, using UTC")
            else:
                logger.info(f"Determined timezone: {tz_str}")
        
        # Initialize Kerykeion chart instance with coordinates
        # Setting online=False to avoid geonames API calls
        chart = AstrologicalSubject(
            name=name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lat=lat,
            lng=lng,
            tz_str=tz_str,
            city=city,
            nation=nation,
            online=False
        )
        
        # Build text export in AstroSeek format
        text_lines = []
        
        # Note: We access chart._model to get the AstrologicalSubjectModel
        # This is the documented way to access chart data in Kerykeion
        # See: https://github.com/g-battaglia/kerykeion
        
        # Header section
        text_lines.append(f"City: {chart._model.city}")
        text_lines.append(f"Country: {chart._model.nation}")
        text_lines.append(f"Latitude, Longitude: {chart._model.lat}, {chart._model.lng}")
        text_lines.append("House system: Placidus system")
        text_lines.append("")
        
        # Planets section
        text_lines.append("Planets:")
        planets_data = []
        
        # Define the main planets in order
        planet_names = ['sun', 'moon', 'mercury', 'venus', 'mars',
                        'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
        
        for planet_attr in planet_names:
            planet_obj = getattr(chart._model, planet_attr)
            planet_name = planet_obj.name
            sign_abbr = planet_obj.sign
            sign = SIGN_MAP.get(sign_abbr, sign_abbr)
            position = planet_obj.position
            house_str = planet_obj.house
            house_num = parse_house_name(house_str) if house_str else None
            retrograde = planet_obj.retrograde
            
            # Format position as degrees and minutes
            pos_str = deg_to_dms(position)
            
            # Build planet line
            planet_line = f"{planet_name} in {sign} {pos_str}"
            
            # Add retrograde marker
            if retrograde:
                planet_line += ", Retrograde"
            
            # Add house information if available
            if house_num:
                planet_line += f", in {house_num}{house_suffix(house_num)} House"
            
            text_lines.append(planet_line)
            
            # Store planet data for JSON
            planets_data.append({
                "name": planet_name,
                "sign": sign,
                "position": round(position, 2),
                "house": house_num,
                "retrograde": retrograde
            })
        
        text_lines.append("")
        
        # Angles section (ASC and MC)
        text_lines.append("Angles:")
        
        # Ascendant (1st house cusp)
        asc = chart._model.first_house
        asc_sign = SIGN_MAP.get(asc.sign, asc.sign)
        asc_position = asc.position
        asc_str = deg_to_dms(asc_position)
        text_lines.append(f"ASC in {asc_sign} {asc_str}")
        
        # Midheaven (MC is the 10th house cusp)
        mc = chart._model.tenth_house
        mc_sign = SIGN_MAP.get(mc.sign, mc.sign)
        mc_position = mc.position
        mc_str = deg_to_dms(mc_position)
        text_lines.append(f"MC in {mc_sign} {mc_str}")
        
        text_lines.append("")
        
        # Houses section
        text_lines.append("Houses:")
        houses_data = []
        
        # Get all house cusps
        house_attrs = [
            'first_house', 'second_house', 'third_house',
            'fourth_house', 'fifth_house', 'sixth_house',
            'seventh_house', 'eighth_house', 'ninth_house',
            'tenth_house', 'eleventh_house', 'twelfth_house'
        ]
        
        for idx, house_attr in enumerate(house_attrs, start=1):
            house_obj = getattr(chart._model, house_attr)
            house_sign_abbr = house_obj.sign
            house_sign = SIGN_MAP.get(house_sign_abbr, house_sign_abbr)
            house_position = house_obj.position
            house_str = deg_to_dms(house_position)
            
            text_lines.append(f"{idx}{house_suffix(idx)} House in {house_sign} {house_str}")
            
            houses_data.append({
                "number": idx,
                "sign": house_sign,
                "position": round(house_position, 2)
            })
        
        text_lines.append("")
        
        # Aspects section
        text_lines.append("Aspects:")
        aspects_data = []
        
        # Calculate aspects
        aspects = NatalAspects(chart)
        
        for aspect_obj in aspects.all_aspects:
            planet1 = aspect_obj.p1_name
            planet2 = aspect_obj.p2_name
            aspect_type = aspect_obj.aspect.capitalize()
            orb = aspect_obj.orbit
            is_applying = aspect_obj.aspect_movement == "Applying"
            
            # Format orb
            orb_str = deg_to_dms(abs(orb))
            applying_str = "Applying" if is_applying else "Separating"
            
            aspect_line = f"{planet1} {aspect_type} {planet2} (Orb: {orb_str}, {applying_str})"
            text_lines.append(aspect_line)
            
            aspects_data.append({
                "planet1": planet1,
                "planet2": planet2,
                "aspect": aspect_type,
                "orb": round(abs(orb), 2),
                "applying": is_applying
            })
        
        # Join all lines into text export
        text_export = "\n".join(text_lines)
        
        # Build structured JSON
        chart_json = {
            "planets": planets_data,
            "houses": houses_data,
            "aspects": aspects_data,
            "angles": {
                "asc": {
                    "sign": asc_sign,
                    "position": round(asc_position, 2)
                },
                "mc": {
                    "sign": mc_sign,
                    "position": round(mc_position, 2)
                }
            },
            "meta": {
                "city": chart._model.city,
                "nation": chart._model.nation,
                "lat": chart._model.lat,
                "lng": chart._model.lng,
                "timezone": chart._model.tz_str,
                "engine": "kerykeion_swisseph"
            }
        }
        
        logger.info("Natal chart generated successfully using Kerykeion")
        
        return {
            "text_export": text_export,
            "chart_json": chart_json
        }
        
    except Exception as e:
        logger.exception(f"Failed to generate natal chart with Kerykeion: {e}")
        raise Exception(f"Failed to generate natal chart: {str(e)}")
