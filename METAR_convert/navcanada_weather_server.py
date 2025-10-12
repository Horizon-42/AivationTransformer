"""
Nav Canada Weather Data Server

This module provides functionality to fetch METAR, TAF, and Upper Wind data 
from Nav Canada and return parsed objects.

Similar interface to weather_data_server but uses Nav Canada as the data source.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

from navcanada_simple_client import NavCanadaSimpleClient
from metar import METAR
from taf import TAF
from upper_wind import UpperWind


@dataclass
class NavCanadaWeatherRequest:
    """Configuration for Nav Canada weather data requests"""
    station_ids: List[str]
    save_raw_data: bool = True
    raw_data_filename: Optional[str] = None
    headless: bool = True
    timeout: int = 30


@dataclass
class NavCanadaWeatherResponse:
    """Response containing parsed weather objects"""
    metars: Dict[str, List[METAR]]
    tafs: Dict[str, List[TAF]]
    upper_winds: List[UpperWind]
    raw_data_file: Optional[str]
    extraction_summary: Dict[str, Any]
    session_info: Dict[str, Any]


class NavCanadaWeatherServer:
    """
    Server for fetching aviation weather data from Nav Canada
    
    Queries Nav Canada website, saves intermediate JSON, and returns
    parsed METAR, TAF, and Upper Wind objects.
    """

    def __init__(self, 
                 headless: bool = True, 
                 timeout: int = 30,
                 data_dir: str = "weather_data"):
        """
        Initialize the Nav Canada weather server
        
        Args:
            headless: Run browser in headless mode
            timeout: Request timeout in seconds
            data_dir: Directory to save raw JSON data
        """
        self.headless = headless
        self.timeout = timeout
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def get_weather(self,
                    station_ids: Union[str, List[str]],
                    save_raw_data: bool = True,
                    raw_data_filename: Optional[str] = None) -> NavCanadaWeatherResponse:
        """
        Fetch and parse weather data from Nav Canada
        
        Args:
            station_ids: Single station ID or list of ICAO station codes (e.g., 'CYVR' or ['CYVR', 'CYYC'])
            save_raw_data: Whether to save intermediate JSON file
            raw_data_filename: Custom filename for raw data (optional)
            
        Returns:
            NavCanadaWeatherResponse containing parsed METAR, TAF, and Upper Wind objects
            
        Raises:
            ValueError: If station_ids is empty
            Exception: If data extraction fails
        """
        # Normalize station_ids to list
        if isinstance(station_ids, str):
            station_ids = [station_ids]
        
        if not station_ids:
            raise ValueError("station_ids must not be empty")

        print(f"\n{'='*70}")
        print(f"🌐 Nav Canada Weather Server")
        print(f"📍 Requesting data for: {', '.join(station_ids)}")
        print(f"{'='*70}\n")

        # Step 1: Extract raw data from Nav Canada
        raw_data = self._extract_raw_data(station_ids)
        
        if 'error' in raw_data:
            raise Exception(f"Data extraction failed: {raw_data['error']}")

        # Step 2: Save raw JSON if requested
        raw_data_filepath = None
        if save_raw_data:
            raw_data_filepath = self._save_raw_data(raw_data, raw_data_filename)

        # Step 3: Parse into objects
        parsed_data = self._parse_weather_data(raw_data)

        # Step 4: Create response
        response = NavCanadaWeatherResponse(
            metars=parsed_data['metars'],
            tafs=parsed_data['tafs'],
            upper_winds=parsed_data['upper_winds'],
            raw_data_file=raw_data_filepath,
            extraction_summary=raw_data.get('extraction_summary', {}),
            session_info=raw_data.get('session_info', {})
        )

        self._print_summary(response)
        
        return response

    def get_metar(self,
                  station_ids: Union[str, List[str]],
                  save_raw_data: bool = True,
                  raw_data_filename: Optional[str] = None) -> Dict[str, List[METAR]]:
        """
        Fetch only METAR data from Nav Canada
        
        Args:
            station_ids: Single station ID or list of ICAO station codes
            save_raw_data: Whether to save intermediate JSON file
            raw_data_filename: Custom filename for raw data (optional)
            
        Returns:
            Dictionary mapping station IDs to lists of METAR objects
        """
        response = self.get_weather(station_ids, save_raw_data, raw_data_filename)
        return response.metars

    def get_taf(self,
                station_ids: Union[str, List[str]],
                save_raw_data: bool = True,
                raw_data_filename: Optional[str] = None) -> Dict[str, List[TAF]]:
        """
        Fetch only TAF data from Nav Canada
        
        Args:
            station_ids: Single station ID or list of ICAO station codes
            save_raw_data: Whether to save intermediate JSON file
            raw_data_filename: Custom filename for raw data (optional)
            
        Returns:
            Dictionary mapping station IDs to lists of TAF objects
        """
        response = self.get_weather(station_ids, save_raw_data, raw_data_filename)
        return response.tafs

    def get_upper_winds(self,
                        station_ids: Union[str, List[str]],
                        save_raw_data: bool = True,
                        raw_data_filename: Optional[str] = None) -> List[UpperWind]:
        """
        Fetch upper wind data from Nav Canada
        
        Note: Upper winds typically cover multiple stations in a region
        
        Args:
            station_ids: Single station ID or list of ICAO station codes
            save_raw_data: Whether to save intermediate JSON file
            raw_data_filename: Custom filename for raw data (optional)
            
        Returns:
            List of UpperWind objects
        """
        response = self.get_weather(station_ids, save_raw_data, raw_data_filename)
        return response.upper_winds

    def _extract_raw_data(self, station_ids: List[str]) -> Dict[str, Any]:
        """Extract raw data from Nav Canada using the simple client"""
        print("📡 Extracting data from Nav Canada...")
        
        with NavCanadaSimpleClient(headless=self.headless, timeout=self.timeout) as client:
            results = client.get_simple_weather_data(station_ids)
        
        return results

    def _save_raw_data(self, raw_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save raw JSON data to file"""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            stations = raw_data.get('session_info', {}).get('stations_requested', [])
            stations_str = '_'.join(stations[:3])  # Limit to first 3 stations in filename
            filename = f"navcanada_{stations_str}_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Raw data saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"⚠️ Failed to save raw data: {e}")
            return None

    def _parse_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw JSON into METAR, TAF, and Upper Wind objects"""
        print("\n🔄 Parsing weather data into objects...")
        
        weather_data = raw_data.get('weather_data', {})
        
        parsed = {
            'metars': {},
            'tafs': {},
            'upper_winds': []
        }

        # Parse METARs
        metar_data = weather_data.get('METAR', {})
        for station, entries in metar_data.items():
            parsed_metars = []
            for entry in entries:
                try:
                    metar = METAR.from_optimized_json(
                        entry['bulletin'],
                        station,
                        entry.get('extraction_time', '')
                    )
                    parsed_metars.append(metar)
                except Exception as e:
                    print(f"⚠️ Failed to parse METAR for {station}: {e}")
            
            if parsed_metars:
                parsed['metars'][station] = parsed_metars
        
        print(f"  ✅ Parsed {sum(len(v) for v in parsed['metars'].values())} METARs from {len(parsed['metars'])} stations")

        # Parse TAFs
        taf_data = weather_data.get('TAF', {})
        for station, entries in taf_data.items():
            parsed_tafs = []
            for entry in entries:
                try:
                    taf = TAF.from_optimized_json(
                        entry['bulletin'],
                        station,
                        entry.get('extraction_time', '')
                    )
                    parsed_tafs.append(taf)
                except Exception as e:
                    print(f"⚠️ Failed to parse TAF for {station}: {e}")
            
            if parsed_tafs:
                parsed['tafs'][station] = parsed_tafs
        
        print(f"  ✅ Parsed {sum(len(v) for v in parsed['tafs'].values())} TAFs from {len(parsed['tafs'])} stations")

        # Parse Upper Winds
        upper_wind_data = weather_data.get('Upper_Wind', [])
        for entry in upper_wind_data:
            try:
                bulletin = entry.get('bulletin', '')
                upper_wind = UpperWind.from_bulletin(bulletin)
                parsed['upper_winds'].append(upper_wind)
            except Exception as e:
                print(f"⚠️ Failed to parse Upper Wind: {e}")
        
        print(f"  ✅ Parsed {len(parsed['upper_winds'])} Upper Wind reports")

        return parsed

    def _print_summary(self, response: NavCanadaWeatherResponse):
        """Print summary of parsed data"""
        print(f"\n{'='*70}")
        print("📊 PARSING SUMMARY")
        print(f"{'='*70}")
        
        # METAR summary
        total_metars = sum(len(v) for v in response.metars.values())
        print(f"\n🌤️  METAR:")
        print(f"   • {total_metars} observation(s) from {len(response.metars)} station(s)")
        for station, metars in response.metars.items():
            print(f"   • {station}: {len(metars)} METAR(s)")
        
        # TAF summary
        total_tafs = sum(len(v) for v in response.tafs.values())
        print(f"\n📅 TAF:")
        print(f"   • {total_tafs} forecast(s) from {len(response.tafs)} station(s)")
        for station, tafs in response.tafs.items():
            print(f"   • {station}: {len(tafs)} TAF(s)")
        
        # Upper Wind summary
        print(f"\n🌬️  Upper Winds:")
        print(f"   • {len(response.upper_winds)} report(s)")
        
        # Files
        if response.raw_data_file:
            print(f"\n📄 Raw data file: {response.raw_data_file}")
        
        print(f"\n{'='*70}\n")

    def export_to_json(self, 
                      response: NavCanadaWeatherResponse, 
                      filename: Optional[str] = None) -> str:
        """
        Export parsed objects to JSON format
        
        Args:
            response: NavCanadaWeatherResponse object
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"parsed_weather_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        export_data = {
            'export_time': datetime.now(timezone.utc).isoformat(),
            'metars': {
                station: [metar.to_dict() for metar in metars]
                for station, metars in response.metars.items()
            },
            'tafs': {
                station: [taf.to_dict() for taf in tafs]
                for station, tafs in response.tafs.items()
            },
            'upper_winds': [wind.to_dict() for wind in response.upper_winds],
            'extraction_summary': response.extraction_summary,
            'session_info': response.session_info
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Exported parsed data to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None


