"""

Weather Data Server for Aviation Weather Transformer

This module provides functionality to fetch METAR and TAF data from aviation weather APIs.
"""

import requests
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass


@dataclass
class WeatherRequest:
    """Configuration for weather data requests"""
    station_ids: Optional[List[str]] = None
    bbox: Optional[tuple] = None  # (lat_min, lon_min, lat_max, lon_max)
    format: str = 'raw'
    include_taf: bool = False
    hours_back: float = 1.5
    date: Optional[str] = None  # Format: YYYYMMDDHHMM


class AviationWeatherClient:
    """
    Client for fetching aviation weather data from aviationweather.gov API
    
    Handles METAR and TAF data retrieval with support for station IDs,
    bounding box queries, and historical data requests.
    """

    BASE_URL = "https://aviationweather.gov/api/data"

    def __init__(self, timeout: int = 30):
        """
        Initialize the weather client
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        # Set user agent for API compliance
        self.session.headers.update({
            'User-Agent': 'AviationTransformer/1.0 (Aviation Weather Data Processing)'
        })

    def get_metar(self,
                  station_ids: Optional[Union[str, List[str]]] = None,
                  bbox: Optional[tuple] = None,
                  hours_back: float = 1.5,
                  date: Optional[str] = None,
                  format: str = 'raw') -> Dict[str, Any]:
        """
        Fetch METAR data from Aviation Weather API
        
        Args:
            station_ids: Single station ID or list of ICAO station codes (e.g., 'KMCI' or ['KMCI', 'KJFK'])
            bbox: Bounding box as (lat_min, lon_min, lat_max, lon_max)
            hours_back: Hours back from current time to retrieve data
            date: Specific date in format YYYYMMDDHHMM (UTC)
            format: Data format ('raw', 'xml', 'json')
            
        Returns:
            Dictionary containing API response data
            
        Raises:
            requests.RequestException: If API request fails
            ValueError: If neither station_ids nor bbox provided
        """
        if not station_ids and not bbox:
            raise ValueError("Either station_ids or bbox must be provided")

        params = self._build_metar_params(
            station_ids, bbox, hours_back, date, format)

        try:
            response = self.session.get(
                f"{self.BASE_URL}/metar",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            return {
                'status_code': response.status_code,
                'data': response.text,
                'headers': dict(response.headers),
                'url': response.url,
                'request_params': params
            }

        except requests.RequestException as e:
            raise requests.RequestException(
                f"Failed to fetch METAR data: {str(e)}") from e

    def get_taf(self,
                station_ids: Optional[Union[str, List[str]]] = None,
                bbox: Optional[tuple] = None,
                hours_back: float = 1.5,
                date: Optional[str] = None,
                format: str = 'raw') -> Dict[str, Any]:
        """
        Fetch TAF data from Aviation Weather API
        
        Args:
            station_ids: Single station ID or list of ICAO station codes
            bbox: Bounding box as (lat_min, lon_min, lat_max, lon_max)  
            hours_back: Hours back from current time to retrieve data
            date: Specific date in format YYYYMMDDHHMM (UTC)
            format: Data format ('raw', 'xml', 'json')
            
        Returns:
            Dictionary containing API response data
            
        Raises:
            requests.RequestException: If API request fails
            ValueError: If neither station_ids nor bbox provided
        """
        if not station_ids and not bbox:
            raise ValueError("Either station_ids or bbox must be provided")

        params = self._build_taf_params(
            station_ids, bbox, hours_back, date, format)

        try:
            response = self.session.get(
                f"{self.BASE_URL}/taf",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            return {
                'status_code': response.status_code,
                'data': response.text,
                'headers': dict(response.headers),
                'url': response.url,
                'request_params': params
            }

        except requests.RequestException as e:
            raise requests.RequestException(
                f"Failed to fetch TAF data: {str(e)}") from e

    def _build_metar_params(self,
                            station_ids: Optional[Union[str, List[str]]],
                            bbox: Optional[tuple],
                            hours_back: float,
                            date: Optional[str],
                            format: str) -> Dict[str, str]:
        """Build parameters for METAR API request"""
        params = {
            'format': format,
            'taf': 'false',
            'hours': str(hours_back)
        }

        if station_ids:
            if isinstance(station_ids, str):
                params['ids'] = station_ids
            else:
                params['ids'] = ','.join(station_ids)

        if bbox:
            params['bbox'] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

        if date:
            params['date'] = date

        return params

    def _build_taf_params(self,
                          station_ids: Optional[Union[str, List[str]]],
                          bbox: Optional[tuple],
                          hours_back: float,
                          date: Optional[str],
                          format: str) -> Dict[str, str]:
        """Build parameters for TAF API request"""
        params = {
            'format': format,
            'hours': str(hours_back)
        }

        if station_ids:
            if isinstance(station_ids, str):
                params['ids'] = station_ids
            else:
                params['ids'] = ','.join(station_ids)

        if bbox:
            params['bbox'] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

        if date:
            params['date'] = date

        return params

    def get_current_utc_date(self) -> str:
        """
        Get current UTC date in API format (YYYYMMDDHHMM)
        
        Returns:
            Current UTC datetime as string
        """
        return datetime.now(timezone.utc).strftime('%Y%m%d%H%M')

    def close(self):
        """Close the HTTP session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == "__main__":
    # Example matching your provided URL
    with AviationWeatherClient() as client:
        try:
            # Single station request (like your example)
            metar_data = client.get_metar(
                station_ids="KMCI",
                hours_back=1.5,
                date="202509270000"
            )
            print("METAR Data:")
            print(metar_data['data'])
            print(f"Request URL: {metar_data['url']}")

            # Multiple stations
            multi_station_data = client.get_metar(
                station_ids=["KMCI", "KJFK", "KLAX"]
            )
            print("\nMulti-station METAR Data:")
            print(multi_station_data['data'])

            # Bounding box request
            bbox_data = client.get_metar(
                bbox=(40, -90, 45, -85),
                hours_back=1.5
            )
            print("\nBounding box METAR Data:")
            print(bbox_data['data'])

        except Exception as e:
            print(f"Error: {e}")
