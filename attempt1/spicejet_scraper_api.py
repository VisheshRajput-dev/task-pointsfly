"""
SpiceJet Scraper API Wrapper
Outputs JSON for API consumption
"""

import sys
import json
import os
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO, TextIOWrapper

# Set stdout encoding to UTF-8 to handle Unicode characters like ₹
# This is needed for Windows which defaults to cp1252
if hasattr(sys.stdout, 'buffer'):
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except:
            pass  # If it fails, we'll use ensure_ascii=True instead
if hasattr(sys.stderr, 'buffer'):
    if sys.stderr.encoding != 'utf-8':
        try:
            sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except:
            pass

# Suppress print statements from scraper
class SuppressOutput:
    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
    
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        return self
    
    def __exit__(self, *args):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

def main():
    if len(sys.argv) < 4:
        # Write to stderr for errors, stdout only for JSON
        sys.stderr.write(json.dumps({"error": "Missing arguments: origin destination date"}) + "\n")
        sys.exit(1)
    
    origin_input = sys.argv[1]
    destination_input = sys.argv[2]
    date_input = sys.argv[3]
    
    # Import after setting up suppression
    from spicejet_scraper import SpiceJetScraper
    from utils import normalize_city_input, parse_date
    
    # Normalize inputs
    origin = normalize_city_input(origin_input)
    destination = normalize_city_input(destination_input)
    date = parse_date(date_input)
    
    # Validate inputs
    if not origin:
        sys.stderr.write(json.dumps({"error": f"Invalid origin: {origin_input}"}) + "\n")
        sys.exit(1)
    
    if not destination:
        sys.stderr.write(json.dumps({"error": f"Invalid destination: {destination_input}"}) + "\n")
        sys.exit(1)
    
    if not date:
        sys.stderr.write(json.dumps({"error": f"Invalid date: {date_input}"}) + "\n")
        sys.exit(1)
    
    # Create scraper and scrape (suppress all print output)
    try:
        with SuppressOutput():
            scraper = SpiceJetScraper()
            flights = scraper.scrape_flights(origin, destination, date)
    except Exception as e:
        # Write error to stderr, not stdout
        sys.stderr.write(json.dumps({"error": f"Scraping failed: {str(e)}"}) + "\n")
        sys.exit(1)
    
    # Output JSON to stdout only (this is the only thing that should be in stdout)
    result = {
        "success": True,
        "flights": flights,
        "count": len(flights)
    }
    
    # Use ensure_ascii=True to escape Unicode characters (like ₹) as \u20b9
    # This ensures compatibility with Windows cp1252 encoding
    # The frontend will decode these Unicode escape sequences
    json_output = json.dumps(result, indent=2, ensure_ascii=True)
    
    # Write to stdout - use buffer if available to avoid encoding issues
    try:
        if hasattr(sys.stdout, 'buffer'):
            # Write bytes directly to avoid encoding issues
            sys.stdout.buffer.write(json_output.encode('utf-8'))
            sys.stdout.buffer.flush()
        else:
            sys.stdout.write(json_output)
            sys.stdout.flush()
    except (UnicodeEncodeError, AttributeError):
        # Final fallback: write bytes directly
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(json_output.encode('utf-8'))
            sys.stdout.buffer.flush()
        else:
            # Last resort: use ASCII encoding
            sys.stdout.write(json_output.encode('ascii', errors='replace').decode('ascii'))
            sys.stdout.flush()
    
    # Ensure output is complete before exiting
    import time
    time.sleep(0.1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()

