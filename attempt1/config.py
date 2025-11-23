"""
Configuration settings for SpiceJet flight scraper
"""

# SpiceJet website URLs
SPICEJET_BASE_URL = "https://www.spicejet.com"
SPICEJET_SEARCH_URL = "https://www.spicejet.com/search"

# Browser settings
HEADLESS_MODE = True  # Always headless for SpiceJet
IMPLICIT_WAIT = 10  # Seconds
EXPLICIT_WAIT_TIMEOUT = 30  # Seconds
PAGE_LOAD_TIMEOUT = 60  # Seconds

# User agent to avoid detection
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Delays between actions (in seconds) to avoid being flagged as bot
ACTION_DELAY = 2
AFTER_SEARCH_DELAY = 10  # Wait longer for API to respond

# Airport code mappings (city names to airport codes)
AIRPORT_CODES = {
    # Major Indian cities
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

