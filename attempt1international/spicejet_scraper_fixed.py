# This is a complete rewrite of the _parse_html method to fix all issues
# I'll provide the corrected version that you can replace in the main file

def _parse_html(self):
    """Parse flight data from HTML to get prices and points for all fare types"""
    flights = []
    
    try:
        print("Parsing HTML for prices and points...")
        
        # Wait for page to fully render
        time.sleep(5)
        
        # Scroll to load all content
        try:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(3)
        except:
            pass
        
        # Wait for fare bundles
        try:
            self.page.wait_for_selector("#fare-bundle-val, [id='fare-bundle-val']", timeout=10000)
            time.sleep(2)
        except:
            pass
        
        # Find all fare-bundle-val containers (one per flight)
        fare_bundles = self.page.query_selector_all("#fare-bundle-val, [id='fare-bundle-val']")
        print(f"Found {len(fare_bundles)} fare bundle(s)")
        
        seen_flights = set()
        
        for bundle in fare_bundles:
            try:
                # Get the parent container that has the flight info
                flight_container = bundle.evaluate("""
                    el => {
                        let current = el;
                        // Go up to find container with aircraft-no
                        for (let i = 0; i < 20 && current; i++) {
                            let aircraftNo = current.querySelector('#aircraft-no');
                            if (aircraftNo) {
                                return current;
                            }
                            current = current.parentElement;
                        }
                        return el.parentElement?.parentElement || el.parentElement;
                    }
                """)
                
                if not flight_container:
                    continue
                
                # Get flight number from aircraft-no
                aircraft_no_elem = bundle.query_selector("#aircraft-no, [id='aircraft-no']")
                if not aircraft_no_elem:
                    # Try to find in parent
                    try:
                        parent = bundle.evaluate("el => el.parentElement")
                        if parent:
                            all_elems = bundle.query_selector_all("*")
                            for elem in all_elems:
                                if elem.get_attribute('id') == 'aircraft-no':
                                    aircraft_no_elem = elem
                                    break
                    except:
                        pass
                
                if not aircraft_no_elem:
                    continue
                
                flight_num = aircraft_no_elem.inner_text() if hasattr(aircraft_no_elem, 'inner_text') else aircraft_no_elem.text_content()
                flight_num = flight_num.strip()
                
                if not flight_num:
                    continue
                
                # Get all text from the flight container
                container_text = bundle.evaluate("""
                    el => {
                        let current = el;
                        for (let i = 0; i < 15 && current; i++) {
                            let text = current.innerText || '';
                            if (text.match(/\\d{1,2}:\\d{2}/) && text.includes('₹')) {
                                return text;
                            }
                            current = current.parentElement;
                        }
                        return (el.innerText || '');
                    }
                """)
                
                # Extract times
                times = re.findall(r'\b(\d{1,2}):(\d{2})\b', container_text)
                dep_time = f"{times[0][0]}:{times[0][1]}" if len(times) >= 1 else 'N/A'
                arr_time = f"{times[1][0]}:{times[1][1]}" if len(times) >= 2 else 'N/A'
                
                # Create unique key
                unique_key = f"{flight_num}_{dep_time}_{arr_time}"
                if unique_key in seen_flights:
                    continue
                seen_flights.add(unique_key)
                
                # Extract duration
                dur_match = re.search(r'(\d+)\s*h\s*(\d+)\s*m', container_text, re.IGNORECASE)
                duration = f"{dur_match.group(1)}h {dur_match.group(2)}m" if dur_match else 'N/A'
                
                flight = {
                    'airline': 'SpiceJet',
                    'flight_number': flight_num,
                    'departure_time': dep_time,
                    'arrival_time': arr_time,
                    'duration': duration,
                    'price_inr': 'N/A',
                    'award_points': 'N/A',
                    'spicesaver_price': 'N/A',
                    'spiceflex_price': 'N/A',
                    'spicemax_price': 'N/A',
                    'spicesaver_points': 'N/A',
                    'spiceflex_points': 'N/A',
                    'spicemax_points': 'N/A'
                }
                
                # Extract prices and points for each fare type using exact data-testid
                fare_configs = [
                    ('spicesaver', 'spicesaver-flight-select-radio-button-0'),
                    ('spiceflex', 'spiceflex-flight-select-radio-button-1'),
                    ('spicemax', 'spicemax-flight-select-radio-button-2')
                ]
                
                for fare_key, exact_testid in fare_configs:
                    try:
                        # Find button with exact testid
                        fare_button = bundle.query_selector(f"[data-testid='{exact_testid}']")
                        
                        if fare_button:
                            # Get price and points from the fare button's parent container
                            fare_data = fare_button.evaluate("""
                                el => {
                                    let current = el.parentElement;
                                    for (let i = 0; i < 10 && current; i++) {
                                        let text = current.innerText || '';
                                        if (text.includes('₹') && text.includes('Earn')) {
                                            // Find price element
                                            let priceElem = current.querySelector('[class*="1i10wst"], [id*="selected-onward"]');
                                            // Find points element
                                            let pointsElem = current.querySelector('[class*="1gkfh8e"]');
                                            
                                            return {
                                                text: text,
                                                price: priceElem ? (priceElem.innerText || '') : '',
                                                points: pointsElem ? (pointsElem.innerText || '') : ''
                                            };
                                        }
                                        current = current.parentElement;
                                    }
                                    return {text: '', price: '', points: ''};
                                }
                            """)
                            
                            if fare_data:
                                # Extract price
                                if fare_data.get('price'):
                                    price_text = fare_data['price']
                                    price_match = re.search(r'₹\s*([\d,]+)', price_text)
                                    if not price_match:
                                        price_match = re.search(r'([\d,]+)', price_text)
                                    if price_match:
                                        price = f"₹{price_match.group(1)}"
                                        if flight[f'{fare_key}_price'] == 'N/A':
                                            flight[f'{fare_key}_price'] = price
                                        if fare_key == 'spicesaver' and flight['price_inr'] == 'N/A':
                                            flight['price_inr'] = price
                                
                                # Extract points - capture full number (4 digits)
                                if fare_data.get('points'):
                                    points_text = fare_data['points']
                                    # Match "Earn" followed by 1-4 digits (with optional commas)
                                    points_match = re.search(r'Earn\s*(\d{1,4}(?:,\d{3})*)', points_text, re.IGNORECASE)
                                    if points_match:
                                        points_value = points_match.group(1).replace(',', '')
                                        if flight[f'{fare_key}_points'] == 'N/A':
                                            flight[f'{fare_key}_points'] = points_value
                                
                                # Fallback: extract from text
                                if (flight[f'{fare_key}_price'] == 'N/A' or flight[f'{fare_key}_points'] == 'N/A') and fare_data.get('text'):
                                    text = fare_data['text']
                                    if flight[f'{fare_key}_price'] == 'N/A':
                                        price_match = re.search(r'₹\s*([\d,]+)', text)
                                        if price_match:
                                            flight[f'{fare_key}_price'] = f"₹{price_match.group(1)}"
                                            if fare_key == 'spicesaver' and flight['price_inr'] == 'N/A':
                                                flight['price_inr'] = f"₹{price_match.group(1)}"
                                    
                                    if flight[f'{fare_key}_points'] == 'N/A':
                                        points_match = re.search(r'Earn\s*(\d{1,4}(?:,\d{3})*)', text, re.IGNORECASE)
                                        if points_match:
                                            flight[f'{fare_key}_points'] = points_match.group(1).replace(',', '')
                    except Exception as e:
                        pass
                
                flights.append(flight)
                print(f"  Extracted: {flight_num} | Saver: {flight['spicesaver_price']}, Flex: {flight['spiceflex_price']}, Max: {flight['spicemax_price']} | Points: {flight['spicesaver_points']}/{flight['spiceflex_points']}/{flight['spicemax_points']}")
                
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()
    
    return flights

