"""
Configuration settings for Etihad Airways flight scraper
"""

# Etihad website URLs
ETIHAD_BASE_URL = "https://digital.etihad.com"
ETIHAD_SEARCH_URL = "https://digital.etihad.com/book/search"

# Browser settings
HEADLESS_MODE = False  # Set to False to see browser (for testing), True for headless
IMPLICIT_WAIT = 10  # Seconds
EXPLICIT_WAIT_TIMEOUT = 30  # Seconds
PAGE_LOAD_TIMEOUT = 60  # Seconds

# User agent to avoid detection (updated to latest Chrome)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# Delays between actions (in seconds) to avoid being flagged as bot
ACTION_DELAY = 3
AFTER_SEARCH_DELAY = 20  # Wait longer for redirect and API to respond

# Airport code mappings (city names to airport codes)
# Etihad primarily serves international routes
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
    "kochi": "COK",
    "cochin": "COK",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    # Middle East (Etihad's hub region)
    "abu dhabi": "AUH",
    "dubai": "DXB",
    "doha": "DOH",
    "riyadh": "RUH",
    "jeddah": "JED",
    "dammam": "DMM",
    "kuwait": "KWI",
    "muscat": "MCT",
    "bahrain": "BAH",
    "manama": "BAH",
    # Asia
    "singapore": "SIN",
    "bangkok": "BKK",
    "kuala lumpur": "KUL",
    "jakarta": "CGK",
    "manila": "MNL",
    "hong kong": "HKG",
    "tokyo": "NRT",
    "osaka": "KIX",
    "seoul": "ICN",
    "beijing": "PEK",
    "shanghai": "PVG",
    "guangzhou": "CAN",
    "shenzhen": "SZX",
    "chengdu": "CTU",
    "mumbai": "BOM",
    "delhi": "DEL",
    "bangalore": "BLR",
    "chennai": "MAA",
    "kolkata": "CCU",
    "hyderabad": "HYD",
    "kochi": "COK",
    "colombo": "CMB",
    "dhaka": "DAC",
    "kathmandu": "KTM",
    "islamabad": "ISB",
    "karachi": "KHI",
    "lahore": "LHE",
    # Europe
    "london": "LHR",
    "manchester": "MAN",
    "edinburgh": "EDI",
    "paris": "CDG",
    "frankfurt": "FRA",
    "munich": "MUC",
    "amsterdam": "AMS",
    "rome": "FCO",
    "milan": "MXP",
    "madrid": "MAD",
    "barcelona": "BCN",
    "zurich": "ZRH",
    "vienna": "VIE",
    "brussels": "BRU",
    "istanbul": "IST",
    "athens": "ATH",
    "moscow": "SVO",
    "dublin": "DUB",
    # North America
    "new york": "JFK",
    "newark": "EWR",
    "washington": "IAD",
    "chicago": "ORD",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "toronto": "YYZ",
    "vancouver": "YVR",
    "montreal": "YUL",
    # Africa
    "cairo": "CAI",
    "casablanca": "CMN",
    "johannesburg": "JNB",
    "cape town": "CPT",
    "nairobi": "NBO",
    "lagos": "LOS",
    "accra": "ACC",
    # Australia/Oceania
    "sydney": "SYD",
    "melbourne": "MEL",
    "perth": "PER",
    "brisbane": "BNE",
    "auckland": "AKL",
}

# Reverse mapping (airport codes to city names)
CODE_TO_CITY = {code: city for city, code in AIRPORT_CODES.items()}

