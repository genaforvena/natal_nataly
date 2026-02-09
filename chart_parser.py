"""
Chart Parser Module
Parses user-uploaded natal charts (e.g., from AstroSeek) into standardized JSON format.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Constants
MAX_ORIGINAL_INPUT_LENGTH = 1000  # Maximum characters to store from original input

# Zodiac signs mapping
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANET_NAMES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Ascendant"]

ASPECT_NAMES = ["Conjunction", "Opposition", "Trine", "Square", "Sextile"]


def normalize_sign_name(sign: str) -> Optional[str]:
    """Normalize zodiac sign name"""
    sign_normalized = sign.strip().capitalize()
    if sign_normalized in ZODIAC_SIGNS:
        return sign_normalized
    return None


def normalize_planet_name(planet: str) -> Optional[str]:
    """Normalize planet name"""
    planet_normalized = planet.strip().capitalize()
    
    # Handle common variations
    variations = {
        "Asc": "Ascendant",
        "Mc": "Midheaven",
        "Node": "North Node"
    }
    
    if planet_normalized in variations:
        planet_normalized = variations[planet_normalized]
    
    if planet_normalized in PLANET_NAMES or planet_normalized == "Midheaven":
        return planet_normalized
    
    return None


def parse_astro_seek_format(text: str) -> Dict:
    """
    Parse AstroSeek text format chart.
    
    Expected format examples:
    Sun: 15°30' Aries, House 7
    Moon: 5°12' Libra, House 1
    Mercury: 28°45' Pisces, House 6 (R)
    
    Or with aspects:
    Sun Square Moon (orb: 0.5°)
    Venus Conjunction Mars (orb: 2.3°)
    """
    logger.info("Parsing AstroSeek format chart")
    
    planets = {}
    houses = {}
    aspects = []
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to parse planet position
        # Pattern: Planet: degree°minutes' Sign, House number (optional R for retrograde)
        planet_match = re.match(
            r'(\w+):\s*(\d+)°(\d+)[\'\′]?\s+(\w+)(?:,?\s+House\s+(\d+))?(?:\s*\(R\))?',
            line,
            re.IGNORECASE
        )
        
        if planet_match:
            planet_name = normalize_planet_name(planet_match.group(1))
            if not planet_name:
                continue
            
            degree_in_sign = float(planet_match.group(2))
            minutes = float(planet_match.group(3))
            degree_in_sign += minutes / 60.0
            
            sign = normalize_sign_name(planet_match.group(4))
            if not sign:
                continue
            
            house = int(planet_match.group(5)) if planet_match.group(5) else 1
            retrograde = '(R)' in line or '(r)' in line
            
            planets[planet_name] = {
                "sign": sign,
                "deg": round(degree_in_sign, 2),
                "house": house,
                "retrograde": retrograde
            }
            continue
        
        # Try to parse aspect
        # Pattern: Planet1 AspectType Planet2 (orb: value°)
        aspect_match = re.match(
            r'(\w+)\s+(\w+)\s+(\w+)(?:\s*\(orb:\s*(\d+\.?\d*)°?\))?',
            line,
            re.IGNORECASE
        )
        
        if aspect_match:
            from_planet = normalize_planet_name(aspect_match.group(1))
            aspect_type = aspect_match.group(2).capitalize()
            to_planet = normalize_planet_name(aspect_match.group(3))
            orb = float(aspect_match.group(4)) if aspect_match.group(4) else 0.0
            
            if from_planet and to_planet and aspect_type in ASPECT_NAMES:
                aspects.append({
                    "from": from_planet,
                    "to": to_planet,
                    "type": aspect_type,
                    "orb": orb,
                    "applying": False  # Unknown from upload
                })
            continue
        
        # Try to parse house cusp
        # Pattern: House 1: 26°30' Virgo
        house_match = re.match(
            r'House\s+(\d+):\s*(\d+)°(\d+)[\'\′]?\s+(\w+)',
            line,
            re.IGNORECASE
        )
        
        if house_match:
            house_num = house_match.group(1)
            degree_in_sign = float(house_match.group(2))
            minutes = float(house_match.group(3))
            degree_in_sign += minutes / 60.0
            sign = normalize_sign_name(house_match.group(4))
            
            if sign:
                houses[house_num] = {
                    "sign": sign,
                    "deg": round(degree_in_sign, 2)
                }
    
    if not planets:
        raise ValueError("No valid planet positions found in uploaded chart")
    
    # Build standardized chart
    chart = {
        "planets": planets,
        "houses": houses if houses else {},
        "aspects": aspects,
        "source": "uploaded",
        "original_input": text[:MAX_ORIGINAL_INPUT_LENGTH],  # Store first N chars of original
        "engine_version": "user_uploaded",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info(f"Successfully parsed chart with {len(planets)} planets, {len(houses)} houses, {len(aspects)} aspects")
    return chart


def parse_uploaded_chart(text: str, format_hint: str = "auto") -> Dict:
    """
    Parse uploaded chart text into standardized JSON format.
    
    Args:
        text: Chart text from user
        format_hint: Format hint ("auto", "astroseek", etc.)
    
    Returns:
        dict: Standardized chart JSON
    """
    logger.info(f"Parsing uploaded chart, format_hint={format_hint}")
    
    if format_hint == "auto" or format_hint == "astroseek":
        try:
            return parse_astro_seek_format(text)
        except Exception as e:
            logger.warning(f"Failed to parse as AstroSeek format: {e}")
    
    # Try other formats here in the future
    
    raise ValueError("Could not parse uploaded chart. Please ensure it's in a supported format (AstroSeek recommended).")


def validate_chart_data(chart: Dict) -> bool:
    """
    Validate that chart has required fields and structure.
    
    Args:
        chart: Chart dictionary to validate
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If chart is invalid
    """
    logger.debug("Validating chart data")
    
    # Required top-level fields
    required_fields = ["planets", "houses", "aspects", "source", "created_at"]
    for field in required_fields:
        if field not in chart:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate planets
    if not isinstance(chart["planets"], dict):
        raise ValueError("'planets' must be a dictionary")
    
    if not chart["planets"]:
        raise ValueError("'planets' cannot be empty")
    
    # Check at least Sun and Moon
    if "Sun" not in chart["planets"] or "Moon" not in chart["planets"]:
        raise ValueError("Chart must contain at least Sun and Moon positions")
    
    # Validate planet structure
    for planet_name, planet_data in chart["planets"].items():
        if not isinstance(planet_data, dict):
            raise ValueError(f"Planet '{planet_name}' data must be a dictionary")
        
        required_planet_fields = ["sign", "deg", "house", "retrograde"]
        for field in required_planet_fields:
            if field not in planet_data:
                raise ValueError(f"Planet '{planet_name}' missing required field: {field}")
        
        # Validate sign
        if planet_data["sign"] not in ZODIAC_SIGNS:
            raise ValueError(f"Invalid zodiac sign for {planet_name}: {planet_data['sign']}")
        
        # Validate degree (0 to less than 30)
        if not (0 <= planet_data["deg"] < 30):
            raise ValueError(f"Invalid degree for {planet_name}: {planet_data['deg']} (must be 0-29.99)")
        
        # Validate house (1-12)
        if not (1 <= planet_data["house"] <= 12):
            raise ValueError(f"Invalid house for {planet_name}: {planet_data['house']} (must be 1-12)")
    
    # Validate houses structure
    if not isinstance(chart["houses"], dict):
        raise ValueError("'houses' must be a dictionary")
    
    # Validate aspects structure
    if not isinstance(chart["aspects"], list):
        raise ValueError("'aspects' must be a list")
    
    logger.info("Chart data validation successful")
    return True
