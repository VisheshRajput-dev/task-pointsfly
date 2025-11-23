"""
Main scraper module for IndiGo flights - Attempt 2
Using undetected-chromedriver for better stealth
"""

import time
import sys
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import config
from utils import normalize_city_input, parse_date, format_flight_data


class IndiGoScraper:
    """Scraper class for IndiGo flight data using undetected-chromedriver"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Initialize and configure Chrome WebDriver using undetected-chromedriver"""
        try:
            print("Setting up Chrome WebDriver with undetected-chromedriver...")
            
            # Initialize undetected Chrome driver
            # This automatically handles ChromeDriver installation and patching
            print("Starting Chrome browser (this may take a moment)...")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Clean up any previous driver instance
                    if hasattr(self, 'driver') and self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                    
                    # Create NEW options object for each attempt (undetected-chromedriver doesn't allow reuse)
                    options = uc.ChromeOptions()
                    
                    # Always show browser for testing
                    if not config.HEADLESS_MODE:
                        options.add_argument('--start-maximized')
                    
                    # Set user agent
                    options.add_argument(f'user-agent={config.USER_AGENT}')
                    
                    # Only add options that undetected-chromedriver supports
                    # Don't use excludeSwitches or useAutomationExtension - they're not supported
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    
                    # Initialize driver
                    self.driver = uc.Chrome(options=options, version_main=None, keep_alive=True)
                    
                    # Give browser a moment to fully start
                    time.sleep(3)
                    
                    # Verify browser is actually open by checking window handles
                    handles = self.driver.window_handles
                    if len(handles) > 0:
                        print(f"Browser opened successfully with {len(handles)} window(s)!")
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
            
            # Set up waits - but use longer timeouts to prevent browser from closing
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            # Don't set page_load_timeout too short - it might cause browser to close
            self.driver.set_page_load_timeout(60)  # Increased timeout
            self.wait = WebDriverWait(self.driver, config.EXPLICIT_WAIT_TIMEOUT)
            
            # Give browser additional time to fully initialize
            time.sleep(2)
            
            # Keep browser alive by accessing it
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
        """Close the browser driver"""
        if self.driver:
            try:
                # Try to close gracefully
                self.driver.quit()
            except:
                try:
                    # If quit fails, try close
                    self.driver.close()
                except:
                    # Ignore cleanup errors
                    pass
    
    def navigate_to_search_page(self):
        """Navigate to IndiGo flight search page"""
        try:
            print("Navigating to IndiGo website...")
            
            # Check if driver is still valid
            try:
                # Check window handles to verify browser is open
                handles = self.driver.window_handles
                if len(handles) == 0:
                    raise Exception("Browser window is closed")
                print(f"Browser has {len(handles)} open window(s)")
            except Exception as e:
                print(f"Browser window appears to be closed: {e}")
                print("Attempting to reinitialize browser...")
                if not self.setup_driver():
                    return False
            
            # Navigate to the page with retry and error handling
            print(f"Loading URL: {config.FLIGHT_SEARCH_URL}")
            
            navigation_success = False
            max_nav_retries = 3
            
            for nav_attempt in range(max_nav_retries):
                try:
                    # Double-check browser is still open
                    handles = self.driver.window_handles
                    if len(handles) == 0:
                        raise Exception("Browser window closed before navigation")
                    
                    # Navigate with timeout handling
                    # Use a try-except to catch any navigation errors
                    try:
                        # First, ensure browser is responsive
                        _ = self.driver.current_url
                        time.sleep(1)
                        
                        # Navigate - use execute_script as fallback if get() fails
                        try:
                            # Set a longer timeout for this specific navigation
                            original_timeout = self.driver.timeouts.page_load
                            self.driver.set_page_load_timeout(60)
                            
                            self.driver.get(config.FLIGHT_SEARCH_URL)
                            
                            # Reset timeout
                            self.driver.set_page_load_timeout(original_timeout)
                        except Exception as direct_get_error:
                            # If direct get() fails, try JavaScript navigation
                            print("Direct navigation failed, trying JavaScript navigation...")
                            try:
                                self.driver.execute_script(f"window.location.href = '{config.FLIGHT_SEARCH_URL}';")
                                time.sleep(5)  # Wait longer for navigation
                            except Exception as js_error:
                                raise direct_get_error  # Raise original error
                    except Exception as get_error:
                        # Check if browser is still open
                        try:
                            handles_after = self.driver.window_handles
                            if len(handles_after) == 0:
                                raise Exception("Browser closed during navigation")
                            # Browser is still open, maybe page just took too long
                            # Try to get current URL anyway
                            try:
                                current_url = self.driver.current_url
                                if 'goindigo' in current_url.lower():
                                    print(f"Navigation may have succeeded (timeout but URL is correct): {current_url}")
                                    navigation_success = True
                                    break
                            except:
                                pass
                        except:
                            raise Exception(f"Browser closed: {get_error}")
                        
                        # If it's a timeout but browser is open, continue
                        if "timeout" in str(get_error).lower() or "timed out" in str(get_error).lower():
                            print(f"Navigation timeout, but browser is still open. Continuing...")
                            time.sleep(2)
                            try:
                                current_url = self.driver.current_url
                                if 'goindigo' in current_url.lower():
                                    navigation_success = True
                                    break
                            except:
                                pass
                        else:
                            raise get_error
                    
                    # Wait for page to start loading
                    time.sleep(3)
                    
                    # Verify navigation was successful
                    try:
                        current_url = self.driver.current_url
                        if 'goindigo' in current_url.lower() or 'indigo' in current_url.lower():
                            print(f"Successfully navigated to: {current_url}")
                            navigation_success = True
                            break
                        else:
                            raise Exception(f"Unexpected URL: {current_url}")
                    except Exception as verify_error:
                        # Check if browser is still open
                        try:
                            handles_check = self.driver.window_handles
                            if len(handles_check) == 0:
                                raise Exception("Browser closed after navigation")
                        except:
                            raise Exception(f"Browser closed: {verify_error}")
                        raise verify_error
                        
                except Exception as nav_error:
                    if nav_attempt < max_nav_retries - 1:
                        print(f"Navigation attempt {nav_attempt + 1} failed: {nav_error}")
                        print("Retrying navigation...")
                        
                        # Check if browser is still open, reinitialize if needed
                        try:
                            handles = self.driver.window_handles
                            if len(handles) == 0:
                                print("Browser closed. Reinitializing...")
                                if not self.setup_driver():
                                    return False
                        except:
                            print("Browser closed. Reinitializing...")
                            if not self.setup_driver():
                                return False
                        
                        time.sleep(3)
                    else:
                        print(f"Failed to navigate after {max_nav_retries} attempts: {nav_error}")
                        return False
            
            if not navigation_success:
                return False
            
            time.sleep(config.ACTION_DELAY)
            
            # Handle cookie consent if present
            try:
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(text(), 'Accept') or contains(text(), 'OK') or contains(@class, 'cookie')]"))
                )
                cookie_button.click()
                time.sleep(config.ACTION_DELAY)
                print("Handled cookie consent.")
            except TimeoutException:
                pass  # No cookie popup
            
            # Handle any popups/modals
            try:
                close_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(@class, 'close') or contains(@class, 'modal-close')]")
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.5)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error navigating to search page: {e}")
            return False
    
    def fill_search_form(self, origin, destination, date):
        """Fill the flight search form"""
        try:
            print(f"Filling search form: {origin} -> {destination} on {date}")
            time.sleep(2)  # Wait for page to fully load
            
            # Wait for the form to be visible
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-widget-form")))
            time.sleep(1)
            
            # Fill Origin field
            print("Filling origin field...")
            try:
                origin_container = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//div[@aria-label='sourceCity' or contains(@class, 'search-widget-form-body__from')]"))
                )
                origin_container.click()
                time.sleep(1)
                
                origin_input = self.driver.find_element(By.XPATH, 
                    "//div[@aria-label='sourceCity']//input[@placeholder='Start typing..']")
                
                # Type with human-like delays (2 chars per second)
                self.driver.execute_script("arguments[0].value = '';", origin_input)
                for char in origin:
                    origin_input.send_keys(char)
                    time.sleep(0.5)
                
                time.sleep(0.5)  # Wait before selecting dropdown
                
                # Select from dropdown
                try:
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "city-selection")))
                    time.sleep(1.5)
                    
                    dropdown_option = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, 
                            f"//div[contains(@class, 'city-selection__list-item-wrapper')]//div[contains(@class, 'city-selection__list-item--info__right')]//div[normalize-space(text())='{origin}']/ancestor::div[contains(@class, 'city-selection__list-item-wrapper')]"))
                    )
                    dropdown_option.click()
                    time.sleep(1)
                    print(f"Selected origin: {origin}")
                except TimeoutException:
                    origin_input.send_keys(Keys.ENTER)
                    time.sleep(1)
                    print(f"Used Enter for origin: {origin}")
            except Exception as e:
                print(f"Error filling origin: {e}")
                return False
            
            # Fill Destination field
            print("Filling destination field...")
            try:
                dest_container = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//div[@aria-label='destinationCity' or contains(@class, 'search-widget-form-body__to')]"))
                )
                dest_container.click()
                time.sleep(1)
                
                dest_input = self.driver.find_element(By.XPATH,
                    "//div[@aria-label='destinationCity']//input[@placeholder='Start typing..']")
                
                # Type with human-like delays
                self.driver.execute_script("arguments[0].value = '';", dest_input)
                for char in destination:
                    dest_input.send_keys(char)
                    time.sleep(0.5)
                
                time.sleep(0.5)
                
                # Select from dropdown
                try:
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "city-selection")))
                    time.sleep(1.5)
                    
                    dropdown_option = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH,
                            f"//div[contains(@class, 'city-selection__list-item-wrapper')]//div[contains(@class, 'city-selection__list-item--info__right')]//div[normalize-space(text())='{destination}']/ancestor::div[contains(@class, 'city-selection__list-item-wrapper')]"))
                    )
                    dropdown_option.click()
                    time.sleep(1)
                    print(f"Selected destination: {destination}")
                except TimeoutException:
                    dest_input.send_keys(Keys.ENTER)
                    time.sleep(1)
                    print(f"Used Enter for destination: {destination}")
            except Exception as e:
                print(f"Error filling destination: {e}")
                return False
            
            # Fill Date field - Click on calendar day button
            print("Filling date field...")
            try:
                date_parts = date.split('-')
                if len(date_parts) == 3:
                    if len(date_parts[0]) == 4:  # YYYY-MM-DD
                        year, month, day = date_parts
                    else:  # DD-MM-YYYY
                        day, month, year = date_parts
                else:
                    raise Exception(f"Invalid date format: {date}")
                
                # Convert to integers for comparison
                year_int = int(year)
                month_int = int(month)
                day_int = int(day)
                
                # Click on date container to open calendar
                date_container = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//div[@aria-label='departureDate' or contains(@class, 'search-widget-form-body__departure')]"))
                )
                date_container.click()
                time.sleep(2)
                
                # Wait for calendar to appear
                try:
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rdrCalendarWrapper")))
                    time.sleep(1)
                    print("Calendar opened successfully")
                except TimeoutException:
                    print("Warning: Calendar did not appear, trying alternative method...")
                    # Try setting date via input as fallback
                    try:
                        date_input = self.driver.find_element(By.XPATH,
                            "//div[@aria-label='departureDate']//input")
                        formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        js_code = f"""
                        var input = arguments[0];
                        input.value = '{formatted_date}';
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        """
                        self.driver.execute_script(js_code, date_input)
                        time.sleep(1)
                        print(f"Set date via input (fallback): {formatted_date}")
                        return  # Exit early if using fallback
                    except:
                        print("Warning: Could not set date via input either.")
                        return
                
                # Navigate to correct month if needed
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                target_month_name = month_names[month_int - 1]
                target_month_year = f"{target_month_name} {year_int}"
                
                max_nav_attempts = 12  # Max 12 months to navigate
                for nav_attempt in range(max_nav_attempts):
                    try:
                        # Get current month/year from calendar
                        month_year_elem = self.driver.find_element(By.CLASS_NAME, "rdrMonthAndYearPickers")
                        current_month_year = month_year_elem.text.strip()
                        
                        if current_month_year == target_month_year:
                            # We're on the correct month, break
                            print(f"✓ Calendar is on correct month: {target_month_year}")
                            break
                        
                        # Determine if we need to go forward or backward
                        current_parts = current_month_year.split()
                        if len(current_parts) == 2:
                            current_month_name = current_parts[0]
                            current_year = int(current_parts[1])
                            
                            current_month_num = month_names.index(current_month_name) + 1
                            
                            # Calculate months difference
                            months_diff = (year_int - current_year) * 12 + (month_int - current_month_num)
                            
                            if months_diff > 0:
                                # Need to go forward
                                next_button = self.driver.find_element(By.CLASS_NAME, "rdrNextButton")
                                next_button.click()
                                time.sleep(0.5)
                                print(f"Navigated forward to month {current_month_num + 1}")
                            elif months_diff < 0:
                                # Need to go backward
                                prev_button = self.driver.find_element(By.CLASS_NAME, "rdrPprevButton")
                                prev_button.click()
                                time.sleep(0.5)
                                print(f"Navigated backward to month {current_month_num - 1}")
                            else:
                                # Already on correct month
                                break
                    except Exception as nav_error:
                        if nav_attempt == 0:
                            print(f"Warning: Could not navigate calendar: {nav_error}")
                        break
                
                # Now find and click the day button
                time.sleep(1)
                
                day_found = False
                try:
                    # Method 1: Find day button by exact XPath with month context
                    print(f"Looking for date: {day_int} in month {month_int}, year {year_int}")
                    
                    # Try to find the day button in the correct month
                    month_containers = self.driver.find_elements(By.CLASS_NAME, "rdrMonth")
                    
                    for month_container in month_containers:
                        try:
                            # Check if this month matches our target
                            month_name_elem = month_container.find_element(By.CLASS_NAME, "rdrMonthName")
                            month_name_text = month_name_elem.text.strip()
                            
                            # Check if this month container has our target month
                            target_month_name = month_names[month_int - 1]
                            if target_month_name in month_name_text and str(year_int) in month_name_text:
                                # This is the correct month, find the day in this container
                                day_buttons = month_container.find_elements(By.XPATH,
                                    f".//button[contains(@class, 'rdrDay') and not(contains(@class, 'rdrDayDisabled')) and not(contains(@class, 'rdrDayPassive'))]")
                                
                                for day_button in day_buttons:
                                    try:
                                        date_span = day_button.find_element(By.XPATH, ".//span[@class='date']")
                                        date_text = date_span.text.strip()
                                        
                                        if date_text == str(day_int):
                                            # Found it! Click the button
                                            print(f"Found date button for {day_int}, clicking...")
                                            # Scroll into view first
                                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", day_button)
                                            time.sleep(0.5)
                                            
                                            # Try regular click first
                                            try:
                                                day_button.click()
                                                time.sleep(0.5)
                                            except:
                                                # If regular click fails, use JavaScript
                                                self.driver.execute_script("arguments[0].click();", day_button)
                                                time.sleep(0.5)
                                            
                                            # Wait for calendar to close or date to be set
                                            time.sleep(2)
                                            
                                            # Verify date was set by checking input
                                            try:
                                                date_input = self.driver.find_element(By.XPATH,
                                                    "//div[@aria-label='departureDate']//input")
                                                selected_date = date_input.get_attribute('value')
                                                if selected_date:
                                                    print(f"✓ Date selected successfully: {selected_date}")
                                                    day_found = True
                                                    break
                                                else:
                                                    # Date not set yet, try clicking again
                                                    print("Date not set, trying click again...")
                                                    self.driver.execute_script("arguments[0].click();", day_button)
                                                    time.sleep(2)
                                                    selected_date = date_input.get_attribute('value')
                                                    if selected_date:
                                                        print(f"✓ Date selected on retry: {selected_date}")
                                                        day_found = True
                                                        break
                                            except:
                                                # If we can't verify, assume it worked
                                                day_found = True
                                                print(f"✓ Selected date: {day_int}-{month_int}-{year_int}")
                                                break
                                    except Exception as e:
                                        continue
                                
                                if day_found:
                                    break
                        except:
                            continue
                    
                    # Method 2: If not found, try searching all visible day buttons
                    if not day_found:
                        print("Method 1 failed, trying method 2...")
                        all_day_buttons = self.driver.find_elements(By.XPATH,
                            "//button[contains(@class, 'rdrDay') and not(contains(@class, 'rdrDayDisabled')) and not(contains(@class, 'rdrDayPassive'))]")
                        
                        print(f"Found {len(all_day_buttons)} clickable day buttons")
                        
                        for day_button in all_day_buttons:
                            try:
                                date_span = day_button.find_element(By.XPATH, ".//span[@class='date']")
                                date_text = date_span.text.strip()
                                
                                if date_text == str(day_int):
                                    # Check if button is visible and in viewport
                                    if day_button.is_displayed():
                                        print(f"Found date button for {day_int}, clicking (method 2)...")
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", day_button)
                                        time.sleep(0.5)
                                        
                                        # Try regular click first
                                        try:
                                            day_button.click()
                                            time.sleep(0.5)
                                        except:
                                            self.driver.execute_script("arguments[0].click();", day_button)
                                            time.sleep(0.5)
                                        
                                        # Wait and verify
                                        time.sleep(2)
                                        try:
                                            date_input = self.driver.find_element(By.XPATH,
                                                "//div[@aria-label='departureDate']//input")
                                            selected_date = date_input.get_attribute('value')
                                            if selected_date:
                                                print(f"✓ Date selected (method 2): {selected_date}")
                                                day_found = True
                                                break
                                        except:
                                            day_found = True
                                            print(f"✓ Selected date (method 2): {day_int}-{month_int}-{year_int}")
                                            break
                            except:
                                continue
                    
                    # Method 3: Direct XPath search
                    if not day_found:
                        print("Method 2 failed, trying method 3 (direct XPath)...")
                        try:
                            day_button = self.driver.find_element(By.XPATH,
                                f"//button[contains(@class, 'rdrDay') and not(contains(@class, 'rdrDayDisabled')) and not(contains(@class, 'rdrDayPassive'))]//span[@class='date' and normalize-space(text())='{day_int}']/ancestor::button[1]")
                            
                            if day_button.is_displayed():
                                print(f"Found date button via XPath for {day_int}, clicking (method 3)...")
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", day_button)
                                time.sleep(0.5)
                                
                                # Try regular click first
                                try:
                                    day_button.click()
                                    time.sleep(0.5)
                                except:
                                    self.driver.execute_script("arguments[0].click();", day_button)
                                    time.sleep(0.5)
                                
                                # Wait and verify
                                time.sleep(2)
                                try:
                                    date_input = self.driver.find_element(By.XPATH,
                                        "//div[@aria-label='departureDate']//input")
                                    selected_date = date_input.get_attribute('value')
                                    if selected_date:
                                        print(f"✓ Date selected (method 3): {selected_date}")
                                        day_found = True
                                except:
                                    day_found = True
                                    print(f"✓ Selected date (method 3): {day_int}-{month_int}-{year_int}")
                        except Exception as e:
                            print(f"Method 3 failed: {e}")
                    
                    # Always verify the date was selected
                    time.sleep(1)
                    date_verified = False
                    try:
                        date_input = self.driver.find_element(By.XPATH,
                            "//div[@aria-label='departureDate']//input")
                        selected_date_value = date_input.get_attribute('value')
                        if selected_date_value:
                            print(f"✓ Verified: Date input shows '{selected_date_value}'")
                            date_verified = True
                        else:
                            print("⚠ Warning: Date input is empty after selection")
                            # Try clicking the date button one more time
                            if day_found:
                                print("Trying to click date button again...")
                                try:
                                    # Find and click the date button again
                                    day_button = self.driver.find_element(By.XPATH,
                                        f"//button[contains(@class, 'rdrDay') and not(contains(@class, 'rdrDayDisabled'))]//span[@class='date' and normalize-space(text())='{day_int}']/ancestor::button[1]")
                                    day_button.click()
                                    time.sleep(2)
                                    selected_date_value = date_input.get_attribute('value')
                                    if selected_date_value:
                                        print(f"✓ Date set on retry: '{selected_date_value}'")
                                        date_verified = True
                                except:
                                    pass
                    except:
                        pass
                    
                    # If date still not verified, try fallback method
                    if not date_verified:
                        print(f"⚠ Date not verified, trying fallback: set date via input...")
                        try:
                            # Close calendar first if still open
                            try:
                                close_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'rdrCloseButton') or contains(@aria-label, 'close')]")
                                close_button.click()
                                time.sleep(0.5)
                            except:
                                # Click outside calendar to close it
                                try:
                                    self.driver.find_element(By.TAG_NAME, "body").click()
                                    time.sleep(0.5)
                                except:
                                    pass
                            
                            date_input = self.driver.find_element(By.XPATH,
                                "//div[@aria-label='departureDate']//input")
                            formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            
                            # Try multiple ways to set the date
                            try:
                                # Method 1: Direct value setting
                                self.driver.execute_script(f"arguments[0].value = '{formatted_date}';", date_input)
                                time.sleep(0.5)
                                
                                # Method 2: Trigger events
                                self.driver.execute_script("""
                                    var input = arguments[0];
                                    input.dispatchEvent(new Event('input', { bubbles: true }));
                                    input.dispatchEvent(new Event('change', { bubbles: true }));
                                    input.dispatchEvent(new Event('blur', { bubbles: true }));
                                """, date_input)
                                time.sleep(1)
                                
                                # Verify
                                selected_date_value = date_input.get_attribute('value')
                                if selected_date_value:
                                    print(f"✓ Date set via input fallback: '{selected_date_value}'")
                                else:
                                    print(f"⚠ Could not set date via input fallback")
                            except Exception as e:
                                print(f"⚠ Error setting date via input: {e}")
                        except Exception as e:
                            print(f"⚠ Could not set date via input: {e}")
                    
                except Exception as day_error:
                    print(f"⚠ Warning: Error while selecting date: {day_error}")
                    # Try fallback: set date via input
                    try:
                        date_input = self.driver.find_element(By.XPATH,
                            "//div[@aria-label='departureDate']//input")
                        formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        js_code = f"""
                        var input = arguments[0];
                        input.value = '{formatted_date}';
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        """
                        self.driver.execute_script(js_code, date_input)
                        time.sleep(1)
                        print(f"Set date via input (fallback): {formatted_date}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"Warning: Could not fill date field: {e}")
                import traceback
                traceback.print_exc()
            
            # Submit the form
            print("Submitting search...")
            time.sleep(1)
            try:
                search_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(@class, 'search-btn') or contains(text(), 'Search')] | "
                        "//button[@type='button' and contains(@class, 'skyplus-button')]"))
                )
                
                if search_button.get_attribute('disabled'):
                    time.sleep(2)
                    self.driver.execute_script("arguments[0].click();", search_button)
                else:
                    search_button.click()
                
                print("Search submitted. Waiting for results...")
                time.sleep(config.AFTER_SEARCH_DELAY)
                
                return True
            except Exception as e:
                print(f"Error clicking search button: {e}")
                return False
            
        except Exception as e:
            print(f"Error filling search form: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_flight_data(self):
        """Extract flight data from the results page"""
        try:
            print("Waiting for flight results to load...")
            
            # Wait for URL to change to results page
            try:
                self.wait.until(lambda driver: 'booking' in driver.current_url.lower() or 
                               'search' in driver.current_url.lower() or 
                               'result' in driver.current_url.lower())
                time.sleep(3)
            except:
                pass
            
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            
            # Wait for flight results to appear
            print("Waiting for flight results to appear...")
            max_wait_time = 30
            wait_interval = 2
            waited = 0
            
            while waited < max_wait_time:
                try:
                    # Check for flight containers
                    flight_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                        ".srp__search-result-list__item")
                    
                    if len(flight_containers) > 0:
                        print(f"Found {len(flight_containers)} flight containers!")
                        time.sleep(5)
                        break
                    
                    # Check for flight numbers
                    all_flight_elements = self.driver.find_elements(By.XPATH, 
                        "//*[contains(text(), '6E')]")
                    
                    valid_flights = []
                    for e in all_flight_elements:
                        text = e.text
                        if text and re.search(r'6E\s*\d{3,}', text, re.IGNORECASE):
                            if not re.search(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', text.strip(), re.IGNORECASE):
                                valid_flights.append(e)
                    
                    price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '₹')]")
                    
                    if len(valid_flights) > 0 and len(price_elements) > 2:
                        print(f"Flight results detected! Found {len(valid_flights)} flights, {len(price_elements)} prices")
                        time.sleep(5)
                        break
                    else:
                        if waited % 5 == 0:
                            print(f"Waiting for results... ({waited}s/{max_wait_time}s)")
                        time.sleep(wait_interval)
                        waited += wait_interval
                except Exception as e:
                    if waited % 5 == 0:
                        print(f"Waiting... ({waited}s/{max_wait_time}s) - Error: {e}")
                    time.sleep(wait_interval)
                    waited += wait_interval
            
            # Extract flight data
            print("Extracting flight data...")
            flights = self._extract_with_selenium()
            
            return flights
            
        except Exception as e:
            print(f"Error extracting flight data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_with_selenium(self):
        """Extract flight data using Selenium"""
        flights = []
        try:
            # Find flight containers
            flight_selectors = [
                ".srp__search-result-list__item",
                "div.srp__search-result-list__item",
                "div[class*='flight-card']",
                "div[class*='flight-result']",
            ]
            
            flight_elements = []
            for selector in flight_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        flight_elements = elements
                        print(f"Found {len(elements)} flights using selector: {selector}")
                        break
                except:
                    continue
            
            if not flight_elements:
                print("No flight containers found. Searching page for flight data...")
                # Search for elements containing flight numbers
                all_elements = self.driver.find_elements(By.XPATH, "//*")
                for elem in all_elements:
                    try:
                        text = elem.text
                        if text and len(text) < 500:
                            has_flight = bool(re.search(r'6E\s*\d{3,}', text, re.IGNORECASE))
                            has_price = bool(re.search(r'[₹Rs]\s*[\d,]+', text, re.IGNORECASE))
                            has_times = len(re.findall(r'\b\d{1,2}:\d{2}\b', text)) >= 2
                            
                            if has_flight and has_price and has_times:
                                if not re.search(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', text.strip(), re.IGNORECASE):
                                    flight_elements.append(elem)
                    except:
                        continue
            
            # Extract data from each flight element
            seen_flights = set()  # Track seen flights to avoid duplicates
            for idx, element in enumerate(flight_elements[:20]):
                try:
                    flight_data = {
                        'airline': 'IndiGo',
                        'flight_number': 'N/A',
                        'departure_time': 'N/A',
                        'arrival_time': 'N/A',
                        'duration': 'N/A',
                        'price_inr': 'N/A',
                        'award_points': 'N/A'
                    }
                    
                    # Get text from element and its children
                    element_text = element.text
                    
                    # If element text is empty or very short, try to get text from child elements
                    if not element_text or len(element_text.strip()) < 10:
                        try:
                            child_elements = element.find_elements(By.XPATH, ".//*")
                            child_texts = [e.text for e in child_elements if e.text and len(e.text.strip()) > 0]
                            element_text = " ".join(child_texts)
                        except:
                            pass
                    
                    # Skip calendar elements
                    if re.search(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[,\s]+\d+\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', 
                                element_text.strip(), re.IGNORECASE):
                        continue
                    
                    # Extract flight number
                    flight_match = re.search(r'6E\s*\d{3,}', element_text, re.IGNORECASE)
                    if flight_match:
                        flight_data['flight_number'] = flight_match.group(0).strip()
                    else:
                        continue
                    
                    # Extract times
                    times = re.findall(r'\b(\d{1,2}):(\d{2})\b', element_text)
                    if len(times) >= 2:
                        flight_data['departure_time'] = f"{times[0][0]}:{times[0][1]}"
                        flight_data['arrival_time'] = f"{times[1][0]}:{times[1][1]}"
                    else:
                        continue
                    
                    # Extract duration
                    duration_patterns = [
                        r'(\d+)\s*h\s*(\d+)\s*m',
                        r'(\d+)\s*hr\s*(\d+)\s*min',
                        r'(\d+)\s*h(\d+)\s*m',
                    ]
                    for pattern in duration_patterns:
                        dur_match = re.search(pattern, element_text, re.IGNORECASE)
                        if dur_match:
                            flight_data['duration'] = f"{dur_match.group(1)}h {dur_match.group(2)}m"
                            break
                    
                    # Extract price - PRIORITIZE ECONOMY CLASS PRICE
                    price_found = False
                    
                    # First, try to get Economy class price (the cheaper one)
                    try:
                        economy_price_elems = element.find_elements(By.CSS_SELECTOR, 
                            ".economy-class-item .selected-fare__fare-price")
                        
                        if economy_price_elems:
                            price_text = economy_price_elems[0].text.strip()
                            # Extract price from text (remove any icons/spans)
                            price_match = re.search(r'₹\s*([\d,]+)', price_text)
                            if price_match:
                                price_val = price_match.group(1)
                                price_num = price_val.replace(',', '').replace('.', '')
                                if price_num.isdigit() and int(price_num) >= 100:
                                    flight_data['price_inr'] = f"₹{price_val}"
                                    price_found = True
                                    print(f"  Found Economy price: ₹{price_val}")
                    except Exception as e:
                        pass
                    
                    # If Economy price not found, try Business class price as fallback
                    if not price_found:
                        try:
                            business_price_elems = element.find_elements(By.CSS_SELECTOR, 
                                ".business-class-item .selected-fare__fare-price")
                            
                            if business_price_elems:
                                price_text = business_price_elems[0].text.strip()
                                price_match = re.search(r'₹\s*([\d,]+)', price_text)
                                if price_match:
                                    price_val = price_match.group(1)
                                    price_num = price_val.replace(',', '').replace('.', '')
                                    if price_num.isdigit() and int(price_num) >= 100:
                                        flight_data['price_inr'] = f"₹{price_val}"
                                        price_found = True
                                        print(f"  Found Business price (fallback): ₹{price_val}")
                        except Exception as e:
                            pass
                    
                    # Fallback: try regex patterns in element text if still not found
                    if not price_found:
                        price_patterns = [
                            r'₹\s*([\d,]+)',      # ₹ 21,159 (with space)
                            r'₹([\d,]+)',         # ₹21,159 (no space)
                            r'Rs\.?\s*([\d,]+)',  # Rs 21,159 or Rs. 21,159
                            r'INR\s*([\d,]+)',    # INR 21,159
                            r'([\d,]+)\s*INR',    # 21,159 INR
                        ]
                        
                        for pattern in price_patterns:
                            price_matches = re.findall(pattern, element_text, re.IGNORECASE)
                            # Filter out small numbers that aren't prices (like flight numbers, times)
                            for match in price_matches:
                                if isinstance(match, tuple):
                                    match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                                if not match:
                                    continue
                                # Remove commas and check if it's a reasonable price (at least 1000)
                                price_num = match.replace(',', '').replace('.', '')
                                if price_num.isdigit() and int(price_num) >= 1000:
                                    flight_data['price_inr'] = f"₹{match}"
                                    price_found = True
                                    break
                            if price_found:
                                break
                    
                    # If still no price, try looking in child elements specifically
                    if not price_found:
                        try:
                            # Approach 1: Find elements containing ₹ symbol with numbers nearby
                            price_elements = element.find_elements(By.XPATH, 
                                ".//*[contains(text(), '₹') or contains(text(), 'Rs')]")
                            
                            for price_elem in price_elements:
                                try:
                                    price_text = price_elem.text
                                    # Try to extract price from this element
                                    for pattern in price_patterns:
                                        price_match = re.search(pattern, price_text, re.IGNORECASE)
                                        if price_match:
                                            price_val = price_match.group(1) if price_match.groups() else ''
                                            if not price_val:
                                                continue
                                            price_num = price_val.replace(',', '').replace('.', '')
                                            if price_num.isdigit() and int(price_num) >= 1000:
                                                flight_data['price_inr'] = f"₹{price_val}"
                                                price_found = True
                                                break
                                    if price_found:
                                        break
                                    
                                    # Also try getting text from parent
                                    try:
                                        parent = price_elem.find_element(By.XPATH, "./..")
                                        parent_text = parent.text
                                        for pattern in price_patterns:
                                            price_match = re.search(pattern, parent_text, re.IGNORECASE)
                                            if price_match:
                                                price_val = price_match.group(1) if price_match.groups() else ''
                                                if not price_val:
                                                    continue
                                                price_num = price_val.replace(',', '').replace('.', '')
                                                if price_num.isdigit() and int(price_num) >= 1000:
                                                    flight_data['price_inr'] = f"₹{price_val}"
                                                    price_found = True
                                                    break
                                        if price_found:
                                            break
                                    except:
                                        pass
                                except:
                                    continue
                            
                            # Approach 2: Look for price in data attributes or specific price classes
                            if not price_found:
                                try:
                                    # Look for elements with price-related classes
                                    price_containers = element.find_elements(By.XPATH, 
                                        ".//*[contains(@class, 'price') or contains(@class, 'fare') or contains(@class, 'amount')]")
                                    for container in price_containers:
                                        container_text = container.text
                                        for pattern in price_patterns:
                                            price_match = re.search(pattern, container_text, re.IGNORECASE)
                                            if price_match:
                                                price_val = price_match.group(1) if price_match.groups() else ''
                                                if not price_val:
                                                    continue
                                                price_num = price_val.replace(',', '').replace('.', '')
                                                if price_num.isdigit() and int(price_num) >= 1000:
                                                    flight_data['price_inr'] = f"₹{price_val}"
                                                    price_found = True
                                                    break
                                        if price_found:
                                            break
                                except:
                                    pass
                            
                            # Approach 3: Look for numbers near ₹ symbol in the entire element tree
                            if not price_found:
                                try:
                                    # Get all text nodes that contain ₹
                                    all_text = element.text
                                    # Find all occurrences of ₹ followed by numbers
                                    rupee_pattern = r'₹\s*([\d,]{4,})'  # At least 4 digits (prices are usually 4+ digits)
                                    matches = re.findall(rupee_pattern, all_text)
                                    for match in matches:
                                        price_num = match.replace(',', '').replace('.', '')
                                        if price_num.isdigit() and int(price_num) >= 1000:
                                            flight_data['price_inr'] = f"₹{match}"
                                            price_found = True
                                            break
                                except:
                                    pass
                        except Exception as e:
                            # Debug: print if needed
                            pass
                    
                    # Extract award points - PRIORITIZE ECONOMY CLASS POINTS
                    try:
                        # First, try to get Economy class points (usually lower, more relevant)
                        economy_points_elems = element.find_elements(By.CSS_SELECTOR, 
                            ".economy-class-item .loyalty-points.loyalty-starts-at-points")
                        
                        if economy_points_elems:
                            points_text = economy_points_elems[0].text.strip()
                            # Extract number from "+ Earn 736 IndiGo BluChips"
                            points_match = re.search(r'(\d{1,3}(?:,\d{3})*)', points_text)
                            if points_match:
                                flight_data['award_points'] = points_match.group(1)
                                print(f"  Found Economy points: {flight_data['award_points']}")
                    except Exception as e:
                        pass
                    
                    # If Economy points not found, try Business class points as fallback
                    if flight_data['award_points'] == 'N/A':
                        try:
                            business_points_elems = element.find_elements(By.CSS_SELECTOR, 
                                ".business-class-item .loyalty-points.loyalty-starts-at-points")
                            
                            if business_points_elems:
                                points_text = business_points_elems[0].text.strip()
                                points_match = re.search(r'(\d{1,3}(?:,\d{3})*)', points_text)
                                if points_match:
                                    flight_data['award_points'] = points_match.group(1)
                                    print(f"  Found Business points (fallback): {flight_data['award_points']}")
                        except Exception as e:
                            pass
                    
                    # Fallback: extract points using regex from element text
                    if flight_data['award_points'] == 'N/A':
                        points_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:IndiGo\s*BluChips|points|miles|pts)', 
                                                element_text, re.IGNORECASE)
                        if points_match:
                            flight_data['award_points'] = points_match.group(1)
                    
                    # Only add if we have flight number and at least price or times
                    if flight_data['flight_number'] != 'N/A' and \
                       (flight_data['price_inr'] != 'N/A' or 
                        (flight_data['departure_time'] != 'N/A' and flight_data['arrival_time'] != 'N/A')):
                        
                        # Create unique key to avoid duplicates
                        flight_key = f"{flight_data['flight_number']}_{flight_data['departure_time']}_{flight_data['arrival_time']}"
                        
                        if flight_key not in seen_flights:
                            seen_flights.add(flight_key)
                            # Clean up price - if it's just "₹," or invalid, set to N/A
                            if flight_data['price_inr'] in ['₹,', '₹', 'N/A'] or not flight_data['price_inr'].replace('₹', '').replace(',', '').isdigit():
                                if not price_found:
                                    flight_data['price_inr'] = 'N/A'
                            
                            flights.append(flight_data)
                            print(f"Extracted flight {len(flights)}: {flight_data['flight_number']} | "
                                  f"{flight_data['departure_time']}-{flight_data['arrival_time']} | "
                                  f"{flight_data['price_inr']}")
                        else:
                            # Duplicate flight, skip it
                            continue
                
                except Exception as e:
                    print(f"Error extracting data from flight element {idx}: {e}")
                    continue
            
            return flights
            
        except Exception as e:
            print(f"Error in Selenium extraction: {e}")
            return []

    def scrape_flights(self, origin, destination, date):
        """Main method to scrape flights"""
        try:
            # Setup driver
            if not self.setup_driver():
                return []
            
            # Navigate to search page
            if not self.navigate_to_search_page():
                return []
            
            # Fill search form
            if not self.fill_search_form(origin, destination, date):
                return []
            
            # Extract flight data
            flights = self.extract_flight_data()
            
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
    print("IndiGo Flight Scraper - Attempt 2 (undetected-chromedriver)")
    print("=" * 60)
    print()
    
    # Get user input
    if len(sys.argv) >= 4:
        origin_input = sys.argv[1]
        destination_input = sys.argv[2]
        date_input = sys.argv[3]
    else:
        origin_input = input("Enter origin city or code (e.g., Delhi or DEL): ").strip()
        destination_input = input("Enter destination city or code (e.g., Mumbai or BOM): ").strip()
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
    scraper = IndiGoScraper()
    flights = scraper.scrape_flights(origin, destination, date)
    
    # Display results
    print("\n" + "=" * 60)
    print("FLIGHT RESULTS")
    print("=" * 60)
    print()
    
    if flights:
        formatted_output = format_flight_data(flights)
        print(formatted_output)
        print(f"\nTotal flights found: {len(flights)}")
    else:
        print("No flights found. This could be due to:")
        print("1. No flights available for the selected route/date")
        print("2. Website structure has changed (selectors may need updating)")
        print("3. Anti-scraping measures detected")
        print("\nTip: Check the browser window to see what's happening.")


if __name__ == "__main__":
    main()
