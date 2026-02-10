"""
Transit calculations using Kerykeion library.
Calculates current or future transits relative to natal chart.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from kerykeion import AstrologicalSubject
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

# Initialize TimezoneFinder once at module level
_timezone_finder = TimezoneFinder()

# Planet names (lowercase for Kerykeion attribute access)
PLANET_ATTRS = ['sun', 'moon', 'mercury', 'venus', 'mars', 
                'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

# Aspect types we care about
MAJOR_ASPECTS = {
    "Conjunction": 0,
    "Opposition": 180,
    "Trine": 120,
    "Square": 90,
    "Sextile": 60
}

# Sign names for conversion
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


def sign_to_abs_degree(sign: str, position: float) -> float:
    """Convert sign + position to absolute degree (0-360)"""
    try:
        sign_idx = SIGNS.index(sign)
        return sign_idx * 30 + position
    except ValueError:
        logger.warning(f"Unknown sign: {sign}, defaulting to 0")
        return 0


def build_transits(
    natal_chart_json: dict,
    transit_date: datetime
) -> Dict[str, Any]:
    """
    Calculate transits for a given date relative to natal chart.
    
    Args:
        natal_chart_json: User's natal chart data (old format)
        transit_date: Date/time for transit calculations (UTC)
        
    Returns:
        Dictionary with transit planet positions and aspects to natal planets
    """
    logger.info(f"Building transits for date: {transit_date.isoformat()}")
    
    try:
        # Extract birth data from natal chart
        # natal_chart_json has "original_input" like: "DOB: 1990-05-15, Time: 14:30, Lat: 40.7128, Lng: -74.0060"
        original_input = natal_chart_json.get("original_input", "")
        
        # Try to extract coordinates from original_input
        import re
        lat_match = re.search(r'Lat:\s*([-+]?\d+\.?\d*)', original_input)
        lng_match = re.search(r'Lng:\s*([-+]?\d+\.?\d*)', original_input)
        
        if not lat_match or not lng_match:
            logger.error("Could not extract coordinates from natal chart")
            raise ValueError("Natal chart missing coordinates")
        
        birth_lat = float(lat_match.group(1))
        birth_lng = float(lng_match.group(1))
        
        # Determine timezone for transit date
        tz_str = _timezone_finder.timezone_at(lat=birth_lat, lng=birth_lng)
        if not tz_str:
            tz_str = "UTC"
            logger.warning(f"Could not determine timezone, using UTC")
        
        logger.info(f"Using timezone: {tz_str} for transits")
        
        # Create AstrologicalSubject for transit date
        transit_subject = AstrologicalSubject(
            name="Transit",
            year=transit_date.year,
            month=transit_date.month,
            day=transit_date.day,
            hour=transit_date.hour,
            minute=transit_date.minute,
            lat=birth_lat,
            lng=birth_lng,
            tz_str=tz_str,
            city="Transit Location",
            online=False
        )
        
        # Extract transit planet positions
        transit_planets = {}
        for planet_attr in PLANET_ATTRS:
            planet_obj = getattr(transit_subject._model, planet_attr)
            planet_name = planet_obj.name
            sign_abbr = planet_obj.sign
            sign = SIGN_MAP.get(sign_abbr, sign_abbr)
            position = planet_obj.position
            retrograde = planet_obj.retrograde
            
            transit_planets[planet_name] = {
                "sign": sign,
                "position": round(position, 2),
                "retrograde": retrograde
            }
        
        # Calculate aspects between transit planets and natal planets
        natal_planets = natal_chart_json.get("planets", {})
        transit_aspects = []
        
        for transit_name, transit_data in transit_planets.items():
            transit_abs = sign_to_abs_degree(transit_data["sign"], transit_data["position"])
            
            for natal_name, natal_data in natal_planets.items():
                if natal_name == "Ascendant":
                    continue  # Skip Ascendant for transit aspects
                
                natal_sign = natal_data.get("sign", "")
                natal_deg = natal_data.get("deg", 0)
                natal_abs = sign_to_abs_degree(natal_sign, natal_deg)
                
                # Calculate aspect angle
                angle_diff = abs(transit_abs - natal_abs)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                # Check for major aspects
                for aspect_name, aspect_angle in MAJOR_ASPECTS.items():
                    orb = 8 if aspect_name in ["Conjunction", "Opposition"] else 6
                    
                    if abs(angle_diff - aspect_angle) <= orb:
                        transit_aspects.append({
                            "transit_planet": transit_name,
                            "natal_planet": natal_name,
                            "aspect": aspect_name,
                            "orb": round(abs(angle_diff - aspect_angle), 2)
                        })
                        break
        
        result = {
            "date": transit_date.isoformat(),
            "planets": transit_planets,
            "aspects_to_natal": transit_aspects
        }
        
        logger.info(f"Transits calculated successfully: {len(transit_planets)} planets, {len(transit_aspects)} aspects")
        return result
        
    except Exception as e:
        logger.exception(f"Failed to build transits: {e}")
        raise Exception(f"Failed to calculate transits: {str(e)}")


def format_transits_for_llm(transits: Dict[str, Any]) -> str:
    """
    Format transit data as readable text for LLM.
    
    Args:
        transits: Transit data from build_transits()
        
    Returns:
        Formatted string suitable for LLM prompt
    """
    lines = [
        f"=== TRANSITS FOR {transits['date']} ===",
        "",
        "Transit Planet Positions:"
    ]
    
    for planet, data in transits["planets"].items():
        retro = " (R)" if data["retrograde"] else ""
        lines.append(f"  {planet}: {data['position']:.2f}° {data['sign']}{retro}")
    
    lines.append("")
    lines.append("Aspects to Natal Chart:")
    
    if not transits["aspects_to_natal"]:
        lines.append("  No major aspects found")
    else:
        for aspect in transits["aspects_to_natal"]:
            lines.append(
                f"  Transit {aspect['transit_planet']} {aspect['aspect']} "
                f"Natal {aspect['natal_planet']} (orb: {aspect['orb']}°)"
            )
    
    return "\n".join(lines)