# Example usage
if __name__ == "__main__":
    print("🌤️  Nav Canada Weather Server - Example Usage")
    print("=" * 70)
    
    # Initialize server
    server = NavCanadaWeatherServer(headless=True, timeout=30)
    
    try:
        # Example 1: Get all weather data for Vancouver
        print("\n📋 Example 1: Get all weather for CYVR")
        print("-" * 70)
        response = server.get_weather(
            station_ids='CYVR',
            save_raw_data=True,
            raw_data_filename='example_cyvr.json'
        )
        
        # Access parsed objects
        if 'CYVR' in response.metars:
            for metar in response.metars['CYVR']:
                print(f"\n🌤️  METAR: {metar.station_id}")
                print(f"   Temp: {metar.temperature_celsius}°C")
                print(f"   Wind: {metar.wind_direction_degrees}° at {metar.wind_speed_knots}kt")
                print(f"   Visibility: {metar.visibility}")
        
        # Export to JSON
        server.export_to_json(response, 'example_cyvr_parsed.json')
        
        # Example 2: Get only METARs for multiple stations
        print("\n\n📋 Example 2: Get METARs for CYVR and CYYC")
        print("-" * 70)
        metars = server.get_metar(
            station_ids=['CYVR', 'CYYC'],
            save_raw_data=True
        )
        
        for station, metar_list in metars.items():
            print(f"\n{station}: {len(metar_list)} METAR(s)")
        
        # Example 3: Get only TAFs
        print("\n\n📋 Example 3: Get TAFs for CYVR and CYYC")
        print("-" * 70)
        tafs = server.get_taf(
            station_ids=['CYVR', 'CYYC'],
            save_raw_data=True
        )
        
        for station, taf_list in tafs.items():
            print(f"\n{station}: {len(taf_list)} TAF(s)")
            for taf in taf_list:
                print(f"   Valid: {taf.valid_from} to {taf.valid_to}")
        
        # Example 4: Get upper winds
        print("\n\n📋 Example 4: Get Upper Winds")
        print("-" * 70)
        upper_winds = server.get_upper_winds(
            station_ids=['CYVR'],
            save_raw_data=True
        )
        
        for wind in upper_winds:
            print(f"\n🌬️  Upper Wind Report:")
            print(f"   Valid: {wind.valid_time}")
            print(f"   Stations: {len(wind.station_data)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ Examples complete!")
