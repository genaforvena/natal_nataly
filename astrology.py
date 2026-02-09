import swisseph as swe
from datetime import datetime

EPHE_PATH = "./ephe"
swe.set_ephe_path(EPHE_PATH)

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
    dt = datetime.strptime(f"{dob} {time}", "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day, 
                    dt.hour + dt.minute / 60.0)
    return jd

def generate_natal_chart(dob: str, time: str, lat: float, lng: float) -> dict:
    '''
    Returns structured natal chart JSON.
    '''
    try:
        # Convert to Julian Day
        jd = datetime_to_julian(dob, time)
        
        # Calculate planets
        chart = {}
        for planet_name, planet_id in PLANETS.items():
            result = swe.calc_ut(jd, planet_id)
            degree = result[0][0]
            sign = get_zodiac_sign(degree)
            chart[planet_name] = {
                "degree": degree,
                "sign": sign
            }
        
        # Calculate Ascendant
        houses = swe.houses(jd, lat, lng, b'P')  # Placidus house system
        asc_degree = houses[1][0]  # Ascendant
        chart["Ascendant"] = {
            "degree": asc_degree,
            "sign": get_zodiac_sign(asc_degree)
        }
        
        return chart
    except Exception as e:
        raise Exception(f"Failed to generate natal chart: {str(e)}")
