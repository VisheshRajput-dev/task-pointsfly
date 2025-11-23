from datetime import datetime
import re
import config

def normalize_city_input(city_input):
    """
    Normalize city input (name or code) to a 3-letter airport code.
    Uses a predefined mapping in config.py.
    """
    if not city_input:
        return None
    
    normalized = city_input.strip().lower()
    
    # Check if it's already an airport code
    if len(normalized) == 3 and normalized.upper() in config.CODE_TO_CITY:
        return normalized.upper()
    
    # Check if it's a city name
    if normalized in config.AIRPORT_CODES:
        return config.AIRPORT_CODES[normalized]
    
    return None

def parse_date(date_string):
    """
    Parse date string in various formats to YYYY-MM-DD format.
    Ensures the date is not in the past.
    """
    if not date_string:
        return None
    
    date_string = date_string.strip()
    
    # Try different separators and patterns
    patterns = [
        (r'(\d{2})[-/.\s](\d{2})[-/.\s](\d{4})', '%d-%m-%Y'),  # DD-MM-YYYY
        (r'(\d{4})[-/.\s](\d{2})[-/.\s](\d{2})', '%Y-%m-%d'),  # YYYY-MM-DD
        (r'(\d{1,2})[-/.\s](\d{1,2})[-/.\s](\d{4})', '%d-%m-%Y'),  # D-M-YYYY
    ]
    
    for pattern, date_format in patterns:
        match = re.match(pattern, date_string)
        if match:
            try:
                # Reconstruct date string with standard separators
                if len(match.group(1)) == 4:  # YYYY-MM-DD format
                    date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                else:  # DD-MM-YYYY format
                    date_str = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Validate date is not in the past
                if parsed_date.date() < datetime.now().date():
                    return None
                
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    return None

def format_flight_data(flights):
    """
    Formats a list of flight dictionaries into a readable table string.
    Supports both IndiGo and SpiceJet formats.
    """
    if not flights:
        return "No flights found."

    # Check if this is SpiceJet data (has fare types)
    is_spicejet = any('spicesaver_price' in flight for flight in flights)
    
    if is_spicejet:
        # SpiceJet format with multiple fare types
        headers = ["Airline", "Flight", "Departure", "Arrival", "Duration", 
                  "SpiceSaver", "SpiceFlex", "SpiceMax", "Points (Saver)"]
        
        # Calculate column widths
        col_widths = {header: len(header) for header in headers}
        for flight in flights:
            col_widths["Airline"] = max(col_widths["Airline"], len(flight.get('airline', 'N/A')))
            col_widths["Flight"] = max(col_widths["Flight"], len(flight.get('flight_number', 'N/A')))
            col_widths["Departure"] = max(col_widths["Departure"], len(flight.get('departure_time', 'N/A')))
            col_widths["Arrival"] = max(col_widths["Arrival"], len(flight.get('arrival_time', 'N/A')))
            col_widths["Duration"] = max(col_widths["Duration"], len(flight.get('duration', 'N/A')))
            col_widths["SpiceSaver"] = max(col_widths["SpiceSaver"], len(flight.get('spicesaver_price', 'N/A')))
            col_widths["SpiceFlex"] = max(col_widths["SpiceFlex"], len(flight.get('spiceflex_price', 'N/A')))
            col_widths["SpiceMax"] = max(col_widths["SpiceMax"], len(flight.get('spicemax_price', 'N/A')))
            # Points can be for any fare type, show all if available
            points_str = flight.get('spicesaver_points', 'N/A')
            if flight.get('spiceflex_points', 'N/A') != 'N/A':
                points_str += f"/{flight.get('spiceflex_points', 'N/A')}"
            if flight.get('spicemax_points', 'N/A') != 'N/A':
                points_str += f"/{flight.get('spicemax_points', 'N/A')}"
            col_widths["Points (Saver)"] = max(col_widths["Points (Saver)"], len(points_str))
        
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
            row.append(flight.get('spicesaver_price', 'N/A').ljust(col_widths["SpiceSaver"]))
            row.append(flight.get('spiceflex_price', 'N/A').ljust(col_widths["SpiceFlex"]))
            row.append(flight.get('spicemax_price', 'N/A').ljust(col_widths["SpiceMax"]))
            # Show all points if available
            points_str = flight.get('spicesaver_points', 'N/A')
            if flight.get('spiceflex_points', 'N/A') != 'N/A':
                points_str += f"/{flight.get('spiceflex_points', 'N/A')}"
            if flight.get('spicemax_points', 'N/A') != 'N/A':
                points_str += f"/{flight.get('spicemax_points', 'N/A')}"
            row.append(points_str.ljust(col_widths["Points (Saver)"]))
            result.append(" | ".join(row))
        
        result.append(f"\nTotal flights found: {len(flights)}")
        return "\n".join(result)
    else:
        # IndiGo format (original)
        headers = ["Airline", "Flight", "Departure", "Arrival", "Duration", "Price (INR)", "Points"]
        
        # Calculate column widths
        col_widths = {header: len(header) for header in headers}
        for flight in flights:
            col_widths["Airline"] = max(col_widths["Airline"], len(flight.get('airline', 'N/A')))
            col_widths["Flight"] = max(col_widths["Flight"], len(flight.get('flight_number', 'N/A')))
            col_widths["Departure"] = max(col_widths["Departure"], len(flight.get('departure_time', 'N/A')))
            col_widths["Arrival"] = max(col_widths["Arrival"], len(flight.get('arrival_time', 'N/A')))
            col_widths["Duration"] = max(col_widths["Duration"], len(flight.get('duration', 'N/A')))
            col_widths["Price (INR)"] = max(col_widths["Price (INR)"], len(flight.get('price_inr', 'N/A')))
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
            row.append(flight.get('price_inr', 'N/A').ljust(col_widths["Price (INR)"]))
            row.append(flight.get('award_points', 'N/A').ljust(col_widths["Points"]))
            result.append(" | ".join(row))
        
        result.append(f"\nTotal flights found: {len(flights)}")
        return "\n".join(result)
