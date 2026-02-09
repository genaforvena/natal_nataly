import swisseph as swe
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

EPHE_PATH = "./ephe"
HOUSE_SYSTEM = b'P'  # Placidus house system
swe.set_ephe_path(EPHE_PATH)
logger.info(f"Swiss Ephemeris path set to: {EPHE_PATH}")

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

def get_zodiac_sign(degree: float) -> str:
    """Convert degree to zodiac sign"""
    sign_index = int(degree / 30)
    return ZODIAC_SIGNS[sign_index]

def datetime_to_julian(dob: str, time: str) -> float:
    """Convert date and time to Julian Day"""
    logger.debug(f"Converting datetime to Julian: dob={dob}, time={time}")
    try:
        dt = datetime.strptime(f"{dob} {time}", "%Y-%m-%d %H:%M")
        jd = swe.julday(dt.year, dt.month, dt.day, 
                        dt.hour + dt.minute / 60.0)
        logger.debug(f"Julian Day calculated: {jd}")
        return jd
    except Exception as e:
        logger.exception(f"Error converting datetime to Julian: {e}")
        raise

def generate_natal_chart(dob: str, time: str, lat: float, lng: float) -> dict:
    '''
    Returns structured natal chart JSON.
    '''
    logger.info(f"Generating natal chart for dob={dob}, time={time}, lat={lat}, lng={lng}")
    try:
        # Convert to Julian Day
        jd = datetime_to_julian(dob, time)
        
        # Calculate planets
        chart = {}
        logger.debug("Calculating planetary positions")
        for planet_name, planet_id in PLANETS.items():
            result = swe.calc_ut(jd, planet_id)
            degree = result[0][0]
            sign = get_zodiac_sign(degree)
            chart[planet_name] = {
                "degree": degree,
                "sign": sign
            }
            logger.debug(f"{planet_name}: {degree:.2f}° in {sign}")
        
        # Calculate Ascendant
        logger.debug("Calculating house cusps and Ascendant")
        houses = swe.houses(jd, lat, lng, HOUSE_SYSTEM)
        asc_degree = houses[1][0]  # Ascendant
        chart["Ascendant"] = {
            "degree": asc_degree,
            "sign": get_zodiac_sign(asc_degree)
        }
        logger.debug(f"Ascendant: {asc_degree:.2f}° in {chart['Ascendant']['sign']}")
        
        logger.info("Natal chart generated successfully")
        return chart
    except Exception as e:
        logger.exception(f"Failed to generate natal chart: {str(e)}")
        raise Exception(f"Failed to generate natal chart: {str(e)}")
