from datetime import datetime
import re
import config

def normalize_city_input(city_input):
    """
    Normalize city input (name or code) to a 3-letter airport code.
    Uses a predefined mapping in config.py.
    Works for international airports (Etihad primarily serves international routes).
    """
    if not city_input:
        return None
    
    normalized = city_input.strip().lower()
    
    # Check if it's already an airport code (3 letters)
    if len(normalized) == 3 and normalized.upper() in config.CODE_TO_CITY:
        return normalized.upper()
    
    # Check if it's a city name
    if normalized in config.AIRPORT_CODES:
        return config.AIRPORT_CODES[normalized]
    
    # If not found, return the uppercase version (might be a valid airport code not in our list)
    return normalized.upper() if len(normalized) == 3 else None

def parse_date(date_string):
    """
    Parse date string in various formats to YYYY-MM-DD format.
    Ensures the date is not in the past.
    """
    if not date_string:
        return None
    
    date_string = date_string.strip()
    
    # Try different date formats
    formats = [
        "%Y-%m-%d",      # 2025-12-18
        "%d-%m-%Y",      # 18-12-2025
        "%d/%m/%Y",      # 18/12/2025
        "%Y/%m/%d",      # 2025/12/18
        "%d.%m.%Y",      # 18.12.2025
        "%Y.%m.%d",      # 2025.12.18
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_string, fmt)
            # Check if date is not in the past
            if date_obj.date() >= datetime.now().date():
                return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None

def format_date_for_etihad(date_string):
    """
    Convert date from YYYY-MM-DD to Etihad's format: DATE_1=202511300000
    Format: YYYYMMDDHHMM (date + 0000 for time)
    """
    try:
        # Parse the date
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        # Format as YYYYMMDD0000
        return date_obj.strftime("%Y%m%d0000")
    except:
        return None

def format_flight_data(flights):
    """
    Formats a list of flight dictionaries into a readable table string.
    Supports Etihad format (single price, may have different fare classes).
    """
    if not flights:
        return "No flights found."

    # Etihad format (similar to IndiGo - single price)
    headers = ["Airline", "Flight", "Departure", "Arrival", "Duration", "Price", "Points"]
    
    # Calculate column widths
    col_widths = {header: len(header) for header in headers}
    for flight in flights:
        col_widths["Airline"] = max(col_widths["Airline"], len(flight.get('airline', 'N/A')))
        col_widths["Flight"] = max(col_widths["Flight"], len(flight.get('flight_number', 'N/A')))
        col_widths["Departure"] = max(col_widths["Departure"], len(flight.get('departure_time', 'N/A')))
        col_widths["Arrival"] = max(col_widths["Arrival"], len(flight.get('arrival_time', 'N/A')))
        col_widths["Duration"] = max(col_widths["Duration"], len(flight.get('duration', 'N/A')))
        col_widths["Price"] = max(col_widths["Price"], len(flight.get('price', 'N/A')))
        col_widths["Points"] = max(col_widths["Points"], len(flight.get('award_points', 'N/A')))
    
    # Build header line
    header_line = " | ".join(header.ljust(col_widths[header]) for header in headers)
    separator_line = "-+-".join("-" * col_widths[header] for header in headers)
    
    result = [header_line, separator_line]
    
    # Add flight data
    for flight in flights:
        row = []
        row.append(flight.get('airline', 'N/A').ljust(col_widths["Airline"]))
        row.append(flight.get('flight_number', 'N/A').ljust(col_widths["Flight"]))
        row.append(flight.get('departure_time', 'N/A').ljust(col_widths["Departure"]))
        row.append(flight.get('arrival_time', 'N/A').ljust(col_widths["Arrival"]))
        row.append(flight.get('duration', 'N/A').ljust(col_widths["Duration"]))
        row.append(flight.get('price', 'N/A').ljust(col_widths["Price"]))
        row.append(flight.get('award_points', 'N/A').ljust(col_widths["Points"]))
        result.append(" | ".join(row))
    
    result.append(f"\nTotal flights found: {len(flights)}")
    return "\n".join(result)

