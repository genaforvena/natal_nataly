"""
DEPRECATED: This module is no longer used in production.
The natal chart generation has been migrated to use Kerykeion library.

See: services/chart_builder.py for the new implementation.

This file is kept for reference only. The old implementation used pyswisseph directly,
while the new implementation uses Kerykeion (which itself uses Swiss Ephemeris as backend)
and provides better structure and timezone handling.

Migration notes:
- Old function: generate_natal_chart(dob, time, lat, lng, original_input)
- New function: services.chart_builder.build_natal_chart_text_and_json(...)
- New implementation provides both text export (AstroSeek format) and structured JSON
- Timezone is automatically determined from coordinates using timezonefinder
"""

import swisseph as swe
import logging
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)

EPHE_PATH = "./ephe"
HOUSE_SYSTEM = b'P'  # Placidus house system
swe.set_ephe_path(EPHE_PATH)
logger.info(f"Swiss Ephemeris path set to: {EPHE_PATH}")

# Get Swiss Ephemeris version for tracking
try:
    SWISSEPH_VERSION = swe.version
    logger.info(f"Swiss Ephemeris version: {SWISSEPH_VERSION}")
except:
    SWISSEPH_VERSION = "unknown"
    logger.warning("Could not determine Swiss Ephemeris version")

# Zodiac signs
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Planet constants
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

# Aspect definitions with orbs
ASPECTS = {
    "Conjunction": {"angle": 0, "orb": 8},
    "Opposition": {"angle": 180, "orb": 8},
    "Trine": {"angle": 120, "orb": 8},
    "Square": {"angle": 90, "orb": 8},
    "Sextile": {"angle": 60, "orb": 6}
}

def get_zodiac_sign(degree: float) -> str:
    """Convert degree to zodiac sign"""
    sign_index = int(degree / 30)
    return ZODIAC_SIGNS[sign_index]

def get_degree_in_sign(degree: float) -> float:
    """Get degree within the sign (0-30)"""
    return degree % 30

def get_house_for_planet(planet_degree: float, house_cusps: list) -> int:
    """Determine which house a planet is in"""
    # Normalize planet degree
    planet_deg = planet_degree % 360
    
    # Find the house by comparing with cusps
    for i in range(12):
        cusp_start = house_cusps[i] % 360
        cusp_end = house_cusps[(i + 1) % 12] % 360
        
        if cusp_start < cusp_end:
            if cusp_start <= planet_deg < cusp_end:
                return i + 1
        else:  # Wraps around 0 degrees
            if planet_deg >= cusp_start or planet_deg < cusp_end:
                return i + 1
    
    return 1  # Default to first house if not found

def calculate_aspect_angle(deg1: float, deg2: float) -> float:
    """Calculate the shortest angle between two degrees"""
    diff = abs(deg1 - deg2)
    if diff > 180:
        diff = 360 - diff
    return diff

def is_applying(deg1: float, deg2: float, speed1: float, speed2: float, aspect_angle: float) -> bool:
    """
    Determine if an aspect is applying (getting closer) or separating.
    
    An aspect is applying if the angle between the planets is decreasing,
    meaning the faster planet is approaching the exact aspect angle.
    """
    current_angle = calculate_aspect_angle(deg1, deg2)
    
    # If speeds are equal, aspect is neither applying nor separating
    if abs(speed1 - speed2) < 0.001:
        return False
    
    # Calculate the rate of change of the angle
    # Positive rate means separating, negative means applying
    relative_speed = speed1 - speed2
    
    # Determine if the angle is getting smaller
    # If the faster planet is behind and catching up, it's applying
    if relative_speed > 0:
        # Planet 1 is moving faster
        # Check if it's approaching the aspect angle
        # This is a simplified approach - for proper calculation, we'd need
        # to consider the specific aspect and zodiacal positions
        return True  # Conservative: assume applying if faster
    else:
        return False

