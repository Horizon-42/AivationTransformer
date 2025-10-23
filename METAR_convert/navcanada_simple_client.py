"""
Simple Nav Canada Weather Client

Optimized version that organizes data by type and station:
- METAR/TAF/NOTAM grouped by station
- Upper Wind as a list (covers multiple stations)
- Easy to parse and work with
"""

import json
import re
import stat
import subprocess
import sys
import time
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
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class NavCanadaSimpleClient:
    """
    Simple Nav Canada Weather Data Client
    
    Outputs optimized structure:
    - METAR/TAF/NOTAM grouped by station
    - Upper Wind as a list
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
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        chrome_options.add_argument("--remote-debugging-port=0")
        
        try:
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            print("✅ Simple client ready")
            return True

        except WebDriverException as exc:
            print(f"⚠️  Selenium Manager driver resolution failed: {exc}")
            try:
                driver_path = ChromeDriverManager().install()
                self._prepare_chromedriver_binary(driver_path)
                service = Service(driver_path)
                self.driver = webdriver.Chrome(
                    service=service, options=chrome_options)
                self.driver.set_page_load_timeout(self.timeout)
                print("✅ Simple client ready via webdriver-manager fallback")
                return True
            except Exception as second_exc:
                print(f"❌ Client setup failed after fallback: {second_exc}")
                return False
        except Exception as e:
            print(f"❌ Client setup failed: {e}")
            return False

    def _prepare_chromedriver_binary(self, driver_path: str) -> None:
        """Ensure the downloaded ChromeDriver binary can execute, especially on macOS."""
        if not driver_path:
            return

        path_obj = Path(driver_path)
        if not path_obj.exists():
            return

        # Guarantee execute permissions
        try:
            current_mode = path_obj.stat().st_mode
            path_obj.chmod(current_mode | stat.S_IXUSR |
                           stat.S_IXGRP | stat.S_IXOTH)
        except Exception as chmod_exc:
            print(
                f"⚠️  Unable to adjust chromedriver permissions: {chmod_exc}")

        # macOS quarantine flag blocks execution of downloaded binaries
        if sys.platform == "darwin":
            try:
                subprocess.run(
                    ["xattr", "-dr", "com.apple.quarantine", str(path_obj)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                # xattr not available; ignore
                pass

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
        """Extract results in optimized structure grouped by type and station"""
        print("📊 Extracting weather data...")
        
        # Optimized structure
        organized_data = {
            "METAR": {},
            "TAF": {},
            "Upper_Wind": [],
            # New: station-wise upper wind view for easier consumption
            "Upper_Wind_By_Station": {},
            "NOTAM": {}
        }
        
        try:
            # Wait for results to load
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
                return self._extract_alternative(station_codes, organized_data)
            
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
                    
                    if not metadata_text or not bulletin_text:
                        continue

                    # Create entry
                    entry = {
                        'bulletin': bulletin_text,
                        'row_index': i,
                        'extraction_time': datetime.now(timezone.utc).isoformat()
                    }

                    # Categorize by type and station
                    if "METAR" in metadata_text:
                        station_match = re.search(
                            r"METAR\s*\n?([A-Z]{4})", metadata_text)
                        station = station_match.group(
                            1) if station_match else "Unknown"
                        organized_data["METAR"].setdefault(
                            station, []).append(entry)
                        entry_count += 1

                    elif "TAF" in metadata_text:
                        station_match = re.search(
                            r"TAF\s*\n?([A-Z]{4})", metadata_text)
                        station = station_match.group(
                            1) if station_match else "Unknown"
                        organized_data["TAF"].setdefault(
                            station, []).append(entry)
                        entry_count += 1
                        
                    elif "Upper Wind" in metadata_text or "UPPER WIND" in metadata_text.upper():
                        # Post-process Upper Wind: split by VALID blocks and fix station codes (add leading 'C')
                        split_bulletins = self._split_upper_wind_bulletin_and_fix_codes(
                            bulletin_text)
                        for _bw in split_bulletins:
                            # Backward-compatible full bulletin list
                            organized_data["Upper_Wind"].append({
                                'bulletin': _bw,
                                'row_index': i,
                                'extraction_time': entry['extraction_time']
                            })
                            # New: populate station-wise trimmed versions
                            for stn in self._station_codes_in_upper_wind_block(_bw):
                                trimmed = self._trim_upper_wind_block_for_station(
                                    _bw, stn)
                                if trimmed:
                                    organized_data["Upper_Wind_By_Station"].setdefault(stn, []).append({
                                        'bulletin': trimmed,
                                        'row_index': i,
                                        'extraction_time': entry['extraction_time']
                                    })
                        entry_count += len(split_bulletins)
                        
                    elif "NOTAM" in metadata_text:
                        station_match = re.search(
                            r"NOTAM\s*\n?([A-Z]{4})", metadata_text)
                        station = station_match.group(
                            1) if station_match else "Other"
                        organized_data["NOTAM"].setdefault(
                            station, []).append(entry)
                        entry_count += 1
                
                except Exception as e:
                    print(f"⚠️ Error processing row {i}: {e}")
                    continue

            print(f"✅ Extracted {entry_count} entries")
            
            if entry_count == 0:
                print("⚠️ No data extracted - trying pre-formatted text extraction")
                return self._extract_pre_text(station_codes, organized_data)
            
            return organized_data
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return organized_data
    
    def _extract_alternative(self, station_codes: List[str], organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Alternative extraction method - look for pre-formatted text blocks"""
        print("🔄 Trying alternative extraction...")
        
        try:
            # Look for pre-formatted text elements
            pre_elements = self.driver.find_elements(By.TAG_NAME, "pre")
            
            entry_count = 0
            for i, pre in enumerate(pre_elements):
                text = pre.text.strip()
                if not text:
                    continue

                entry = {
                    'bulletin': text,
                    'row_index': i,
                    'extraction_time': datetime.now(timezone.utc).isoformat()
                }

                # Categorize based on content
                if "METAR" in text:
                    station_match = re.search(r"METAR\s+([A-Z]{4})", text)
                    station = station_match.group(
                        1) if station_match else "Unknown"
                    organized_data["METAR"].setdefault(
                        station, []).append(entry)
                    entry_count += 1
                    
                elif "TAF" in text:
                    station_match = re.search(r"TAF\s+([A-Z]{4})", text)
                    station = station_match.group(
                        1) if station_match else "Unknown"
                    organized_data["TAF"].setdefault(station, []).append(entry)
                    entry_count += 1

                elif "VALID" in text and any(alt in text for alt in ['3000', '6000', '9000']):
                    # Split by VALID blocks and fix station codes (add leading 'C') even in raw data
                    split_bulletins = self._split_upper_wind_bulletin_and_fix_codes(
                        text)
                    for _bw in split_bulletins:
                        # Backward-compatible full bulletin list
                        organized_data["Upper_Wind"].append({
                            'bulletin': _bw,
                            'row_index': i,
                            'extraction_time': entry['extraction_time']
                        })
                        # New: station-wise trimmed versions
                        for stn in self._station_codes_in_upper_wind_block(_bw):
                            trimmed = self._trim_upper_wind_block_for_station(
                                _bw, stn)
                            if trimmed:
                                organized_data["Upper_Wind_By_Station"].setdefault(stn, []).append({
                                    'bulletin': trimmed,
                                    'row_index': i,
                                    'extraction_time': entry['extraction_time']
                                })
                    entry_count += len(split_bulletins)

                elif "NOTAM" in text:
                    station_match = re.search(
                        r"\(([A-Z]\d+/\d+).*A\)\s+([A-Z]{4})", text)
                    station = station_match.group(
                        2) if station_match else "Other"
                    organized_data["NOTAM"].setdefault(
                        station, []).append(entry)
                    entry_count += 1

            print(f"✅ Alternative extraction found {entry_count} entries")
            
        except Exception as e:
            print(f"❌ Alternative extraction failed: {e}")
        
        return organized_data
    
    def _extract_pre_text(self, station_codes: List[str], organized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from pre-formatted text elements"""
        return self._extract_alternative(station_codes, organized_data)

    def _split_upper_wind_bulletin_and_fix_codes(self, text: str) -> List[str]:
        """Split an Upper Wind bulletin into individual VALID blocks and prefix 'C' to 3-letter station codes.

        The Nav Canada Upper Wind table uses 3-letter identifiers (e.g., YVR, YYZ). For ICAO consistency,
        we convert leading 3-letter station codes on each data row to their 4-letter Canadian ICAO form by
        prefixing 'C' (e.g., YVR -> CYVR). We also split multi-period bulletins into one block per VALID ... FOR USE ... section.
        """
        if not text:
            return []

        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Find each VALID ... FOR USE ... block (non-greedy up to next VALID or end)
        pattern = re.compile(
            r"^VALID\s+\d{6}Z\s+FOR\s+USE\s+[\d\-]+[\s\S]*?(?=^VALID\s+\d{6}Z\s+FOR\s+USE\s+[\d\-]+|\Z)", re.MULTILINE)
        blocks = [m.group(0) for m in pattern.finditer(text)]

        if not blocks:
            # If no clear split, treat the whole text as one block
            blocks = [text]

        fixed_blocks: List[str] = []
        for block in blocks:
            lines = block.split('\n')
            fixed_lines: List[str] = []
            for line in lines:
                # Only modify lines that start with a station code. If already 4 letters at start, keep.
                m4 = re.match(r"^(\s*)([A-Z]{4})(\b.*)$", line)
                if m4:
                    fixed_lines.append(line)
                    continue

                m3 = re.match(r"^(\s*)([A-Z]{3})(\b\s+.*)$", line)
                if m3:
                    # Avoid matching the altitude header or non-station rows; they won't match this pattern anyway.
                    prefix, code3, rest = m3.groups()
                    # Prefix with 'C' to form ICAO station code
                    fixed_lines.append(f"{prefix}C{code3}{rest}")
                else:
                    fixed_lines.append(line)

            fixed_blocks.append("\n".join(fixed_lines).strip())

        return fixed_blocks

    def _station_codes_in_upper_wind_block(self, block: str) -> List[str]:
        """Identify 4-letter station codes present at the start of lines in a block."""
        stations: List[str] = []
        for line in block.split('\n'):
            m = re.match(r"^\s*([A-Z]{4})\b", line)
            if m:
                stn = m.group(1)
                if stn not in stations:
                    stations.append(stn)
        return stations

    def _trim_upper_wind_block_for_station(self, block: str, station: str) -> str:
        """Return header + altitude lines + only the given station row (and its wrapped continuation if present)."""
        if not block:
            return ""
        lines = block.split('\n')
        out_lines: List[str] = []

        # Header line
        if lines and lines[0].strip().startswith('VALID'):
            out_lines.append(lines[0])

        # Altitude header line(s): numbers and subsequent '|' continuation lines
        i = 1
        while i < len(lines):
            line = lines[i]
            if re.match(r"^\s*\d{4,5}", line) or re.match(r"^\s*\|", line):
                out_lines.append(line)
                i += 1
                while i < len(lines) and re.match(r"^\s*\|", lines[i]):
                    out_lines.append(lines[i])
                    i += 1
                break
            i += 1

        # Station row (and one possible wrapped continuation)
        for j in range(i, len(lines)):
            line = lines[j]
            if re.match(rf"^\s*{station}\b", line):
                out_lines.append(line)
                if j + 1 < len(lines) and not re.match(r"^\s*([A-Z]{4})\b|^VALID|^\s*\d{4,5}|^\s*\|", lines[j+1]):
                    out_lines.append(lines[j+1])
                break

        return "\n".join(out_lines).strip()
    
    def get_simple_weather_data(self, station_codes: List[str]) -> Dict[str, Any]:
        """Main method - get weather data in optimized structure"""
        print(f"\n{'='*60}")
        print(f"🌤️  OPTIMIZED NAV CANADA EXTRACTION")
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
            
            # Extract in optimized structure
            weather_data = self.extract_simple_results(station_codes)

            # Calculate summary
            metar_count = sum(len(v) for v in weather_data["METAR"].values())
            taf_count = sum(len(v) for v in weather_data["TAF"].values())
            notam_count = sum(len(v) for v in weather_data["NOTAM"].values())
            upper_wind_count = len(weather_data["Upper_Wind"])
            total_entries = metar_count + taf_count + notam_count + upper_wind_count

            # Get all stations found
            stations_found = set()
            stations_found.update(weather_data["METAR"].keys())
            stations_found.update(weather_data["TAF"].keys())
            for station in weather_data["NOTAM"].keys():
                if station != "Other":
                    stations_found.add(station)

            results = {
                'session_info': {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'stations_requested': station_codes,
                    'source': 'Nav Canada Weather Recall',
                    'extraction_method': 'optimized_structure'
                },
                'weather_data': weather_data,
                'extraction_summary': {
                    'total_entries': total_entries,
                    'metar_records': metar_count,
                    'taf_records': taf_count,
                    'notam_records': notam_count,
                    'upper_wind_records': upper_wind_count,
                    'stations_found': sorted(list(stations_found)),
                    'extraction_time': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Cleanup
            self.cleanup()
            
            return results
            
        except Exception as e:
            error_msg = f"Optimized extraction failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.cleanup()
            return {'error': error_msg}
    
    def save_simple_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """Save optimized data structure to JSON file"""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"navcanada_optimized_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Optimized data saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Save failed: {str(e)}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as exc:
                print(f"⚠️  Driver shutdown warning: {exc}")
            else:
                print("✅ Simple client closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def main():
    """Simple extraction example with optimized structure"""
    print("🌤️  Nav Canada Simple Weather Client")
    print("=" * 50)
    print("Optimized structure: METAR/TAF/NOTAM by station, Upper Wind as list")
    print("=" * 50)
    
    # Test with Vancouver and Calgary
    test_stations = ['CYVR', 'CYYC']
    
    with NavCanadaSimpleClient(headless=False) as client:
        # Get optimized data
        results = client.get_simple_weather_data(test_stations)
        
        if 'error' not in results:
            summary = results['extraction_summary']
            weather_data = results['weather_data']

            print(f"\n✅ Optimized extraction complete!")
            print(f"  • Total entries: {summary['total_entries']}")
            print(
                f"  • METAR records: {summary['metar_records']} (stations: {list(weather_data['METAR'].keys())})")
            print(
                f"  • TAF records: {summary['taf_records']} (stations: {list(weather_data['TAF'].keys())})")
            print(
                f"  • NOTAM records: {summary['notam_records']} (categories: {list(weather_data['NOTAM'].keys())})")
            print(f"  • Upper Wind records: {summary['upper_wind_records']}")
            print(f"  • Stations found: {', '.join(summary['stations_found'])}")
            
            # Save data
            filename = client.save_simple_data(results)
            
            if filename:
                print(f"\n📄 Optimized dataset saved to: {filename}")
                print("🔍 Structure: Type -> Station -> [Bulletins]")
        else:
            print(f"❌ Error: {results['error']}")


if __name__ == "__main__":
    main()