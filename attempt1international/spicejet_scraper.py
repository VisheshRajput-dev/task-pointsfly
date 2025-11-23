"""
SpiceJet International Flight Scraper
Uses network request interception to get flight data directly from API
Works for international routes (e.g., DEL to DXB, BOM to SIN, etc.)
"""

import time
import sys
import json
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from datetime import datetime
import config
from utils import normalize_city_input, parse_date, format_flight_data


class SpiceJetScraper:
    """Scraper class for SpiceJet international flight data using Playwright with network interception"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.flight_data = None
        self.all_responses = []
    
    def setup_driver(self):
        """Initialize and configure browser using Playwright in headless mode"""
        try:
            print("Setting up browser with Playwright (headless mode)...")
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    f'--user-agent={config.USER_AGENT}',
                ]
            )
            self.page = self.browser.new_page()
            
            # Set up response interception BEFORE creating page context
            def handle_response(response):
                try:
                    if response.status == 200:
                        url = response.url
                        # Look for SpiceJet API endpoints
                        if 'spicejet' in url.lower() and 'api' in url.lower():
                            # Check if response contains JSON
                            content_type = response.headers.get('content-type', '')
                            if 'json' in content_type.lower() or response.status == 200:
                                try:
                                    data = response.json()
                                    # Store all API responses
                                    self.all_responses.append({'url': url, 'data': data})
                                    
                                    # Prioritize search/availability endpoints
                                    if 'search' in url.lower() and ('availability' in url.lower() or 'lowfare' in url.lower()):
                                        # Check if this looks like flight data
                                        if isinstance(data, dict) or isinstance(data, list):
                                            # Store the response data (prioritize availability endpoint)
                                            if 'availability' in url.lower():
                                                self.flight_data = data
                                                print(f"✓ Captured flight data from: {url}")
                                                # Save for debugging
                                                try:
                                                    with open('spicejet_api_response.json', 'w', encoding='utf-8') as f:
                                                        json.dump(data, f, indent=2, ensure_ascii=False)
                                                    print("  Saved API response to spicejet_api_response.json")
                                                except:
                                                    pass
                                            elif not self.flight_data and 'lowfare' in url.lower():
                                                self.flight_data = data
                                                print(f"✓ Captured flight data from: {url}")
                                except Exception as e:
                                    # Not JSON or error parsing
                                    pass
                except:
                    pass
            
            # Listen for responses - MUST be before navigation
            self.page.on("response", handle_response)
            
            print("Browser initialized successfully (headless mode)!")
            return True
        except Exception as e:
            print(f"Error setting up browser: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """Close the browser"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
    
    def build_search_url(self, origin, destination, date):
        """Build SpiceJet search URL with parameters (works for both domestic and international)"""
        # Format: https://www.spicejet.com/search?from=DEL&to=DXB&tripType=1&departure=2025-12-31&adult=1&child=0&srCitizen=0&infant=0&currency=INR&redirectTo=/
        
        # Format date as YYYY-MM-DD
        date_parts = date.split('-')
        if len(date_parts) == 3:
            if len(date_parts[0]) == 4:  # YYYY-MM-DD
                formatted_date = date
            else:  # DD-MM-YYYY
                formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
        else:
            formatted_date = date
        
        url = f"https://www.spicejet.com/search?from={origin}&to={destination}&tripType=1&departure={formatted_date}&adult=1&child=0&srCitizen=0&infant=0&currency=INR&redirectTo=/"
        return url
    
    def load_search_page(self, origin, destination, date, retry_count=0):
        """Load SpiceJet search page and wait for API calls"""
        max_retries = 2  # Try up to 3 times total (initial + 2 retries)
        
        try:
            if retry_count > 0:
                print(f"\nRetry attempt {retry_count}/{max_retries} - Reloading page...")
                time.sleep(2)  # Brief pause before retry
            
            print(f"Loading SpiceJet search page: {origin} -> {destination} on {date}")
            
            url = self.build_search_url(origin, destination, date)
            print(f"URL: {url}")
            
            # Reset flight_data for this attempt
            if retry_count > 0:
                self.flight_data = None
            
            # Navigate to the page
            self.page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(10)  # Wait longer for API calls and page rendering
            
            # Also wait for specific elements that indicate page loaded
            try:
                self.page.wait_for_selector("body", timeout=10000)
                # Wait for flight results to appear (SG for SpiceJet flights)
                self.page.wait_for_selector("*:has-text('SG')", timeout=15000)
                time.sleep(5)  # Additional wait for dynamic content and prices to load
            except:
                time.sleep(5)  # Fallback wait
            
            # Debug: Print what we captured
            if self.flight_data:
                print(f"✓ Captured API response")
                print(f"Captured data type: {type(self.flight_data)}")
                if isinstance(self.flight_data, dict):
                    print(f"Data keys: {list(self.flight_data.keys())[:10]}")
                    # Print first level structure
                    for key, value in list(self.flight_data.items())[:3]:
                        print(f"  {key}: {type(value)} - {str(value)[:100] if not isinstance(value, (dict, list)) else '...'}")
                elif isinstance(self.flight_data, list):
                    print(f"Data list length: {len(self.flight_data)}")
                    if len(self.flight_data) > 0:
                        print(f"First item type: {type(self.flight_data[0])}")
                        if isinstance(self.flight_data[0], dict):
                            print(f"First item keys: {list(self.flight_data[0].keys())[:10]}")
            else:
                print("⚠ No API response captured yet")
            
            # If we didn't capture data via interception, try to get it from page
            if not self.flight_data:
                print("Trying to extract from page scripts...")
                # Try to find JSON data in the page
                try:
                    # Look for script tags with flight data
                    scripts = self.page.query_selector_all("script")
                    for script in scripts:
                        try:
                            content = script.inner_text()
                            if 'flight' in content.lower() and 'price' in content.lower():
                                # Try to extract JSON from script
                                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                                if json_match:
                                    try:
                                        data = json.loads(json_match.group(0))
                                        self.flight_data = data
                                        print("✓ Found flight data in page scripts")
                                        break
                                    except:
                                        pass
                        except:
                            continue
                except:
                    pass
            
            # Check if we still don't have API data and should retry
            if not self.flight_data and retry_count < max_retries:
                print(f"\n⚠ API response not captured. Retrying... (Attempt {retry_count + 1}/{max_retries})")
                return self.load_search_page(origin, destination, date, retry_count + 1)
            elif not self.flight_data:
                print("\n⚠ API response not captured after all retries. Will extract from HTML only.")
            
            return True
        except Exception as e:
            print(f"Error loading search page: {e}")
            # Retry on error if we haven't exceeded max retries
            if retry_count < max_retries:
                print(f"\n⚠ Error occurred. Retrying... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(3)
                return self.load_search_page(origin, destination, date, retry_count + 1)
            import traceback
            traceback.print_exc()
            return False
    
    def extract_flights_from_data(self):
        """Extract flight data from captured API response or page"""
        flights = []
        
        try:
            # Always parse HTML to get prices and points (API doesn't have prices)
            print("Extracting flights from HTML (for prices and points)...")
            html_flights = self._parse_html()
            
            # If we have API response data, merge with HTML data
            if self.flight_data:
                print("Merging API data with HTML data...")
                api_flights = self._parse_api_response(self.flight_data)
                
                # Create a dictionary to track merged flights (avoid duplicates)
                merged_flights_dict = {}
                
                # First, add all HTML flights (they have prices/points)
                for html_flight in html_flights:
                    flight_num = html_flight.get('flight_number', '')
                    if flight_num and flight_num != 'N/A':
                        # Use flight number as key, but also check times to avoid duplicates
                        key = f"{flight_num}_{html_flight.get('departure_time', 'N/A')}_{html_flight.get('arrival_time', 'N/A')}"
                        if key not in merged_flights_dict:
                            merged_flights_dict[key] = html_flight.copy()
                
                # Now merge API flights with HTML flights by flight number and times
                for api_flight in api_flights:
                    flight_num = api_flight.get('flight_number', '')
                    if not flight_num or flight_num == 'N/A':
                        continue
                    
                    # Try to find matching HTML flight by flight number and times
                    matched = False
                    for key, html_flight in merged_flights_dict.items():
                        if html_flight.get('flight_number') == flight_num:
                            # Check if times match (within reasonable tolerance)
                            api_dep = api_flight.get('departure_time', '')
                            api_arr = api_flight.get('arrival_time', '')
                            html_dep = html_flight.get('departure_time', '')
                            html_arr = html_flight.get('arrival_time', '')
                            
                            # If times match or HTML doesn't have times, merge
                            if (api_dep == html_dep or html_dep == 'N/A') and (api_arr == html_arr or html_arr == 'N/A'):
                                # Merge: use API for basic info, keep HTML for prices/points
                                merged_flights_dict[key].update({
                                    'departure_time': api_dep if api_dep != 'N/A' else html_dep,
                                    'arrival_time': api_arr if api_arr != 'N/A' else html_arr,
                                    'duration': api_flight.get('duration', html_flight.get('duration')),
                                })
                                matched = True
                                break
                    
                    # If no match found, add API flight (but it won't have prices)
                    if not matched:
                        key = f"{flight_num}_{api_flight.get('departure_time', 'N/A')}_{api_flight.get('arrival_time', 'N/A')}"
                        if key not in merged_flights_dict:
                            merged_flights_dict[key] = api_flight.copy()
                
                # Final deduplication: remove any remaining duplicates
                # Use full flight number + times to ensure uniqueness
                final_flights = []
                seen_keys = set()
                for flight in merged_flights_dict.values():
                    flight_num = flight.get('flight_number', '')
                    dep_time = flight.get('departure_time', 'N/A')
                    arr_time = flight.get('arrival_time', 'N/A')
                    # Use full flight number (not just first) to distinguish connecting flights
                    key = f"{flight_num}_{dep_time}_{arr_time}"
                    
                    if key not in seen_keys:
                        seen_keys.add(key)
                        final_flights.append(flight)
                
                flights = final_flights
            else:
                # No API data, just use HTML flights
                # Remove duplicates
                seen = set()
                unique_flights = []
                for flight in html_flights:
                    flight_num = flight.get('flight_number', '')
                    dep_time = flight.get('departure_time', 'N/A')
                    arr_time = flight.get('arrival_time', 'N/A')
                    # Use first flight number for connecting flights
                    first_num = flight_num.split(',')[0].strip() if ',' in flight_num else flight_num
                    key = f"{first_num}_{dep_time}_{arr_time}"
                    if key not in seen:
                        seen.add(key)
                        unique_flights.append(flight)
                flights = unique_flights
            
            return flights
            
        except Exception as e:
            print(f"Error extracting flights: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_api_response(self, data):
        """Parse flight data from API JSON response"""
        flights = []
        
        try:
            # SpiceJet API structure - try to find flight data
            if isinstance(data, dict):
                # Look for common keys that might contain flight data
                possible_keys = [
                    'flights', 'data', 'results', 'items', 'flightList', 'schedules',
                    'availability', 'availabilityList', 'journeys', 'journeyList',
                    'outbound', 'inbound', 'segments', 'segmentList'
                ]
                
                flight_list = None
                for key in possible_keys:
                    if key in data:
                        flight_list = data[key]
                        break
                
                # If no key found, try nested structures
                if not flight_list and isinstance(data, dict):
                    # Try to find any list in the data
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            # Check if first item looks like flight data
                            if isinstance(value[0], dict):
                                # Check if it has flight-like keys
                                first_item = value[0]
                                if any(k in first_item for k in ['flightNumber', 'flight_number', 'departureTime', 'departure_time', 'price', 'fare']):
                                    flight_list = value
                                    break
                
                # If still not found, check nested dicts
                if not flight_list:
                    for key, value in data.items():
                        if isinstance(value, dict):
                            # Recursively search in nested dict
                            nested_flights = self._parse_api_response(value)
                            if nested_flights:
                                flights.extend(nested_flights)
                
                if flight_list:
                    if isinstance(flight_list, list):
                        print(f"Found flight list with {len(flight_list)} items")
                        for idx, flight_item in enumerate(flight_list[:5]):  # Debug first 5
                            if isinstance(flight_item, dict):
                                print(f"  Item {idx} keys: {list(flight_item.keys())[:10]}")
                            flight = self._extract_flight_from_item(flight_item)
                            if flight:
                                flights.append(flight)
                        # Process remaining items
                        for flight_item in flight_list[5:]:
                            flight = self._extract_flight_from_item(flight_item)
                            if flight:
                                flights.append(flight)
                    elif isinstance(flight_list, dict):
                        # If it's a dict, try to extract flights from it
                        flight = self._extract_flight_from_item(flight_list)
                        if flight:
                            flights.append(flight)
            
            elif isinstance(data, list):
                # Data is directly a list of flights
                print(f"Data is a list with {len(data)} items")
                for flight_item in data:
                    flight = self._extract_flight_from_item(flight_item)
                    if flight:
                        flights.append(flight)
            
            # SpiceJet specific parsing - check for 'data' -> 'trips' -> 'journeysAvailable'
            if not flights and isinstance(data, dict) and 'data' in data:
                data_content = data['data']
                if isinstance(data_content, dict) and 'trips' in data_content:
                    trips = data_content['trips']
                    if isinstance(trips, list) and len(trips) > 0:
                        print(f"Found flight data dict with keys: {list(data_content.keys())}")
                        print(f"  Processing {len(trips)} trip(s)")
                        for trip_idx, trip in enumerate(trips):
                            print(f"    Trip {trip_idx} keys: {list(trip.keys())}")
                            if 'journeysAvailable' in trip and isinstance(trip['journeysAvailable'], list):
                                print(f"      Found {len(trip['journeysAvailable'])} item(s) in 'journeysAvailable'")
                                for journey_idx, journey in enumerate(trip['journeysAvailable']):
                                    print(f"        Item {journey_idx} keys: {list(journey.keys())}")
                                    flight = self._extract_flight_from_item(journey)
                                    if flight:
                                        flights.append(flight)
                            else:
                                print(f"      No 'journeysAvailable' found in trip {trip_idx}")
                    else:
                        print("No 'trips' list found in data content.")
                else:
                    print("No 'data' dict found in API response.")
            
        except Exception as e:
            print(f"Error parsing API response: {e}")
            import traceback
            traceback.print_exc()
        
        return flights
    
    def _extract_flight_from_item(self, item):
        """Extract flight information from a single item in API response"""
        if not isinstance(item, dict):
            return None
        
        flight = {
            'airline': 'SpiceJet',
            'flight_number': 'N/A',
            'departure_time': 'N/A',
            'arrival_time': 'N/A',
            'duration': 'N/A',
            'price_inr': 'N/A',
            'award_points': 'N/A'
        }
        
        try:
            # Try to extract flight number
            flight_num_keys = ['flightNumber', 'flight_number', 'flightNo', 'flight_no', 'carrierString', 'carrier_string']
            for key in flight_num_keys:
                if key in item:
                    flight_val = str(item[key]).strip()
                    if flight_val and flight_val != 'N/A':
                        flight['flight_number'] = flight_val
                        break
            
            # If not found, try segments
            if flight['flight_number'] == 'N/A' and 'segments' in item:
                segments = item['segments']
                if isinstance(segments, list) and len(segments) > 0:
                    first_segment = segments[0]
                    if isinstance(first_segment, dict):
                        if 'identifier' in first_segment:
                            identifier = first_segment['identifier']
                            if isinstance(identifier, dict):
                                carrier_code = identifier.get('carrierCode', '')
                                flight_id = identifier.get('identifier', '')
                                if carrier_code and flight_id:
                                    flight['flight_number'] = f"{carrier_code} {flight_id}"
                                elif flight_id:
                                    flight['flight_number'] = flight_id
            
            # Fallback to carrierString
            if flight['flight_number'] == 'N/A' and 'carrierString' in item:
                carrier_string = str(item['carrierString']).strip()
                flight['flight_number'] = carrier_string
            
            # Fallback to designator (if it's a string, not dict)
            if flight['flight_number'] == 'N/A' and 'designator' in item:
                designator = item['designator']
                if isinstance(designator, str):
                    flight['flight_number'] = designator.strip()
            
            # Try to extract departure time
            dep_keys = ['departureTime', 'departure_time', 'depTime', 'dep_time', 'departure', 'dep', 'std', 'scheduledDepartureTime']
            for key in dep_keys:
                if key in item:
                    time_val = str(item[key]).strip()
                    flight['departure_time'] = self._format_time(time_val)
                    break
            
            # If not found, check segments
            if flight['departure_time'] == 'N/A' and 'segments' in item:
                segments = item['segments']
                if isinstance(segments, list) and len(segments) > 0:
                    first_seg = segments[0]
                    if isinstance(first_seg, dict):
                        for key in dep_keys:
                            if key in first_seg:
                                time_val = str(first_seg[key]).strip()
                                flight['departure_time'] = self._format_time(time_val)
                                break
            
            # Try to extract arrival time
            arr_keys = ['arrivalTime', 'arrival_time', 'arrTime', 'arr_time', 'arrival', 'arr', 'sta', 'scheduledArrivalTime']
            for key in arr_keys:
                if key in item:
                    time_val = str(item[key]).strip()
                    flight['arrival_time'] = self._format_time(time_val)
                    break
            
            # If not found, check segments (last segment for arrival)
            if flight['arrival_time'] == 'N/A' and 'segments' in item:
                segments = item['segments']
                if isinstance(segments, list) and len(segments) > 0:
                    last_seg = segments[-1]
                    if isinstance(last_seg, dict):
                        for key in arr_keys:
                            if key in last_seg:
                                time_val = str(last_seg[key]).strip()
                                flight['arrival_time'] = self._format_time(time_val)
                                break
            
            # Try to extract duration
            dur_keys = ['flightDuration', 'duration', 'flight_duration', 'time', 'journeyTime', 'flightTime']
            for key in dur_keys:
                if key in item:
                    dur_val = str(item[key]).strip()
                    flight['duration'] = self._format_duration(dur_val)
                    break
            
            # Calculate duration from times if not found
            if flight['duration'] == 'N/A' and flight['departure_time'] != 'N/A' and flight['arrival_time'] != 'N/A':
                try:
                    dep_parts = flight['departure_time'].split(':')
                    arr_parts = flight['arrival_time'].split(':')
                    if len(dep_parts) == 2 and len(arr_parts) == 2:
                        dep_mins = int(dep_parts[0]) * 60 + int(dep_parts[1])
                        arr_mins = int(arr_parts[0]) * 60 + int(arr_parts[1])
                        if arr_mins < dep_mins:  # Next day
                            arr_mins += 24 * 60
                        duration_mins = arr_mins - dep_mins
                        hours = duration_mins // 60
                        minutes = duration_mins % 60
                        flight['duration'] = f"{hours}h {minutes}m"
                except:
                    pass
            
            # Try to extract price - SpiceJet has 'fares' as dict
            # Note: SpiceJet fares structure is complex, prices might need separate API call
            # For now, we'll try to get the lowest fare code or check if price is in the response
            if 'fares' in item:
                fares = item['fares']
                if isinstance(fares, dict):
                    # Fares is a dict with fare codes as keys
                    # We need to find the actual price - might need to check faresAvailable in parent
                    # For now, mark as available but price needs separate lookup
                    fare_codes = list(fares.keys())
                    if fare_codes:
                        # At least one fare is available
                        flight['price_inr'] = 'Check website'  # Placeholder
                elif isinstance(fares, list) and len(fares) > 0:
                    # If it's a list, get first fare
                    fare = fares[0]
                    if isinstance(fare, dict):
                        price_keys = ['totalFare', 'baseFare', 'fare', 'price', 'amount', 'adultFare']
                        for key in price_keys:
                            if key in fare:
                                price_val = fare[key]
                                if isinstance(price_val, (int, float)):
                                    flight['price_inr'] = f"₹{int(price_val):,}"
                                    break
                                elif isinstance(price_val, str):
                                    price_num = re.sub(r'[₹Rs,.\s]', '', price_val)
                                    if price_num.isdigit():
                                        flight['price_inr'] = f"₹{int(price_num):,}"
                                        break
            
            # Fallback to direct price keys
            if flight['price_inr'] == 'N/A':
                price_keys = ['totalFare', 'baseFare', 'fare', 'price', 'amount', 'adultFare', 'totalPrice', 'total_price']
                for key in price_keys:
                    if key in item:
                        price_val = item[key]
                        if isinstance(price_val, (int, float)):
                            flight['price_inr'] = f"₹{int(price_val):,}"
                            break
                        elif isinstance(price_val, str):
                            price_num = re.sub(r'[₹Rs,.\s]', '', price_val)
                            if price_num.isdigit():
                                flight['price_inr'] = f"₹{int(price_num):,}"
                                break
            
        except Exception as e:
            print(f"Error extracting flight from item: {e}")
            return None
        
        return flight if flight['flight_number'] != 'N/A' else None
    
    def _format_time(self, time_str):
        """Format time string to HH:MM format"""
        try:
            # If it's already in HH:MM format
            if re.match(r'^\d{1,2}:\d{2}$', time_str):
                return time_str
            
            # If it's a datetime string
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return dt.strftime('%H:%M')
            
            # Try to parse as datetime
            dt = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
            return dt.strftime('%H:%M')
        except:
            pass
        return time_str
    
    def _format_duration(self, dur_str):
        """Format duration string"""
        try:
            # Already formatted (e.g., "2h 30m")
            if 'h' in dur_str.lower() or 'hr' in dur_str.lower():
                return dur_str
            # Minutes only
            elif dur_str.isdigit():
                mins = int(dur_str)
                hours = mins // 60
                minutes = mins % 60
                return f"{hours}h {minutes}m"
        except:
            pass
        return dur_str
    
    def _parse_html(self):
        """Parse flight data from HTML to get prices and points for all fare types"""
        flights = []
        
        try:
            print("Parsing HTML for prices and points...")
            
            # Wait a bit more for page to fully render and prices to load
            time.sleep(5)
            
            # Scroll page to load all content
            try:
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
                self.page.evaluate("window.scrollTo(0, 0)")
                time.sleep(3)
            except:
                pass
            
            # Wait for fare bundles to be visible
            try:
                self.page.wait_for_selector("#fare-bundle-val, [id='fare-bundle-val']", timeout=10000)
                time.sleep(2)
            except:
                pass
            
            # Get full page text to search for fare types
            try:
                body = self.page.query_selector("body")
                page_text = body.inner_text() if body else ""
            except:
                page_text = ""
            
            # Find flight containers more precisely
            # Strategy 1: Find by fare-bundle-val (each flight has this)
            fare_bundles = self.page.query_selector_all("#fare-bundle-val, [id='fare-bundle-val']")
            print(f"Found {len(fare_bundles)} fare bundle(s)")
            
            containers_to_check = []
            
            # Process each fare bundle - each one represents one flight
            for bundle in fare_bundles:
                try:
                    # Verify this bundle has a flight number nearby
                    has_aircraft_no = bundle.evaluate("""
                        el => {
                            let current = el;
                            for (let i = 0; i < 20 && current; i++) {
                                let aircraftNo = current.querySelector('#aircraft-no');
                                if (aircraftNo) {
                                    return true;
                                }
                                current = current.parentElement;
                            }
                            return false;
                        }
                    """)
                    if has_aircraft_no:
                        containers_to_check.append(bundle)
                except:
                    pass
            
            # Strategy 2: If no fare bundles found, use flight number elements
            if not containers_to_check:
                flight_number_elems = self.page.query_selector_all("#aircraft-no, [id='aircraft-no']")
                print(f"Found {len(flight_number_elems)} flight number element(s)")
                for elem in flight_number_elems:
                    containers_to_check.append(elem)
            
            # Strategy 3: Fallback - find containers with both flight number and prices
            if not containers_to_check:
                all_divs = self.page.query_selector_all("div")
                for div in all_divs:
                    try:
                        text = div.inner_text() if hasattr(div, 'inner_text') else div.text_content()
                        if text and re.search(r'SG\s*\d{3,}', text, re.IGNORECASE) and re.search(r'₹\s*[\d,]+', text):
                            containers_to_check.append(div)
                            if len(containers_to_check) >= 20:  # Limit to avoid too many
                                break
                    except:
                        continue
            
            print(f"Checking {len(containers_to_check)} container(s) for flight data")
            seen_flights = set()
            
            for container in containers_to_check:
                try:
                    # Get the flight container that contains both aircraft-no and this fare bundle
                    flight_container_data = container.evaluate("""
                        el => {
                            // Find the parent container that has both aircraft-no and this fare bundle
                            let current = el;
                            for (let i = 0; i < 20 && current; i++) {
                                let aircraftNo = current.querySelector('#aircraft-no');
                                if (aircraftNo) {
                                    // Found the flight container
                                    return {
                                        text: current.innerText || '',
                                        aircraftNo: aircraftNo.innerText || aircraftNo.textContent || ''
                                    };
                                }
                                current = current.parentElement;
                            }
                            return {text: '', aircraftNo: ''};
                        }
                    """)
                    
                    text = flight_container_data.get('text', '') if flight_container_data else ''
                    aircraft_no_text = flight_container_data.get('aircraftNo', '').strip() if flight_container_data else ''
                    
                    if not text:
                        # Fallback
                        try:
                            text = container.inner_text() if hasattr(container, 'inner_text') else container.text_content()
                        except:
                            text = ''
                    
                    if not text or len(text) < 30:
                        continue
                    
                    # Get flight number - use the one we extracted above, or search
                    flight_num = aircraft_no_text if aircraft_no_text else 'N/A'
                    
                    # Fallback: Look for flight number pattern (SG + numbers, can be multiple for connecting)
                    if flight_num == 'N/A' or not flight_num:
                        # Try connecting flight pattern first
                        connecting_match = re.search(r'(SG|UK)\s*(\d{3,})\s*,\s*(SG|UK)\s*(\d{3,})', text, re.IGNORECASE)
                        if connecting_match:
                            flight_num = f"{connecting_match.group(1)} {connecting_match.group(2)}, {connecting_match.group(3)} {connecting_match.group(4)}"
                        else:
                            # Direct flight
                            flight_match = re.search(r'(SG|UK)\s*(\d{3,})', text, re.IGNORECASE)
                            if flight_match:
                                flight_num = f"{flight_match.group(1)} {flight_match.group(2)}"
                    
                    if not flight_num or flight_num == 'N/A':
                        continue
                    
                    # Extract times to create unique key
                    # Look for time pattern in format HH:MM
                    times = re.findall(r'\b(\d{1,2}):(\d{2})\b', text)
                    dep_time = f"{times[0][0]}:{times[0][1]}" if len(times) >= 1 else 'N/A'
                    # For arrival, check if there's a +1 (next day indicator)
                    arr_time = f"{times[1][0]}:{times[1][1]}" if len(times) >= 2 else 'N/A'
                    
                    # Also try to get times from the page structure directly
                    try:
                        time_elements = container.query_selector_all("*")
                        for elem in time_elements:
                            elem_text = elem.inner_text() if hasattr(elem, 'inner_text') else elem.text_content()
                            # Look for departure time (first time in the flight card)
                            if dep_time == 'N/A' and re.match(r'^\d{1,2}:\d{2}$', elem_text.strip()):
                                dep_time = elem_text.strip()
                            # Look for arrival time (second time, might have +1)
                            elif arr_time == 'N/A' and re.match(r'^\d{1,2}:\d{2}', elem_text.strip()):
                                arr_time = re.search(r'(\d{1,2}:\d{2})', elem_text.strip()).group(1)
                    except:
                        pass
                    
                    # Create unique key to avoid duplicates (use flight number + times)
                    # Use full flight number and times to create unique key
                    unique_key = f"{flight_num}_{dep_time}_{arr_time}"
                    if unique_key in seen_flights:
                        continue
                    
                    # Only process containers that have prices
                    if not re.search(r'₹\s*[\d,]+', text):
                        continue
                    
                    seen_flights.add(unique_key)
                    
                    flight = {
                        'airline': 'SpiceJet',
                        'flight_number': flight_num,
                        'departure_time': 'N/A',
                        'arrival_time': 'N/A',
                        'duration': 'N/A',
                        'price_inr': 'N/A',
                        'award_points': 'N/A',
                        'spicesaver_price': 'N/A',
                        'spiceflex_price': 'N/A',
                        'spicemax_price': 'N/A',
                        'spicesaver_points': 'N/A',
                        'spiceflex_points': 'N/A',
                        'spicemax_points': 'N/A'
                    }
                    
                    # Extract times - get from the flight container directly, not from text
                    try:
                        # Find time elements in the flight container
                        time_elements = container.query_selector_all("*")
                        times_found = []
                        for elem in time_elements:
                            try:
                                elem_text = elem.inner_text() if hasattr(elem, 'inner_text') else elem.text_content()
                                # Look for time pattern HH:MM
                                time_match = re.match(r'^(\d{1,2}):(\d{2})$', elem_text.strip())
                                if time_match:
                                    time_str = f"{time_match.group(1)}:{time_match.group(2)}"
                                    if time_str not in times_found:
                                        times_found.append(time_str)
                            except:
                                continue
                        
                        # Use first two times found as departure and arrival
                        if len(times_found) >= 2:
                            flight['departure_time'] = times_found[0]
                            flight['arrival_time'] = times_found[1]
                        elif len(times_found) >= 1:
                            flight['departure_time'] = times_found[0]
                    except:
                        # Fallback to regex from text
                        times = re.findall(r'\b(\d{1,2}):(\d{2})\b', text)
                        if len(times) >= 2:
                            flight['departure_time'] = f"{times[0][0]}:{times[0][1]}"
                            flight['arrival_time'] = f"{times[1][0]}:{times[1][1]}"
                    
                    # Extract duration
                    dur_match = re.search(r'(\d+)\s*h\s*(\d+)\s*m', text, re.IGNORECASE)
                    if dur_match:
                        flight['duration'] = f"{dur_match.group(1)}h {dur_match.group(2)}m"
                    
                    # Extract prices and points using data-testid attributes
                    # Based on HTML: data-testid="spicesaver-flight-select-radio-button-0"
                    fare_configs = [
                        ('spicesaver', 'spicesaver-flight-select-radio-button-0'),
                        ('spiceflex', 'spiceflex-flight-select-radio-button-1'),
                        ('spicemax', 'spicemax-flight-select-radio-button-2')
                    ]
                    
                    # Method 1: Use exact data-testid to find each fare type precisely
                    for fare_key, exact_testid in fare_configs:
                        try:
                            # Find button with exact testid in the container or its parents
                            fare_button = None
                            
                            # Try to find in container first - search all elements with data-testid
                            try:
                                all_buttons = container.query_selector_all("[data-testid]")
                                for btn in all_buttons:
                                    btn_testid = btn.get_attribute('data-testid')
                                    if btn_testid == exact_testid:
                                        fare_button = btn
                                        break
                            except:
                                pass
                            
                            # If not found, search within the same fare bundle only
                            if not fare_button:
                                try:
                                    # Get the fare bundle container for this flight
                                    fare_bundle_container = container.evaluate("""
                                        el => {
                                            let current = el;
                                            for (let i = 0; i < 15 && current; i++) {
                                                if (current.id === 'fare-bundle-val') {
                                                    return current;
                                                }
                                                current = current.parentElement;
                                            }
                                            return null;
                                        }
                                    """)
                                    
                                    if fare_bundle_container:
                                        # Search only within this fare bundle
                                        all_buttons = container.query_selector_all(f"[data-testid]")
                                        for btn in all_buttons:
                                            btn_testid = btn.get_attribute('data-testid')
                                            if btn_testid == exact_testid:
                                                # Verify it's in the same fare bundle
                                                btn_fare_bundle = btn.evaluate("el => el.closest('[id=\"fare-bundle-val\"]')")
                                                if btn_fare_bundle:
                                                    fare_button = btn
                                                    break
                                except:
                                    pass
                            
                            if fare_button:
                                # Get the parent container that has both price and points
                                # Make sure we're getting data from the same fare bundle container
                                fare_data = fare_button.evaluate("""
                                    el => {
                                        // Go up the DOM tree to find container with both price and Earn
                                        // But make sure it's within the same fare-bundle-val container
                                        let fareBundle = el.closest('[id="fare-bundle-val"]');
                                        if (!fareBundle) return {text: '', price: '', points: '', available: false};
                                        
                                        // Check if this fare type is available - look for "N/A" or "Not Available" in the fare button's container
                                        // First, find the price element for this fare type
                                        let fareContainer = el.parentElement;
                                        let isAvailable = true;
                                        
                                        // Look for price element in the fare button's parent containers
                                        for (let i = 0; i < 8 && fareContainer && fareBundle.contains(fareContainer); i++) {
                                            // Find price element in this container
                                            let priceElem = fareContainer.querySelector('[class*="1i10wst"], [id*="selected-onward"]');
                                            if (priceElem) {
                                                let priceText = (priceElem.innerText || '').trim().toLowerCase();
                                                // If price element contains "n/a" or "not available", this fare is not available
                                                if (priceText === 'n/a' || priceText.includes('not available')) {
                                                    isAvailable = false;
                                                    break;
                                                }
                                                // If we found a valid price (contains ₹ or numbers), it's available
                                                if (priceText.includes('₹') || /^\\d/.test(priceText)) {
                                                    isAvailable = true;
                                                    break;
                                                }
                                            }
                                            fareContainer = fareContainer.parentElement;
                                        }
                                        
                                        // Now find the price and points elements for this specific fare type
                                        // Look in the fare button's parent containers within the same fare bundle
                                        let current = el.parentElement;
                                        let priceElem = null;
                                        let pointsElem = null;
                                        
                                        // Search for price and points elements in parent containers
                                        for (let i = 0; i < 10 && current && fareBundle.contains(current); i++) {
                                            // Find price element - look for element with class containing "1i10wst" or id containing "selected-onward"
                                            if (!priceElem) {
                                                priceElem = current.querySelector('[class*="1i10wst"], [id*="selected-onward"]');
                                                if (priceElem) {
                                                    let priceText = (priceElem.innerText || '').trim();
                                                    // Check if price is "N/A" or "Not Available"
                                                    if (priceText.toLowerCase() === 'n/a' || priceText.toLowerCase().includes('not available')) {
                                                        isAvailable = false;
                                                    }
                                                }
                                            }
                                            // Find points element - look for element with class containing "1gkfh8e"
                                            if (!pointsElem) {
                                                pointsElem = current.querySelector('[class*="1gkfh8e"]');
                                            }
                                            
                                            // If we found price element, we can stop searching
                                            if (priceElem) {
                                                break;
                                            }
                                            current = current.parentElement;
                                        }
                                        
                                        // Get text from elements
                                        let priceText = priceElem ? (priceElem.innerText || '').trim() : '';
                                        let pointsText = pointsElem ? (pointsElem.innerText || '').trim() : '';
                                        
                                        // If price is "N/A" or "Not Available", mark as unavailable
                                        if (priceText && (priceText.toLowerCase() === 'n/a' || priceText.toLowerCase().includes('not available'))) {
                                            isAvailable = false;
                                        }
                                        
                                        // Get container text for fallback
                                        let containerText = el.parentElement ? (el.parentElement.innerText || '') : '';
                                        
                                        return {
                                            text: containerText || priceText || pointsText || '',
                                            price: priceText,
                                            points: pointsText,
                                            available: isAvailable
                                        };
                                    }
                                """)
                                
                                if fare_data:
                                    # Check if this fare type is available
                                    if not fare_data.get('available', True):
                                        # This fare type is not available, skip it
                                        continue
                                    
                                    if fare_data.get('text'):
                                        # Extract price - look for ₹ followed by number
                                        price_text = fare_data.get('price', '').strip()
                                        
                                        # Check if price is "N/A" or "Not Available" - if so, skip this fare type
                                        if price_text.lower() == 'n/a' or 'not available' in price_text.lower():
                                            # This fare type is not available, skip it
                                            continue
                                        
                                        if not price_text:
                                            # Fallback to text
                                            price_match = re.search(r'₹\s*([\d,]+)', fare_data['text'])
                                            if price_match:
                                                price = f"₹{price_match.group(1)}"
                                                if flight[f'{fare_key}_price'] == 'N/A':
                                                    flight[f'{fare_key}_price'] = price
                                                if fare_key == 'spicesaver' and flight['price_inr'] == 'N/A':
                                                    flight['price_inr'] = price
                                        else:
                                            # Use direct price element - already checked it's not N/A above
                                            price_match = re.search(r'₹\s*([\d,]+)', price_text)
                                            if not price_match:
                                                price_match = re.search(r'([\d,]+)', price_text)
                                            if price_match:
                                                price = f"₹{price_match.group(1)}"
                                                if flight[f'{fare_key}_price'] == 'N/A':
                                                    flight[f'{fare_key}_price'] = price
                                                if fare_key == 'spicesaver' and flight['price_inr'] == 'N/A':
                                                    flight['price_inr'] = price
                                        
                                        # Extract points - look for "Earn" followed by number (1-4 digits)
                                        points_text = fare_data.get('points', '')
                                        if not points_text:
                                            # Fallback to text
                                            points_match = re.search(r'Earn\s*(\d{1,4}(?:,\d{3})*)', fare_data['text'], re.IGNORECASE)
                                            if points_match:
                                                points_value = points_match.group(1).replace(',', '')
                                                if flight[f'{fare_key}_points'] == 'N/A':
                                                    flight[f'{fare_key}_points'] = points_value
                                        else:
                                            # Use direct points element
                                            points_match = re.search(r'Earn\s*(\d{1,4}(?:,\d{3})*)', points_text, re.IGNORECASE)
                                            if points_match:
                                                points_value = points_match.group(1).replace(',', '')
                                                if flight[f'{fare_key}_points'] == 'N/A':
                                                    flight[f'{fare_key}_points'] = points_value
                        except Exception as e:
                            pass
                    
                    # Method 2: Fallback - extract all prices and points from container text
                    # Only use this if data-testid method didn't find all prices
                    if flight['spicesaver_price'] == 'N/A' or flight['spiceflex_price'] == 'N/A' or flight['spicemax_price'] == 'N/A':
                        # Find all prices in the container, but be smarter about it
                        # Look for prices that are near fare type labels
                        fare_type_patterns = {
                            'spicesaver': r'(?:spicesaver|saver).*?₹\s*([\d,]+)',
                            'spiceflex': r'(?:spiceflex|flex).*?₹\s*([\d,]+)',
                            'spicemax': r'(?:spicemax|max).*?₹\s*([\d,]+)'
                        }
                        
                        for fare_key, pattern in fare_type_patterns.items():
                            if flight[f'{fare_key}_price'] == 'N/A':
                                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                                if match:
                                    flight[f'{fare_key}_price'] = f"₹{match.group(1)}"
                                    if fare_key == 'spicesaver' and flight['price_inr'] == 'N/A':
                                        flight['price_inr'] = f"₹{match.group(1)}"
                        
                        # If still missing, try to find all prices in order
                        if flight['spicesaver_price'] == 'N/A':
                            all_prices = re.findall(r'₹\s*([\d,]+)', text)
                            # Remove duplicates while preserving order
                            unique_prices = []
                            seen_prices = set()
                            for p in all_prices:
                                if p not in seen_prices:
                                    seen_prices.add(p)
                                    unique_prices.append(p)
                            
                            # Assign prices in order (usually Saver, Flex, Max)
                            if len(unique_prices) >= 3:
                                if flight['spicesaver_price'] == 'N/A':
                                    flight['spicesaver_price'] = f"₹{unique_prices[0]}"
                                if flight['spiceflex_price'] == 'N/A':
                                    flight['spiceflex_price'] = f"₹{unique_prices[1]}"
                                if flight['spicemax_price'] == 'N/A':
                                    flight['spicemax_price'] = f"₹{unique_prices[2]}"
                                if flight['price_inr'] == 'N/A':
                                    flight['price_inr'] = f"₹{unique_prices[0]}"
                            elif len(unique_prices) >= 1:
                                if flight['spicesaver_price'] == 'N/A':
                                    flight['spicesaver_price'] = f"₹{unique_prices[0]}"
                                if flight['price_inr'] == 'N/A':
                                    flight['price_inr'] = f"₹{unique_prices[0]}"
                    
                    # Extract points using "Earn" pattern - similar approach
                    if flight['spicesaver_points'] == 'N/A' or flight['spiceflex_points'] == 'N/A' or flight['spicemax_points'] == 'N/A':
                        # Look for points near fare type labels
                        fare_point_patterns = {
                            'spicesaver': r'(?:spicesaver|saver).*?Earn\s*(\d{1,4}(?:,\d{3})*)',
                            'spiceflex': r'(?:spiceflex|flex).*?Earn\s*(\d{1,4}(?:,\d{3})*)',
                            'spicemax': r'(?:spicemax|max).*?Earn\s*(\d{1,4}(?:,\d{3})*)'
                        }
                        
                        for fare_key, pattern in fare_point_patterns.items():
                            if flight[f'{fare_key}_points'] == 'N/A':
                                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                                if match:
                                    flight[f'{fare_key}_points'] = match.group(1)
                        
                        # If still missing, find all points in order
                        if flight['spicesaver_points'] == 'N/A':
                            all_earn_points = re.findall(r'Earn\s*(\d{1,4}(?:,\d{3})*)', text, re.IGNORECASE)
                            # Remove commas from points
                            all_earn_points = [p.replace(',', '') for p in all_earn_points]
                            # Remove duplicates while preserving order
                            unique_points = []
                            seen_points = set()
                            for p in all_earn_points:
                                if p not in seen_points:
                                    seen_points.add(p)
                                    unique_points.append(p)
                            
                            # Assign points in order (usually Saver, Flex, Max)
                            if len(unique_points) >= 3:
                                if flight['spicesaver_points'] == 'N/A':
                                    flight['spicesaver_points'] = unique_points[0]
                                if flight['spiceflex_points'] == 'N/A':
                                    flight['spiceflex_points'] = unique_points[1]
                                if flight['spicemax_points'] == 'N/A':
                                    flight['spicemax_points'] = unique_points[2]
                            elif len(unique_points) >= 1:
                                if flight['spicesaver_points'] == 'N/A':
                                    flight['spicesaver_points'] = unique_points[0]
                    
                    # Only add flight if it has at least a price or is a valid flight
                    if flight['spicesaver_price'] != 'N/A' or flight['spiceflex_price'] != 'N/A' or flight['spicemax_price'] != 'N/A' or flight['departure_time'] != 'N/A':
                        flights.append(flight)
                        print(f"  Extracted: {flight_num} | Saver: {flight['spicesaver_price']}, Flex: {flight['spiceflex_price']}, Max: {flight['spicemax_price']}")
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            import traceback
            traceback.print_exc()
        
        return flights
    
    def scrape_flights(self, origin, destination, date):
        """Main method to scrape flights"""
        try:
            # Setup driver
            if not self.setup_driver():
                return []
            
            # Load search page
            if not self.load_search_page(origin, destination, date):
                return []
            
            # Extract flight data
            flights = self.extract_flights_from_data()
            
            return flights
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self.close()


def main():
    """Main function to run the scraper"""
    print("=" * 60)
    print("SpiceJet International Flight Scraper (Network Interception)")
    print("=" * 60)
    print()
    
    # Get user input
    if len(sys.argv) >= 4:
        origin_input = sys.argv[1]
        destination_input = sys.argv[2]
        date_input = sys.argv[3]
    else:
        origin_input = input("Enter origin city or code (e.g., Delhi or DEL): ").strip()
        destination_input = input("Enter destination city or code (e.g., Dubai or DXB): ").strip()
        date_input = input("Enter departure date (DD-MM-YYYY or YYYY-MM-DD): ").strip()
    
    # Normalize inputs
    origin = normalize_city_input(origin_input)
    destination = normalize_city_input(destination_input)
    date = parse_date(date_input)
    
    # Validate inputs
    if not origin:
        print(f"Error: Invalid origin '{origin_input}'. Please enter a valid city name or airport code.")
        return
    
    if not destination:
        print(f"Error: Invalid destination '{destination_input}'. Please enter a valid city name or airport code.")
        return
    
    if not date:
        print(f"Error: Invalid date '{date_input}'. Please enter date in DD-MM-YYYY or YYYY-MM-DD format.")
        return
    
    print(f"\nSearching for international flights: {origin} -> {destination} on {date}\n")
    
    # Create scraper and scrape
    scraper = SpiceJetScraper()
    flights = scraper.scrape_flights(origin, destination, date)
    
    # Display results
    print("\n" + "=" * 60)
    print("FLIGHT RESULTS")
    print("=" * 60)
    print()
    
    if flights:
        print(format_flight_data(flights))
    else:
        print("No flights found. This could be due to:")
        print("1. No flights available for the selected route/date")
        print("2. API structure has changed")
        print("3. Network interception didn't capture the data")
        print("\nTip: The scraper will try to extract data from HTML as fallback.")
    
    print(f"\nTotal flights found: {len(flights)}")


if __name__ == "__main__":
    main()