def calculate_aspects(planet_positions: dict) -> list:
    """Calculate aspects between planets"""
    aspects = []
    planet_list = list(planet_positions.keys())
    
    for i, planet1 in enumerate(planet_list):
        for planet2 in planet_list[i+1:]:
            if planet1 == "Ascendant" or planet2 == "Ascendant":
                continue  # Skip Ascendant for aspects
            
            deg1 = planet_positions[planet1]["degree"]
            deg2 = planet_positions[planet2]["degree"]
            speed1 = planet_positions[planet1].get("speed", 0)
            speed2 = planet_positions[planet2].get("speed", 0)
            
            angle = calculate_aspect_angle(deg1, deg2)
            
            # Check each aspect type
            for aspect_name, aspect_data in ASPECTS.items():
                aspect_angle = aspect_data["angle"]
                orb = aspect_data["orb"]
                
                diff_from_aspect = abs(angle - aspect_angle)
                if diff_from_aspect <= orb:
                    applying = is_applying(deg1, deg2, speed1, speed2, aspect_angle)
                    aspects.append({
                        "from": planet1,
                        "to": planet2,
                        "type": aspect_name,
                        "orb": round(diff_from_aspect, 2),
                        "applying": applying
                    })
                    break  # Found an aspect, move to next planet pair
    
    return aspects

def datetime_to_julian(dob: str, time: str) -> float:
    """Convert date and time to Julian Day"""
    logger.debug(f"Converting datetime to Julian")
    try:
        dt = datetime.strptime(f"{dob} {time}", "%Y-%m-%d %H:%M")
        jd = swe.julday(dt.year, dt.month, dt.day, 
                        dt.hour + dt.minute / 60.0)
        logger.debug(f"Julian Day calculated: {jd}")
        return jd
    except Exception as e:
        logger.exception(f"Error converting datetime to Julian: {e}")
        raise

def generate_natal_chart(dob: str, time: str, lat: float, lng: float, original_input: str = None) -> dict:
    '''
    Generate complete natal chart in standardized JSON format.
    
    Returns:
        dict: Standardized chart with planets, houses, aspects, and metadata
    '''
    # Log only that we're generating, not the sensitive birth details
    logger.info(f"Generating natal chart")
    try:
        # Convert to Julian Day
        jd = datetime_to_julian(dob, time)
        
        # Calculate houses first
        logger.debug("Calculating house cusps")
        houses_result = swe.houses(jd, lat, lng, HOUSE_SYSTEM)
        house_cusps = houses_result[0]  # 12 house cusps
        
        # Calculate planets
        planets = {}
        logger.debug("Calculating planetary positions")
        for planet_name, planet_id in PLANETS.items():
            result = swe.calc_ut(jd, planet_id)
            degree = result[0][0]
            speed = result[0][3]  # Daily speed
            sign = get_zodiac_sign(degree)
            deg_in_sign = get_degree_in_sign(degree)
            house = get_house_for_planet(degree, house_cusps)
            is_retrograde = speed < 0
            
            planets[planet_name] = {
                "sign": sign,
                "deg": round(deg_in_sign, 2),
                "house": house,
                "retrograde": is_retrograde,
                "degree": degree,  # Full degree for aspect calculations
                "speed": speed
            }
            logger.debug(f"{planet_name}: {deg_in_sign:.2f}° {sign}, House {house}, Retrograde: {is_retrograde}")
        
        # Calculate Ascendant (1st house cusp)
        asc_degree = house_cusps[0]
        planets["Ascendant"] = {
            "sign": get_zodiac_sign(asc_degree),
            "deg": round(get_degree_in_sign(asc_degree), 2),
            "house": 1,
            "retrograde": False,
            "degree": asc_degree,
            "speed": 0
        }
        logger.debug(f"Ascendant: {planets['Ascendant']['deg']:.2f}° in {planets['Ascendant']['sign']}")
        
        # Build houses dictionary
        houses = {}
        for i in range(12):
            house_num = i + 1
            house_deg = house_cusps[i]
            houses[str(house_num)] = {
                "sign": get_zodiac_sign(house_deg),
                "deg": round(get_degree_in_sign(house_deg), 2)
            }
        
        # Calculate aspects
        logger.debug("Calculating aspects")
        aspects = calculate_aspects(planets)
        
        # Remove temporary fields used for calculations
        for planet_data in planets.values():
            planet_data.pop("degree", None)
            planet_data.pop("speed", None)
        
        # Build standardized chart
        chart = {
            "planets": planets,
            "houses": houses,
            "aspects": aspects,
            "source": "generated",
            "original_input": original_input or f"DOB: {dob}, Time: {time}, Lat: {lat}, Lng: {lng}",
            "engine_version": f"swisseph {SWISSEPH_VERSION}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info("Natal chart generated successfully")
        return chart
    except Exception as e:
        logger.exception(f"Failed to generate natal chart: {str(e)}")
        raise Exception(f"Failed to generate natal chart: {str(e)}")


def get_engine_version() -> str:
    """Get the version of the astrology engine (Swiss Ephemeris)"""
    return SWISSEPH_VERSION
