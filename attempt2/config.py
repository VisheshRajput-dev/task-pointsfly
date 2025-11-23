"""
Configuration settings for IndiGo flight scraper - Attempt 2
Using undetected-chromedriver for better stealth
"""

# IndiGo website URLs
BASE_URL = "https://www.goindigo.in"
FLIGHT_SEARCH_URL = "https://www.goindigo.in/flight-booking.html"

# Browser settings
HEADLESS_MODE = False  # Set to False to see browser in action
IMPLICIT_WAIT = 10  # Seconds
EXPLICIT_WAIT_TIMEOUT = 30  # Seconds
PAGE_LOAD_TIMEOUT = 30  # Seconds

# User agent to avoid detection
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Delays between actions (in seconds) to avoid being flagged as bot
ACTION_DELAY = 2
AFTER_SEARCH_DELAY = 10  # Wait longer for API to respond

# Airport code mappings (city names to airport codes)
AIRPORT_CODES = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "hyderabad": "HYD",
    "pune": "PNQ",
    "ahmedabad": "AMD",
    "goa": "GOI",
    "kochi": "COK",
    "cochin": "COK",
    "jaipur": "JAI",
    "lucknow": "LKO",
    "varanasi": "VNS",
    "patna": "PAT",
    "guwahati": "GAU",
    "srinagar": "SXR",
    "amritsar": "ATQ",
    "chandigarh": "IXC",
    "dehradun": "DED",
    "indore": "IDR",
    "bhopal": "BHO",
    "nagpur": "NAG",
    "visakhapatnam": "VTZ",
    "vizag": "VTZ",
    "coimbatore": "CJB",
    "madurai": "IXM",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    "mangalore": "IXE",
    "surat": "STV",
    "rajkot": "RAJ",
    "vadodara": "BDQ",
    "baroda": "BDQ",
    "udaipur": "UDR",
    "jodhpur": "JDH",
    "bhubaneswar": "BBI",
    "raipur": "RPR",
    "ranchi": "IXR",
    "imphal": "IMF",
    "agartala": "IXA",
    "aizawl": "AJL",
    "dimapur": "DMU",
    "port blair": "IXZ",
    "leh": "IXL",
}

# Reverse mapping (airport codes to city names)
CODE_TO_CITY = {code: city for city, code in AIRPORT_CODES.items()}
