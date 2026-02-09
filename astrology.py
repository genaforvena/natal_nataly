import swisseph as swe

EPHE_PATH = "./ephe"
swe.set_ephe_path(EPHE_PATH)

def generate_natal_chart(dob: str, time: str, lat: float, lng: float) -> dict:
    '''
    Returns structured natal chart JSON.
    '''
    return {
        "status": "not_implemented"
    }
