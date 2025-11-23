"""
Etihad Airways Flight Scraper
Uses undetected-chromedriver for stealth browsing and network interception
Works for international routes
"""

import time
import sys
import json
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import config
from utils import normalize_city_input, parse_date, format_date_for_etihad, format_flight_data


class EtihadScraper:
    """Scraper class for Etihad Airways flight data using undetected-chromedriver"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.flight_data = None
        self.all_responses = []
    
    def setup_driver(self):
        """Initialize and configure Chrome WebDriver using undetected-chromedriver"""
        try:
            print("Setting up Chrome WebDriver with undetected-chromedriver...")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Clean up any previous driver instance
                    if hasattr(self, 'driver') and self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                    
                    # Create NEW options object for each attempt
                    options = uc.ChromeOptions()
                    
                    # Show browser for testing
                    if not config.HEADLESS_MODE:
                        options.add_argument('--start-maximized')
                    
                    # Set user agent
                    options.add_argument(f'user-agent={config.USER_AGENT}')
                    
                    # Stealth options
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    
                    # Initialize driver
                    self.driver = uc.Chrome(options=options, version_main=None, keep_alive=True)
                    
                    # Minimize the window IMMEDIATELY to not disturb user
                    try:
                        self.driver.minimize_window()
                        print("Browser opened and minimized instantly!")
                    except:
                        # If minimize fails, try alternative method (move off-screen)
                        try:
                            self.driver.set_window_position(-2000, -2000)
                            print("Browser opened and moved off-screen instantly!")
                        except:
                            pass
                    
                    # Give browser a moment to fully start (after minimizing)
                    time.sleep(1)
                    
                    # Verify browser is actually open
                    handles = self.driver.window_handles
                    if len(handles) > 0:
                        print(f"Browser initialized successfully with {len(handles)} window(s)!")
                        break
                    else:
                        raise Exception("Browser window not found after initialization")
                        
                except Exception as init_error:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed: {init_error}")
                        print("Retrying browser initialization...")
                        time.sleep(3)
                    else:
                        raise Exception(f"Failed to open browser after {max_retries} attempts: {init_error}")
            
            # Set up waits
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            self.wait = WebDriverWait(self.driver, config.EXPLICIT_WAIT_TIMEOUT)
            
            # Give browser additional time to fully initialize
            time.sleep(2)
            
            # Keep browser alive
            try:
                _ = self.driver.window_handles
            except:
                pass
            
            print("Chrome WebDriver initialized successfully!")
            return True
        except Exception as e:
            print(f"Error setting up ChromeDriver: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """Close the browser driver and save captured responses"""
        try:
            # Save all responses for analysis
            if self.all_responses:
                try:
                    with open('etihad_all_responses.json', 'w', encoding='utf-8') as f:
                        json.dump(self.all_responses, f, indent=2, ensure_ascii=False)
                    print(f"\n  Saved {len(self.all_responses)} total API responses to etihad_all_responses.json")
                except:
                    pass
            
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    try:
                        self.driver.close()
                    except:
                        pass
        except:
            pass
    
    def build_search_url(self, origin, destination, date):
        """Build Etihad search URL with parameters"""
        # Format: https://digital.etihad.com/book/search?LANGUAGE=EN&CHANNEL=DESKTOP&B_LOCATION=CCU&E_LOCATION=AUH&TRIP_TYPE=O&CABIN=E&TRAVELERS=ADT&TRIP_FLOW_TYPE=AVAILABILITY&...&DATE_1=202511300000
        
        # Convert date to Etihad format (YYYYMMDD0000)
        etihad_date = format_date_for_etihad(date)
        if not etihad_date:
            return None
        
        # Build URL with Etihad's parameter structure
        url = (
            f"{config.ETIHAD_SEARCH_URL}?"
            f"LANGUAGE=EN&"
            f"CHANNEL=DESKTOP&"
            f"B_LOCATION={origin}&"
            f"E_LOCATION={destination}&"
            f"TRIP_TYPE=O&"  # O = One-way
            f"CABIN=E&"  # E = Economy
            f"TRAVELERS=ADT&"  # ADT = Adult
            f"TRIP_FLOW_TYPE=AVAILABILITY&"
            f"WDS_ENABLE_STOPOVER_HOTEL_BOOKING=TRUE&"
            f"WDS_ENABLE_HOTEL_STPF=TRUE&"
            f"SITE_EDITION=EN-IN&"
            f"WDS_ENABLE_UPLIFT=TRUE&"
            f"WDS_ENABLE_FLAGSHIP=TRUE&"
            f"WDS_ELIGIBLE_FLAGSHIP_LIST=A380-800&"
            f"WDS_ENABLE_KOREAN_AMOP=TRUE&"
            f"DATE_1={etihad_date}&"
            f"FLOW=REVENUE&"
            f"WDS_MAX_FLIGHTS_ISDIRECT=TRUE"
        )
        return url
    
    def intercept_network_requests(self):
        """Set up network request interception using Chrome DevTools Protocol"""
        try:
            # Enable Network domain
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            # Set up request interception
            def handle_response(response):
                try:
                    url = response.get('response', {}).get('url', '')
                    status = response.get('response', {}).get('status', 0)
                    
                    if status == 200 and url:
                        # Check if it's a JSON response
                        content_type = response.get('response', {}).get('headers', {}).get('content-type', '')
                        if 'json' in content_type.lower() or 'etihad' in url.lower():
                            # Get response body
                            try:
                                request_id = response.get('requestId')
                                if request_id:
                                    # Get response body
                                    body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                    if body and 'body' in body:
                                        try:
                                            data = json.loads(body['body'])
                                            self.all_responses.append({'url': url, 'data': data})
                                            
                                            # Look for flight data
                                            if any(keyword in url.lower() for keyword in ['search', 'availability', 'flight', 'booking', 'offer', 'fare']):
                                                if not self.flight_data:
                                                    self.flight_data = data
                                                    print(f"✓ Captured flight data from: {url}")
                                                    try:
                                                        with open('etihad_api_response.json', 'w', encoding='utf-8') as f:
                                                            json.dump(data, f, indent=2, ensure_ascii=False)
                                                        print("  Saved API response to etihad_api_response.json")
                                                    except:
                                                        pass
                                        except:
                                            pass
                            except:
                                pass
                except:
                    pass
            
            # Note: CDP response interception is complex, so we'll use a simpler approach
            # by checking page source and network logs after page load
            return True
        except Exception as e:
            print(f"Note: Network interception setup failed: {e}")
            print("Will use HTML parsing instead")
            return False
    
    def load_search_page(self, origin, destination, date, retry_count=0):
        """Load Etihad search page and wait for redirect and API calls"""
        try:
            url = self.build_search_url(origin, destination, date)
            if not url:
                print("Error: Could not build search URL")
                return False
            
            print(f"Loading Etihad search page: {origin} -> {destination} on {date}")
            print(f"URL: {url}")
            
            # Check if driver is still valid
            try:
                handles = self.driver.window_handles
                if len(handles) == 0:
                    raise Exception("Browser window is closed")
            except Exception as e:
                print(f"Browser window appears to be closed: {e}")
                if not self.setup_driver():
                    return False
            
            # Strategy: Visit homepage first to get cookies and establish session
            try:
                print("  Step 1: Visiting Etihad homepage to establish session...")
                self.driver.get(config.ETIHAD_BASE_URL)
                time.sleep(5)  # Wait for page to fully load
                
                # Wait a bit more for any security checks
                time.sleep(3)
                
                print("  Step 2: Navigating to search page...")
                # Now navigate to the search URL (it will redirect automatically)
                self.driver.get(url)
                
                # Wait for page to load
                time.sleep(5)
                
                # Check if we got blocked
                page_source = self.driver.page_source
                if "error code 15" in page_source.lower() or "security system" in page_source.lower() or "flown away" in page_source.lower():
                    print("  ⚠ Security system blocked the request!")
                    print("  This might be due to:")
                    print("    - IP-based blocking")
                    print("    - Browser fingerprint detection")
                    print("    - Missing cookies/session")
                    # Save page for debugging
                    try:
                        with open('etihad_blocked_page.html', 'w', encoding='utf-8') as f:
                            f.write(page_source)
                        print("  Saved blocked page to etihad_blocked_page.html")
                    except:
                        pass
                    return False
                
                # Check final URL after redirect
                final_url = self.driver.current_url
                if final_url != url:
                    print(f"  Page redirected to: {final_url}")
                
                # Wait for API calls and page to fully load
                print("  Waiting for page to fully load and API calls...")
                time.sleep(config.AFTER_SEARCH_DELAY)
                
                # Try to wait for specific elements that indicate page loaded
                try:
                    # Wait for any flight-related elements or page load indicators
                    self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                except:
                    pass
                
                # Additional wait for any delayed API calls
                time.sleep(5)
                
                # Try to extract JSON data from page scripts
                try:
                    json_data = self.driver.execute_script("""
                        // Look for JSON data in window objects or script tags
                        var data = {};
                        // Check common places for flight data
                        if (window.__INITIAL_STATE__) data.__INITIAL_STATE__ = window.__INITIAL_STATE__;
                        if (window.__APOLLO_STATE__) data.__APOLLO_STATE__ = window.__APOLLO_STATE__;
                        if (window.flightData) data.flightData = window.flightData;
                        if (window.availabilityData) data.availabilityData = window.availabilityData;
                        if (window.searchResults) data.searchResults = window.searchResults;
                        
                        // Also try to get flight info from DOM
                        var flightInfo = {};
                        var flightNumbers = [];
                        var times = [];
                        var prices = [];
                        
                        // Get flight numbers
                        var flightElems = document.querySelectorAll('[class*="flight"], [id*="flight"]');
                        flightElems.forEach(function(elem) {
                            var text = elem.innerText || '';
                            var match = text.match(/EY\\s*(\\d{3,4})/i);
                            if (match && flightNumbers.indexOf(match[0]) === -1) {
                                flightNumbers.push(match[0]);
                            }
                        });
                        flightInfo.flightNumbers = flightNumbers;
                        
                        // Get times (HH:MM format)
                        var timeElems = document.querySelectorAll('*');
                        timeElems.forEach(function(elem) {
                            var text = elem.innerText || '';
                            var match = text.match(/\\b(\\d{1,2}):(\\d{2})\\b/);
                            if (match) {
                                var time = match[0];
                                if (times.indexOf(time) === -1 && times.length < 10) {
                                    times.push(time);
                                }
                            }
                        });
                        flightInfo.times = times;
                        
                        data.flightInfo = flightInfo;
                        
                        return Object.keys(data).length > 0 ? data : null;
                    """)
                    if json_data:
                        print("  Found JSON data in window object")
                        self.flight_data = json_data
                        try:
                            with open('etihad_api_response.json', 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, indent=2, ensure_ascii=False)
                            print("  Saved window data to etihad_api_response.json")
                        except:
                            pass
                except Exception as e:
                    print(f"  Error extracting window data: {e}")
                
                # Check if we captured API response
                if self.flight_data:
                    print("✓ API response captured")
                    return True
                else:
                    print("⚠ No API response captured yet")
                    # Wait a bit more
                    time.sleep(5)
                    if self.flight_data:
                        print("✓ API response captured after additional wait")
                        return True
                    
                    # If still no data, try to extract from page
                    print("Trying to extract from page HTML...")
                    return True  # Continue to HTML extraction
                    
            except TimeoutException:
                print(f"⚠ Page load timeout. Retry count: {retry_count}")
                if retry_count < 2:
                    time.sleep(5)
                    return self.load_search_page(origin, destination, date, retry_count + 1)
                return False
            except Exception as e:
                print(f"Error loading page: {e}")
                if retry_count < 2:
                    time.sleep(5)
                    return self.load_search_page(origin, destination, date, retry_count + 1)
                return False
                
        except Exception as e:
            print(f"Error in load_search_page: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_api_response(self, data):
        """Parse flight data from Etihad API response"""
        flights = []
        
        try:
            print("Parsing API response...")
            print(f"Data type: {type(data)}")
            
            # We need to discover Etihad's API structure
            # This is a placeholder - will need to be updated based on actual API response
            if isinstance(data, dict):
                print(f"Data keys: {list(data.keys())}")
                # TODO: Parse based on actual Etihad API structure
            elif isinstance(data, list):
                print(f"Data is a list with {len(data)} items")
                # TODO: Parse list structure
            
            # For now, return empty list - will be implemented after testing
            return flights
            
        except Exception as e:
            print(f"Error parsing API response: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_html(self):
        """Parse flight data from HTML (fallback method)"""
        flights = []
        
        try:
            print("Parsing HTML for flight data...")
            
            # Get page source
            page_source = self.driver.page_source
            
            # Save page source for debugging
            try:
                with open('etihad_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print("  Saved page source to etihad_page_source.html")
            except:
                pass
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Check if we're on the right page (not upsell page)
            current_url = self.driver.current_url
            if 'upsell' in current_url.lower():
                print("  ⚠ Currently on upsell page, trying to navigate to results...")
                # Try to find and click "Continue" or skip upsell
                try:
                    # Wait a bit for page to load
                    time.sleep(3)
                    
                    # Try multiple selectors for continue/skip button
                    continue_selectors = [
                        (By.XPATH, "//a[contains(text(), 'Continue')]"),
                        (By.XPATH, "//button[contains(text(), 'Continue')]"),
                        (By.XPATH, "//a[contains(@class, 'continue')]"),
                        (By.XPATH, "//button[contains(@class, 'continue')]"),
                        (By.XPATH, "//a[contains(@class, 'btnPrimary')]"),
                        (By.XPATH, "//a[contains(@class, 'btnSecondary')]"),
                        (By.CSS_SELECTOR, "a.btnPrimary"),
                        (By.CSS_SELECTOR, "button.btnPrimary"),
                        (By.XPATH, "//button[contains(text(), 'Skip')]"),
                        (By.XPATH, "//a[contains(text(), 'Skip')]"),
                    ]
                    continue_btn = None
                    for by, selector in continue_selectors:
                        try:
                            continue_btn = self.driver.find_element(by, selector)
                            if continue_btn and continue_btn.is_displayed():
                                print(f"  Found continue button with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if continue_btn:
                        print("  Clicking continue button...")
                        self.driver.execute_script("arguments[0].click();", continue_btn)
                        time.sleep(10)  # Wait for navigation
                        # Re-parse after navigation
                        page_source = self.driver.page_source
                        soup = BeautifulSoup(page_source, 'lxml')
                        current_url = self.driver.current_url
                        print(f"  Navigated to: {current_url}")
                    else:
                        print("  No continue button found, will try to parse upsell page")
                except Exception as e:
                    print(f"  Could not navigate from upsell page: {e}")
                    print("  Will try to parse current page anyway")
            
            # Look for flight containers - Etihad uses Angular components
            # Common selectors: ey-bound-card-new, ey-fare-card, fare-card
            
            # Method 1: Look for bound cards (flight containers)
            bound_cards = soup.find_all(['ey-bound-card-new', 'ey-bound-card'], limit=20)
            if not bound_cards:
                # Try alternative selectors
                bound_cards = soup.find_all(attrs={'class': re.compile(r'bound|flight|fare', re.I)}, limit=20)
            
            print(f"  Found {len(bound_cards)} potential flight container(s)")
            
            # If no bound cards, try to extract from text patterns
            if not bound_cards:
                # Look for flight numbers in text (EY followed by 3-4 digits)
                flight_numbers = re.findall(r'EY\s*(\d{3,4})', page_source, re.IGNORECASE)
                print(f"  Found {len(set(flight_numbers))} unique flight number(s) in page: {set(flight_numbers)[:5]}")
                
                # Look for times (HH:MM format)
                times = re.findall(r'\b(\d{1,2}):(\d{2})\b', page_source)
                print(f"  Found {len(times)} time pattern(s)")
                
                # Look for prices (various currency formats)
                prices = re.findall(r'[₹$€£]?\s*([\d,]+\.?\d*)', page_source)
                print(f"  Found {len(prices)} price pattern(s)")
                
                # If we found flight numbers, create basic flight entries
                if flight_numbers:
                    for i, flight_num in enumerate(set(flight_numbers)[:10]):  # Limit to 10 flights
                        flight = {
                            'airline': 'Etihad Airways',
                            'flight_number': f"EY {flight_num}",
                            'departure_time': 'N/A',
                            'arrival_time': 'N/A',
                            'duration': 'N/A',
                            'price': 'N/A',
                            'award_points': 'N/A'
                        }
                        flights.append(flight)
            
            # Method 2: Try to find fare cards with prices
            fare_cards = soup.find_all(attrs={'class': re.compile(r'fare-card|price-card', re.I)}, limit=20)
            if fare_cards:
                print(f"  Found {len(fare_cards)} fare card(s)")
                for card in fare_cards:
                    try:
                        # Extract price
                        price_elem = card.find(string=re.compile(r'[₹$€£]\s*[\d,]+'))
                        if price_elem:
                            price_match = re.search(r'[₹$€£]?\s*([\d,]+\.?\d*)', price_elem)
                            if price_match:
                                price = price_match.group(1)
                                # Try to find associated flight info
                                flight = {
                                    'airline': 'Etihad Airways',
                                    'flight_number': 'N/A',
                                    'departure_time': 'N/A',
                                    'arrival_time': 'N/A',
                                    'duration': 'N/A',
                                    'price': f"₹{price}",
                                    'award_points': 'N/A'
                                }
                                flights.append(flight)
                    except:
                        continue
            
            # Method 3: Look for bound-card-new elements (actual flight containers) - Based on actual HTML structure
            bound_cards = soup.find_all('ey-bound-card-new', limit=20)
            if bound_cards:
                print(f"  Found {len(bound_cards)} bound card(s) (flight container(s))")
                for card in bound_cards:
                    try:
                        flight = {
                            'airline': 'Etihad Airways',
                            'flight_number': 'N/A',
                            'departure_time': 'N/A',
                            'arrival_time': 'N/A',
                            'duration': 'N/A',
                            'price': 'N/A',
                            'award_points': 'N/A'
                        }
                        
                        # Extract flight numbers - can be multiple for connecting flights
                        # Look for: <span class="flight-number ng-star-inserted">EY&nbsp;219&nbsp;</span>
                        flight_numbers = []
                        flight_number_elems = card.find_all('span', class_='flight-number')
                        for elem in flight_number_elems:
                            text = elem.get_text(strip=True)
                            # Extract EY followed by numbers (handle &nbsp; as space)
                            match = re.search(r'EY\s*(\d{3,4})', text, re.IGNORECASE)
                            if match:
                                flight_num = f"EY {match.group(1)}"
                                if flight_num not in flight_numbers:
                                    flight_numbers.append(flight_num)
                        
                        if flight_numbers:
                            # Join multiple flight numbers with comma for connecting flights
                            flight['flight_number'] = ', '.join(flight_numbers)
                        
                        # Extract departure time - look for: <time id="departureTime" class="bound-time">04:25</time>
                        dep_time_elem = card.find('time', id='departureTime')
                        if dep_time_elem:
                            flight['departure_time'] = dep_time_elem.get_text(strip=True)
                        
                        # Extract arrival time - look for: <time id="arrivalTime" class="bound-time">10:25</time>
                        arr_time_elem = card.find('time', id='arrivalTime')
                        if arr_time_elem:
                            flight['arrival_time'] = arr_time_elem.get_text(strip=True)
                        
                        # Extract duration - look for: <span class="total-duration ng-star-inserted"> 7h 30m </span>
                        duration_elem = card.find('span', class_='total-duration')
                        if duration_elem:
                            duration_text = duration_elem.get_text(strip=True)
                            # Clean up duration text (e.g., " 7h 30m " -> "7h 30m")
                            duration_text = re.sub(r'\s+', ' ', duration_text).strip()
                            flight['duration'] = duration_text
                        
                        # Extract Economy price - look for cabin--blue (Economy class)
                        # Structure: <div class="cff-container cabin--blue cabin-1">...<span class="price-amount">49,095</span>
                        economy_container = card.find('div', class_=re.compile(r'cabin--blue|cabin-1'))
                        if economy_container:
                            price_elem = economy_container.find('span', class_='price-amount')
                            if price_elem:
                                price_text = price_elem.get_text(strip=True)
                                # Remove commas and validate
                                price_val = price_text.replace(',', '')
                                if price_val.isdigit() and int(price_val) > 100:
                                    flight['price'] = f"₹{price_text}"
                        
                        # Only add flight if we have at least flight number or times
                        if flight['flight_number'] != 'N/A' or flight['departure_time'] != 'N/A':
                            flights.append(flight)
                            print(f"    Extracted: {flight['flight_number']} | {flight['departure_time']} -> {flight['arrival_time']} | {flight['duration']} | {flight['price']}")
                    except Exception as e:
                        print(f"    Error extracting from bound card: {e}")
                        continue
            
            # Remove duplicates based on flight number
            seen = set()
            unique_flights = []
            for flight in flights:
                key = flight.get('flight_number', '')
                if key and key not in seen:
                    seen.add(key)
                    unique_flights.append(flight)
                elif not key:
                    # Keep flights without flight numbers if they have prices
                    if flight.get('price', 'N/A') != 'N/A':
                        unique_flights.append(flight)
            
            print(f"  Extracted {len(unique_flights)} unique flight(s)")
            return unique_flights
            
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_flights_from_data(self):
        """Extract flight data from captured API response or page"""
        flights = []
        
        try:
            # Try API response first
            if self.flight_data:
                print("Extracting flights from API response...")
                api_flights = self._parse_api_response(self.flight_data)
                if api_flights:
                    flights = api_flights
                else:
                    print("API parsing returned no flights, trying HTML...")
                    flights = self._parse_html()
            else:
                print("No API response captured, trying HTML extraction...")
                flights = self._parse_html()
            
            return flights
            
        except Exception as e:
            print(f"Error extracting flights: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
    print("Etihad Airways Flight Scraper (Undetected ChromeDriver)")
    print("=" * 60)
    print()
    
    # Get user input
    if len(sys.argv) >= 4:
        origin_input = sys.argv[1]
        destination_input = sys.argv[2]
        date_input = sys.argv[3]
    else:
        origin_input = input("Enter origin city or code (e.g., Kolkata or CCU): ").strip()
        destination_input = input("Enter destination city or code (e.g., Abu Dhabi or AUH): ").strip()
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
    
    print(f"\nSearching for flights: {origin} -> {destination} on {date}\n")
    
    # Create scraper and scrape
    scraper = EtihadScraper()
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
        print("2. API structure needs to be discovered")
        print("3. Network interception didn't capture the data")
        print("4. Security system blocked the request")
        print("\nTip: Check etihad_api_response.json and etihad_page_source.html for debugging.")


if __name__ == "__main__":
    main()
