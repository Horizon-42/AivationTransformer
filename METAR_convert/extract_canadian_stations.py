"""
Extract Canadian Weather Stations from UCAR Stations Database

This script reads the UCAR stations database and extracts all Canadian stations
(ICAO codes starting with 'C' and country code 'CA'), preserving their complete
information including coordinates, elevation, and station type.

Output: A filtered file containing only Canadian stations with all metadata.
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Optional


class CanadianStationExtractor:
    """Extract and filter Canadian stations from UCAR stations database"""
    
    def __init__(self, input_file: str, output_txt: str = "canadian_stations.txt", 
                 output_csv: str = "canadian_stations.csv"):
        """
        Initialize the extractor
        
        Args:
            input_file: Path to the UCAR stations database file
            output_txt: Path to output text file for Canadian stations
            output_csv: Path to output CSV file for Canadian stations
        """
        self.input_file = Path(input_file)
        self.output_txt = Path(output_txt)
        self.output_csv = Path(output_csv)
        self.stations: List[str] = []
        self.stations_parsed: List[Dict[str, str]] = []
        self.header_lines: List[str] = []
        
    def extract(self) -> None:
        """Extract Canadian stations from the database"""
        print(f"📖 Reading stations from: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Pattern to match Canadian stations: ICAO starting with C and ending with CA
        # Format: CD  STATION         ICAO  IATA  SYNOP   LAT     LONG   ELEV   M  N  V  U  A  C
        canada_pattern = re.compile(r'^[A-Z]{2}\s+.*\s+C[A-Z0-9]{3}\s+.*\s+CA\s*$')
        
        in_header = True
        for line in lines:
            # Capture header and comments
            if line.startswith('!') or line.startswith('CD  STATION') or line.strip() == '':
                if in_header:
                    self.header_lines.append(line)
                continue
            
            # Check if this is a Canadian station
            if canada_pattern.match(line):
                self.stations.append(line)
                self._parse_station_line(line)
                in_header = False
        
        print(f"✅ Found {len(self.stations)} Canadian stations")
    
    def _parse_station_line(self, line: str) -> None:
        """Parse a station line into structured data
        
        Format: CD  STATION         ICAO  IATA  SYNOP   LAT     LONG   ELEV   M  N  V  U  A  C
        Example: AB CALGARY INTNL AR CYYC  YYC   71877  51 07N  114 01W 1084   X     T          0 CA
        Columns:
        - M = METAR (X=has METAR, Z=obsolete)
        - N = NEXRAD (X=has NEXRAD)
        - V = Aviation flags (T=TAF, V=AIRMET/SIGMET, A=ARTCC, U=T+V)
        - U = Upper air (X=rawinsonde, W=wind profiler, Z=military)
        - A = Auto (A=ASOS, W=AWOS, M=Meso, H=Human, G=Augmented)
        - C = Office type (F=WFO, R=RFC, C=NCEP Center)
        """
        # Parse fixed-width columns based on actual format
        province = line[0:2].strip()
        station = line[3:19].strip()
        icao = line[20:24].strip()
        iata = line[26:29].strip()
        synop = line[31:36].strip()
        lat = line[37:44].strip()
        lon = line[46:54].strip()
        elev = line[56:60].strip()
        
        # Parse flag columns - based on actual format analysis
        # Example: "1084   X     T          0 CA"
        #           pos: 60  62 63 64 65 66 67 68 69 70...
        # Flags appear at: M=62, N=~65, V=68, U=~71, A=~74, C=~77
        metar_flag = line[62:63].strip() if len(line) > 62 else ''
        nexrad_flag = line[65:66].strip() if len(line) > 65 else ''
        aviation_flag = line[68:69].strip() if len(line) > 68 else ''
        upper_air_flag = line[71:72].strip() if len(line) > 71 else ''
        auto_flag = line[74:75].strip() if len(line) > 74 else ''
        office_flag = line[77:78].strip() if len(line) > 77 else ''
        
        # Map flags to descriptive values
        metar_map = {'X': 'Yes', 'Z': 'Obsolete'}
        nexrad_map = {'X': 'Yes'}
        aviation_map = {'T': 'TAF', 'V': 'AIRMET/SIGMET',
                        'A': 'ARTCC', 'U': 'TAF+AIRMET/SIGMET'}
        upper_air_map = {'X': 'Rawinsonde',
                         'W': 'Wind Profiler', 'Z': 'Military', 'T': 'TAF'}
        auto_map = {'A': 'ASOS', 'W': 'AWOS',
                    'M': 'Meso', 'H': 'Human', 'G': 'Augmented'}
        office_map = {'F': 'WFO', 'R': 'RFC', 'C': 'NCEP Center'}
        
        self.stations_parsed.append({
            'province': province,
            'station_name': station,
            'icao': icao,
            'iata': iata,
            'synop': synop,
            'latitude': lat,
            'longitude': lon,
            'elevation_m': elev,
            'metar': metar_map.get(metar_flag, ''),
            'nexrad': nexrad_map.get(nexrad_flag, ''),
            'aviation': aviation_map.get(aviation_flag, ''),
            'upper_air': upper_air_map.get(upper_air_flag, ''),
            'auto_type': auto_map.get(auto_flag, ''),
            'office_type': office_map.get(office_flag, ''),
            'country': 'CA'
        })
        
    def save(self) -> None:
        """Save Canadian stations to output files (both TXT and CSV)"""
        self._save_txt()
        self._save_csv()
    
    def _save_txt(self) -> None:
        """Save Canadian stations to text file"""
        print(f"💾 Saving Canadian stations to: {self.output_txt}")
        
        with open(self.output_txt, 'w', encoding='utf-8') as f:
            # Write header
            f.write("! Canadian Weather Stations Database\n")
            f.write("! Extracted from UCAR Stations Database\n")
            f.write("! Contains all weather stations in Canada (ICAO codes starting with 'C')\n")
            f.write("!\n")
            
            # Write column headers from original file
            for line in self.header_lines:
                if line.startswith('CD  STATION'):
                    f.write(line)
                    break
            
            # Write all Canadian stations
            f.writelines(self.stations)
        
        print(f"✅ Saved {len(self.stations)} stations to {self.output_txt}")
    
    def _save_csv(self) -> None:
        """Save Canadian stations to CSV file"""
        print(f"💾 Saving Canadian stations to: {self.output_csv}")
        
        if not self.stations_parsed:
            print("⚠️ No parsed stations available")
            return
        
        # CSV column headers
        fieldnames = [
            'province',
            'station_name',
            'icao',
            'iata',
            'synop',
            'latitude',
            'longitude',
            'elevation_m',
            'metar',
            'nexrad',
            'aviation',
            'upper_air',
            'auto_type',
            'office_type',
            'country'
        ]
        
        with open(self.output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.stations_parsed)
        
        print(f"✅ Saved {len(self.stations_parsed)} stations to {self.output_csv}")
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about extracted stations"""
        if not self.stations:
            return {}
        
        # Count by province (first 2 characters)
        provinces = {}
        icao_codes = []
        has_metar = 0
        has_taf = 0
        has_upper_air = 0
        
        for station in self.stations:
            parts = station.split()
            if len(parts) >= 3:
                province = parts[0]
                icao = parts[2]
                
                provinces[province] = provinces.get(province, 0) + 1
                if icao and icao.startswith('C'):
                    icao_codes.append(icao)
                
                # Check for METAR (M in column)
                if 'X' in station[60:70]:  # Approximate position of M flag
                    has_metar += 1
                
                # Check for TAF (T in V column)
                if 'T' in station[70:80]:  # Approximate position of V column
                    has_taf += 1
                
                # Check for upper air (X in U column)
                if 'X' in station[76:82]:  # Approximate position of U column
                    has_upper_air += 1
        
        return {
            'total_stations': len(self.stations),
            'provinces': provinces,
            'unique_icao_codes': len(set(icao_codes)),
            'metar_stations': has_metar,
            'taf_stations': has_taf,
            'upper_air_stations': has_upper_air
        }
    
    def print_statistics(self) -> None:
        """Print statistics about extracted stations"""
        stats = self.get_statistics()
        
        if not stats:
            print("⚠️ No statistics available. Run extract() first.")
            return
        
        print(f"\n{'='*70}")
        print("📊 CANADIAN STATIONS STATISTICS")
        print(f"{'='*70}")
        print(f"\n📍 Total Stations: {stats['total_stations']}")
        print(f"🔤 Unique ICAO Codes: {stats['unique_icao_codes']}")
        print(f"\n🌤️  Station Types:")
        print(f"   • METAR Reporting: {stats['metar_stations']}")
        print(f"   • TAF Forecasts: {stats['taf_stations']}")
        print(f"   • Upper Air: {stats['upper_air_stations']}")
        
        print(f"\n🗺️  Stations by Province/Territory:")
        for province, count in sorted(stats['provinces'].items()):
            print(f"   • {province}: {count} stations")
        
        print(f"\n{'='*70}\n")


def main():
    """Main execution function"""
    print("🇨🇦 Canadian Weather Stations Extractor")
    print("=" * 70)
    
    # Input file path (relative to script location)
    script_dir = Path(__file__).parent
    input_file = script_dir.parent / "data" / "stations_ucar.txt"
    output_txt = script_dir / "canadian_stations.txt"
    output_csv = script_dir / "canadian_stations.csv"
    
    # Check if input file exists
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return
    
    # Create extractor and run
    extractor = CanadianStationExtractor(str(input_file), str(output_txt), str(output_csv))
    
    try:
        # Extract stations
        extractor.extract()
        
        # Show statistics
        extractor.print_statistics()
        
        # Save to files (both TXT and CSV)
        extractor.save()
        
        print("✅ Extraction complete!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
