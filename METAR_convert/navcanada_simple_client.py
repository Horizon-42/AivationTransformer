"""
Simple Nav Canada Weather Client

This is a simplified version that just extracts the search results as they appear:
- Metadata column content as keys
- Bulletin column content as values
- No complex parsing or data structure transformations
"""

import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class NavCanadaSimpleClient:
    """
    Simple Nav Canada Weather Data Client
    
    Extracts search results as plain text:
    - Metadata column -> key
    - Bulletin column -> value
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30, data_dir: str = "weather_data"):
        """Initialize the simple client"""
        self.base_url = "https://plan.navcanada.ca/wxrecall/"
        self.timeout = timeout
        self.driver = None
        self.headless = headless
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver"""
        print("🚀 Setting up simple Nav Canada client...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            print("✅ Simple client ready")
            return True
            
        except Exception as e:
            print(f"❌ Client setup failed: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to Nav Canada"""
        print(f"🌐 Connecting to: {self.base_url}")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "root"))
            )
            
            time.sleep(3)
            print(f"✅ Connected: {self.driver.title}")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def search_stations(self, station_codes: List[str]) -> bool:
        """Search for stations"""
        print(f"🔍 Searching for: {', '.join(station_codes)}")
        
        try:
            # Find search input
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Aerodrome' i]")
            
            if not search_input.is_displayed() or not search_input.is_enabled():
                print("❌ Search input not available")
                return False
            
            # Clear and enter stations
            search_input.clear()
            time.sleep(0.5)
            
            stations_string = " ".join([code.upper() for code in station_codes])
            search_input.send_keys(stations_string)
            print(f"✅ Entered: {stations_string}")
            time.sleep(1)
            
            # Search
            try:
                search_button = self.driver.find_element(By.CSS_SELECTOR, ".search-button, button[type='submit'], .btn-search")
                search_button.click()
                time.sleep(2)
                search_button.click()  # Double-click for reliability
                print("✅ Search executed (button)")
            except:
                search_input.send_keys(Keys.RETURN)
                time.sleep(2)
                search_input.send_keys(Keys.RETURN)  # Double-press
                print("✅ Search executed (Enter key)")
            
            # Wait for results
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def extract_simple_results(self, station_codes: List[str]) -> Dict[str, Any]:
        """Extract results as simple metadata-key/bulletin-value pairs"""
        print("📊 Extracting simple results...")
        
        results = {
            'session_info': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stations_requested': station_codes,
                'source': 'Nav Canada Weather Recall',
                'extraction_method': 'simple_metadata_bulletin'
            },
            'weather_data': {},
            'extraction_summary': {
                'total_entries': 0,
                'stations_found': [],
                'extraction_time': datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            # Wait for data to load
            time.sleep(3)
            
            # Find all result rows in the table
            # Look for common table selectors
            table_selectors = [
                "table tbody tr",
                ".table-row",
                ".result-row", 
                "[role='row']",
                "tr:has(td)",
                ".MuiTableRow-root"
            ]
            
            rows = []
            for selector in table_selectors:
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rows:
                        print(f"✅ Found {len(rows)} rows using selector: {selector}")
                        break
                except:
                    continue
            
            if not rows:
                print("❌ No table rows found - trying alternative extraction")
                return self._extract_alternative(station_codes, results)
            
            entry_count = 0
            
            for i, row in enumerate(rows):
                try:
                    # Get all cells in the row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 2:
                        continue
                    
                    # First cell is typically metadata, second is bulletin
                    metadata_cell = cells[0]
                    bulletin_cell = cells[1]
                    
                    metadata_text = metadata_cell.text.strip()
                    bulletin_text = bulletin_cell.text.strip()
                    
                    if metadata_text and bulletin_text:
                        # Use metadata as key (clean it up for JSON)
                        key = f"entry_{entry_count:03d}_{metadata_text[:50].replace(' ', '_').replace('/', '_')}"
                        
                        results['weather_data'][key] = {
                            'metadata': metadata_text,
                            'bulletin': bulletin_text,
                            'row_index': i,
                            'extraction_time': datetime.now(timezone.utc).isoformat()
                        }
                        
                        entry_count += 1
                        
                        # Check which station this belongs to
                        for station in station_codes:
                            if station.upper() in metadata_text.upper() or station.upper() in bulletin_text.upper():
                                if station not in results['extraction_summary']['stations_found']:
                                    results['extraction_summary']['stations_found'].append(station)
                                break
                
                except Exception as e:
                    print(f"⚠️ Error processing row {i}: {e}")
                    continue
            
            results['extraction_summary']['total_entries'] = entry_count
            print(f"✅ Extracted {entry_count} entries")
            
            if entry_count == 0:
                print("⚠️ No data extracted - trying pre-formatted text extraction")
                return self._extract_pre_text(station_codes, results)
            
            return results
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return results
    
    def _extract_alternative(self, station_codes: List[str], results: Dict[str, Any]) -> Dict[str, Any]:
        """Alternative extraction method - look for pre-formatted text blocks"""
        print("🔄 Trying alternative extraction...")
        
        try:
            # Look for pre-formatted text elements
            pre_elements = self.driver.find_elements(By.TAG_NAME, "pre")
            
            entry_count = 0
            for i, pre in enumerate(pre_elements):
                text = pre.text.strip()
                if text:
                    key = f"pre_text_{i:03d}"
                    
                    results['weather_data'][key] = {
                        'metadata': f"Pre-formatted text block {i+1}",
                        'bulletin': text,
                        'element_type': 'pre',
                        'extraction_time': datetime.now(timezone.utc).isoformat()
                    }
                    
                    entry_count += 1
                    
                    # Check station association
                    for station in station_codes:
                        if station.upper() in text.upper():
                            if station not in results['extraction_summary']['stations_found']:
                                results['extraction_summary']['stations_found'].append(station)
            
            results['extraction_summary']['total_entries'] = entry_count
            print(f"✅ Alternative extraction found {entry_count} entries")
            
        except Exception as e:
            print(f"❌ Alternative extraction failed: {e}")
        
        return results
    
    def _extract_pre_text(self, station_codes: List[str], results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from pre-formatted text elements"""
        return self._extract_alternative(station_codes, results)
    
    def get_simple_weather_data(self, station_codes: List[str]) -> Dict[str, Any]:
        """Main method - get simple weather data"""
        print(f"\n{'='*60}")
        print(f"🌤️  SIMPLE NAV CANADA EXTRACTION")
        print(f"📍 Stations: {', '.join(station_codes)}")
        print('='*60)
        
        try:
            # Setup if needed
            if not self.driver:
                if not self.setup_driver():
                    return {'error': 'Failed to setup driver'}
                
                if not self.connect():
                    return {'error': 'Failed to connect'}
            
            # Search
            if not self.search_stations(station_codes):
                return {'error': 'Search failed'}
            
            # Extract
            results = self.extract_simple_results(station_codes)
            
            # Cleanup
            self.cleanup()
            
            return results
            
        except Exception as e:
            error_msg = f"Simple extraction failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.cleanup()
            return {'error': error_msg}
    
    def save_simple_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """Save simple data to JSON file"""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"navcanada_simple_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Simple data saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Save failed: {str(e)}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
            print("✅ Simple client closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def main():
    """Simple extraction example"""
    print("🌤️  Nav Canada Simple Weather Client")
    print("=" * 50)
    print("Simple approach: Metadata -> Key, Bulletin -> Value")
    print("=" * 50)
    
    # Test with Vancouver
    test_stations = ['CYVR']
    
    with NavCanadaSimpleClient(headless=False) as client:
        # Get simple data
        results = client.get_simple_weather_data(test_stations)
        
        if 'error' not in results:
            summary = results['extraction_summary']
            print(f"\n✅ Simple extraction complete!")
            print(f"  • Total entries: {summary['total_entries']}")
            print(f"  • Stations found: {', '.join(summary['stations_found'])}")
            
            # Save data
            filename = client.save_simple_data(results)
            
            if filename:
                print(f"\n📄 Simple dataset saved to: {filename}")
                print("🔍 Structure: metadata -> key, bulletin -> value")
        else:
            print(f"❌ Error: {results['error']}")


if __name__ == "__main__":
    main()