"""
Station Lookup Module

Provides station metadata (coordinates, elevation, names) from the Canadian stations database.
This enriches METAR/TAF/Upper Wind data with proper geographic information.
"""

import csv
from pathlib import Path
from typing import Dict, Optional, Tuple
import re


class StationDatabase:
    """
    Station metadata database for Canadian aviation weather stations.
    Loads from canadian_stations.csv and provides lookup by ICAO code.
    """
    
    def __init__(self, csv_path: str = None):
        """
        Initialize station database.
        
        Args:
            csv_path: Path to canadian_stations.csv. If None, uses default location.
        """
        if csv_path is None:
            # Default to database/canadian_stations.csv relative to this file
            csv_path = Path(__file__).parent / "database" / "canadian_stations.csv"
        
        self.csv_path = Path(csv_path)
        self.stations: Dict[str, dict] = {}
        self._load_stations()
    
    def _load_stations(self):
        """Load station data from CSV file."""
        if not self.csv_path.exists():
            print(f"⚠️  Warning: Station database not found at {self.csv_path}")
            print(f"   Station coordinates will default to 0.0, 0.0")
            return
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                icao = row.get('icao', '').strip()
                if not icao:
                    continue
                
                # Parse latitude: "72 40" or "72 40N" -> 72.667
                lat_str = row.get('latitude', '0 0').strip()
                latitude = self._parse_coordinate(lat_str, is_latitude=True)
                
                # Parse longitude: "077 58W" -> -77.967
                lon_str = row.get('longitude', '0 0').strip()
                longitude = self._parse_coordinate(lon_str, is_latitude=False)
                
                # Parse elevation
                try:
                    elevation = int(row.get('elevation_m', '0'))
                except (ValueError, TypeError):
                    elevation = 0
                
                self.stations[icao] = {
                    'icao': icao,
                    'name': row.get('station_name', f'Station {icao}').strip(),
                    'iata': row.get('iata', '').strip(),
                    'province': row.get('province', '').strip(),
                    'latitude': latitude,
                    'longitude': longitude,
                    'elevation_m': elevation,
                    'has_metar': row.get('metar', '').strip().lower() == 'yes',
                    'has_taf': row.get('aviation', '').strip() == 'TAF',
                    'has_upper_air': row.get('upper_air', '').strip() != '',
                }
        
        print(f"✅ Loaded {len(self.stations)} stations from database")
    
    def _parse_coordinate(self, coord_str: str, is_latitude: bool) -> float:
        """
        Parse coordinate string to decimal degrees.
        
        Format examples:
        - "72 40" or "72 40N" -> 72.667
        - "077 58W" -> -77.967
        
        Args:
            coord_str: Coordinate string from CSV
            is_latitude: True for latitude, False for longitude
            
        Returns:
            Decimal degrees (negative for South/West)
        """
        coord_str = coord_str.strip()
        
        # Extract direction (N/S/E/W)
        direction = None
        if coord_str.endswith(('N', 'S', 'E', 'W')):
            direction = coord_str[-1]
            coord_str = coord_str[:-1].strip()
        
        # Parse degrees and minutes
        parts = coord_str.split()
        if len(parts) < 2:
            return 0.0
        
        try:
            degrees = int(parts[0])
            minutes = int(parts[1])
            
            # Convert to decimal degrees
            decimal = degrees + (minutes / 60.0)
            
            # Apply direction
            if direction:
                if direction in ('S', 'W'):
                    decimal = -decimal
            else:
                # If no direction, assume West for longitude in Canada
                if not is_latitude:
                    decimal = -decimal
            
            return round(decimal, 4)
        
        except (ValueError, IndexError):
            return 0.0
    
    def lookup(self, icao: str) -> Optional[dict]:
        """
        Look up station by ICAO code.
        
        Args:
            icao: ICAO station code (e.g., 'CYIO')
            
        Returns:
            Station dict with keys: icao, name, latitude, longitude, elevation_m
            Returns None if station not found.
        """
        return self.stations.get(icao.upper())
    
    def get_coordinates(self, icao: str) -> Tuple[float, float, int]:
        """
        Get coordinates and elevation for a station.
        
        Args:
            icao: ICAO station code
            
        Returns:
            Tuple of (latitude, longitude, elevation_meters)
            Returns (0.0, 0.0, 0) if station not found.
        """
        station = self.lookup(icao)
        if station:
            return (station['latitude'], station['longitude'], station['elevation_m'])
        return (0.0, 0.0, 0)
    
    def get_name(self, icao: str) -> str:
        """
        Get full station name.
        
        Args:
            icao: ICAO station code
            
        Returns:
            Station name, or "Station {icao}" if not found
        """
        station = self.lookup(icao)
        if station:
            return station['name']
        return f"Station {icao}"
    
    def enrich_metar(self, metar_obj):
        """
        Enrich METAR object with station metadata.
        Updates latitude, longitude, elevation, and station_name in place.
        
        Args:
            metar_obj: METAR object to enrich
        """
        station = self.lookup(metar_obj.station_id)
        if station:
            metar_obj.latitude = station['latitude']
            metar_obj.longitude = station['longitude']
            metar_obj.elevation_meters = station['elevation_m']
            metar_obj.station_name = station['name']
    
    def enrich_taf(self, taf_obj):
        """
        Enrich TAF object with station metadata.
        Updates latitude, longitude, elevation, and station_name in place.
        
        Args:
            taf_obj: TAF object to enrich
        """
        station = self.lookup(taf_obj.station_id)
        if station:
            taf_obj.latitude = station['latitude']
            taf_obj.longitude = station['longitude']
            taf_obj.elevation_meters = station['elevation_m']
            taf_obj.station_name = station['name']
    
    def enrich_upper_wind(self, upper_wind_obj):
        """
        Enrich UpperWind object with station metadata.
        Only sets station_name and elevation_m (no latitude/longitude).
        
        Args:
            upper_wind_obj: UpperWind object to enrich
        """
        station = self.lookup(upper_wind_obj.station)
        if station:
            upper_wind_obj.elevation_m = station['elevation_m']
            upper_wind_obj.station_name = station['name']


