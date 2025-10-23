"""Nav Canada weather data server and parsing utilities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

from navcanada_simple_client import NavCanadaSimpleClient
from metar import METAR
from taf import TAF
from upper_wind import UpperWind, UpperWindMerger
from sigmet import SIGMET, parse_sigmet_text

__all__ = [
    "NavCanadaWeatherRequest",
    "NavCanadaWeatherResponse",
    "NavCanadaWeatherServer",
]


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
    sigmets: List[SIGMET]
    raw_data_file: Optional[str]
    extraction_summary: Dict[str, Any]
    session_info: Dict[str, Any]




class NavCanadaWeatherServer:
    """
    Fetch and parse aviation weather data (METAR, TAF, Upper Wind) from Nav Canada.
    Handles raw data extraction, parsing, and export.
    """

    def __init__(self, 
                 headless: bool = True, 
                 timeout: int = 30,
                 data_dir: str = "weather_data",
                 verbose: bool = True):
        """
        Initialize the Nav Canada weather server
        
        Args:
            headless: Run browser in headless mode
            timeout: Request timeout in seconds
            data_dir: Directory to save raw JSON data
            verbose: Print progress information when True
        """
        self.headless = headless
        self.timeout = timeout
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Print messages when verbose output is enabled."""
        if self.verbose:
            print(message)

    def get_weather(self,
                    station_ids: Union[str, List[str]],
                    save_raw_data: bool = True,
                    raw_data_filename: Optional[str] = None) -> NavCanadaWeatherResponse:
        """
        Fetch and parse all weather data for given stations from Nav Canada.
        Returns a NavCanadaWeatherResponse with all parsed objects.
        """
        # Normalize station_ids to list
        if isinstance(station_ids, str):
            station_ids = [station_ids]
        
        if not station_ids:
            raise ValueError("station_ids must not be empty")

        divider = '=' * 70
        self._log(f"\n{divider}")
        self._log("🌐 Nav Canada Weather Server")
        self._log(f"📍 Requesting data for: {', '.join(station_ids)}")
        self._log(f"{divider}\n")

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
            sigmets=parsed_data['sigmets'],
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
        Fetch only METAR data for given stations.
        Returns a dict mapping station IDs to METAR objects.
        """
        response = self.get_weather(station_ids, save_raw_data, raw_data_filename)
        return response.metars

    def get_taf(self,
                station_ids: Union[str, List[str]],
                save_raw_data: bool = True,
                raw_data_filename: Optional[str] = None) -> Dict[str, List[TAF]]:
        """
        Fetch only TAF data for given stations.
        Returns a dict mapping station IDs to TAF objects.
        """
        response = self.get_weather(station_ids, save_raw_data, raw_data_filename)
        return response.tafs

    def get_upper_winds(self,
                        station_ids: Union[str, List[str]],
                        save_raw_data: bool = True,
                        raw_data_filename: Optional[str] = None) -> List[UpperWind]:
        """
        Fetch upper wind data for given stations.
        Returns a list of UpperWind objects.
        """
        response = self.get_weather(station_ids, save_raw_data, raw_data_filename)
        return response.upper_winds

    def _extract_raw_data(self, station_ids: List[str]) -> Dict[str, Any]:
        """Extract raw JSON data from Nav Canada using the simple client."""
        self._log("📡 Extracting data from Nav Canada...")
        with NavCanadaSimpleClient(headless=self.headless, timeout=self.timeout) as client:
            return client.get_simple_weather_data(station_ids)

    def _save_raw_data(self, raw_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save raw JSON data to file."""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            stations = raw_data.get('session_info', {}).get('stations_requested', [])
            stations_str = '_'.join(stations[:3])
            filename = f"navcanada_{stations_str}_{timestamp}.json"
        filepath = self.data_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)
            self._log(f"💾 Raw data saved to: {filepath}")
            return str(filepath)
        except Exception as e:
            self._log(f"⚠️ Failed to save raw data: {e}")
            return None


    def _parse_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw JSON into METAR, TAF, Upper Wind, and SIGMET objects."""
        self._log("\n🔄 Parsing weather data into objects...")
        weather_data = raw_data.get('weather_data', {})

        metars = self._parse_metars(weather_data)
        tafs = self._parse_tafs(weather_data)
        upper_winds = self._parse_upper_winds(weather_data)
        sigmets = self._parse_sigmets(weather_data)

        metar_reports = sum(len(items) for items in metars.values())
        taf_reports = sum(len(items) for items in tafs.values())

        self._log(
            f"  ✅ Parsed {metar_reports} METARs from {len(metars)} stations")
        self._log(
            f"  ✅ Parsed {taf_reports} TAFs from {len(tafs)} stations")
        self._log(
            f"  ✅ Parsed {len(upper_winds)} Upper Wind report object(s) (one per station)")
        if sigmets:
            self._log(f"  ✅ Parsed {len(sigmets)} SIGMET advisory(ies)")
        else:
            self._log("  ℹ️  No SIGMET advisories found in dataset")

        return {
            'metars': metars,
            'tafs': tafs,
            'upper_winds': upper_winds,
            'sigmets': sigmets,
        }

    def _parse_metars(self, weather_data: Dict[str, Any]) -> Dict[str, List[METAR]]:
        """Parse METAR entries from the weather data block."""
        metars: Dict[str, List[METAR]] = {}
        for station, entries in weather_data.get('METAR', {}).items():
            bulletins = [
                METAR.from_optimized_json(
                    entry.get('bulletin', ''),
                    station,
                    entry.get('extraction_time', ''),
                )
                for entry in entries
                if entry.get('bulletin')
            ]
            if bulletins:
                metars[station] = bulletins
        return metars

    def _parse_tafs(self, weather_data: Dict[str, Any]) -> Dict[str, List[TAF]]:
        """Parse TAF entries from the weather data block."""
        tafs: Dict[str, List[TAF]] = {}
        for station, entries in weather_data.get('TAF', {}).items():
            forecasts = [
                TAF.from_optimized_json(
                    entry.get('bulletin', ''),
                    station,
                    entry.get('extraction_time', ''),
                )
                for entry in entries
                if entry.get('bulletin')
            ]
            if forecasts:
                tafs[station] = forecasts
        return tafs

    def _parse_upper_winds(self, weather_data: Dict[str, Any]) -> List[UpperWind]:
        """Parse Upper Wind bulletins and merge periods by station."""
        bulletins = [
            entry.get('bulletin', '')
            for entry in weather_data.get('Upper_Wind', [])
            if isinstance(entry, dict) and entry.get('bulletin', '').startswith('VALID')
        ]
        station_map = UpperWindMerger.merge_bulletins(bulletins)
        return [UpperWind(station=station, periods=periods) for station, periods in station_map.items()]

    def _parse_sigmets(self, weather_data: Dict[str, Any]) -> List[SIGMET]:
        """Parse SIGMET bulletins into structured advisories."""
        parsed: List[SIGMET] = []
        for entry in weather_data.get('SIGMET', []):
            bulletin = entry.get('bulletin') if isinstance(
                entry, dict) else entry
            if bulletin:
                parsed.extend(parse_sigmet_text(bulletin))
        return parsed






    def _print_summary(self, response: NavCanadaWeatherResponse):
        """Print summary of parsed data."""
        divider = '=' * 70
        self._log(f"\n{divider}")
        self._log("📊 PARSING SUMMARY")
        self._log(divider)
        total_metars = sum(len(v) for v in response.metars.values())
        self._log(f"\n🌤️  METAR:")
        self._log(
            f"   • {total_metars} observation(s) from {len(response.metars)} station(s)")
        for station, metars in response.metars.items():
            self._log(f"   • {station}: {len(metars)} METAR(s)")
        total_tafs = sum(len(v) for v in response.tafs.values())
        self._log(f"\n📅 TAF:")
        self._log(
            f"   • {total_tafs} forecast(s) from {len(response.tafs)} station(s)")
        for station, tafs in response.tafs.items():
            self._log(f"   • {station}: {len(tafs)} TAF(s)")
        self._log(f"\n🌬️  Upper Winds:")
        self._log(f"   • {len(response.upper_winds)} report(s)")
        self._log(f"\n⚠️  SIGMET:")
        self._log(f"   • {len(response.sigmets)} advisory(ies)")
        if response.raw_data_file:
            self._log(f"\n📄 Raw data file: {response.raw_data_file}")
        self._log(f"\n{divider}\n")

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
            'sigmets': [sigmet.to_dict() for sigmet in response.sigmets],
            # ...existing code...
            'extraction_summary': response.extraction_summary,
            'session_info': response.session_info
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self._log(f"💾 Exported parsed data to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self._log(f"❌ Export failed: {e}")
            return None



# Example usage
if __name__ == "__main__":
    print("🌤️  Nav Canada Weather Server - Example Usage")
    print("=" * 70)
    server = NavCanadaWeatherServer(headless=True, timeout=30)
    try:
        response = server.get_weather(
            station_ids='CYVR', save_raw_data=True, raw_data_filename='example_cyvr.json')
        if 'CYVR' in response.metars:
            for metar in response.metars['CYVR']:
                print(f"\n🌤️  METAR: {metar.station_id}")
                print(f"   Temp: {metar.temperature_celsius}°C")
                print(f"   Wind: {metar.wind_direction_degrees}° at {metar.wind_speed_knots}kt")
                print(f"   Visibility: {metar.visibility}")
        server.export_to_json(response, 'example_cyvr_parsed.json')
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print("\n" + "=" * 70)
    print("✅ Examples complete!")