# Global instance for easy access
_global_db = None

def get_station_database() -> StationDatabase:
    """
    Get the global station database instance.
    Creates it on first access.
    
    Returns:
        StationDatabase instance
    """
    global _global_db
    if _global_db is None:
        _global_db = StationDatabase()
    return _global_db


def enrich_weather_data(metars_dict, tafs_dict, upper_winds_list):
    """
    Enrich all weather data with station metadata.
    
    Args:
        metars_dict: Dict of station_id -> List[METAR]
        tafs_dict: Dict of station_id -> List[TAF]
        upper_winds_list: List[UpperWind]
    """
    db = get_station_database()
    
    # Enrich METARs
    enriched_metar_count = 0
    for station_id, metars in metars_dict.items():
        for metar in metars:
            db.enrich_metar(metar)
            if metar.latitude != 0.0 or metar.longitude != 0.0:
                enriched_metar_count += 1

    # Enrich TAFs
    enriched_taf_count = 0
    for station_id, tafs in tafs_dict.items():
        for taf in tafs:
            db.enrich_taf(taf)
            if taf.latitude != 0.0 or taf.longitude != 0.0:
                enriched_taf_count += 1

    # No enrichment for Upper Winds
    total_enriched = enriched_metar_count + enriched_taf_count
    if total_enriched > 0:
        print(f"📍 Enriched {total_enriched} weather records with station coordinates")
        print(f"   METARs: {enriched_metar_count}, TAFs: {enriched_taf_count}")


if __name__ == '__main__':
    # Test the station database
    db = StationDatabase()
    
    print("\n" + "="*60)
    print("Station Database Test")
    print("="*60)
    
    # Test some stations
    test_stations = ['CYIO', 'CYRT', 'CYRB', 'CYYH', 'CYTL', 'CYYC']
    
    for icao in test_stations:
        station = db.lookup(icao)
        if station:
            print(f"\n{icao}: {station['name']}")
            print(f"  Location: {station['latitude']:.4f}°, {station['longitude']:.4f}°")
            print(f"  Elevation: {station['elevation_m']}m")
            print(f"  Services: METAR={station['has_metar']}, TAF={station['has_taf']}, Upper Air={station['has_upper_air']}")
        else:
            print(f"\n{icao}: Not found")
    
    print("\n" + "="*60)
