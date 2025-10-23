"""METAR data model and parsing helpers for the Aviation Weather Transformer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import json
import re

__all__ = ["CloudLayer", "METAR"]


def _parse_iso8601(value: Optional[str]) -> datetime:
    """Parse a potentially simple ISO-8601 string into a timezone-aware datetime."""
    if not value:
        return datetime.now(timezone.utc)

    try:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


@dataclass
class CloudLayer:
    """Represents a single cloud layer observation"""
    coverage: str  # SKC, CLR, FEW, SCT, BKN, OVC
    altitude_feet: Optional[int] = None  # Cloud base altitude in feet AGL
    # CB (cumulonimbus), TCU (towering cumulus)
    cloud_type: Optional[str] = None


@dataclass
class METAR:
    """
    METAR (Meteorological Aerodrome Report) data structure
    
    Represents structured aviation weather observations with human-readable property names.
    All temperatures in Celsius, pressures in hPa, distances in kilometers unless specified.
    """

    # Station Information
    station_id: str  # ICAO identifier (e.g., 'KMCI')
    station_name: str  # Human readable name (e.g., 'Kansas City Intl, MO, US')
    latitude: float  # Decimal degrees
    longitude: float  # Decimal degrees
    elevation_meters: int  # Station elevation in meters

    # Timing Information
    observation_time: datetime  # When observation was made (reportTime)
    receipt_time: datetime  # When report was received by system
    observation_timestamp: int  # Unix timestamp (obsTime)

    # Temperature and Humidity
    temperature_celsius: float  # Air temperature
    dewpoint_celsius: float  # Dewpoint temperature

    # Wind Information
    wind_direction_degrees: Optional[int] = None  # True direction (0-360)
    wind_speed_knots: Optional[int] = None  # Wind speed
    wind_gust_knots: Optional[int] = None  # Gust speed if present
    wind_variable: bool = False  # True if wind direction is variable

    # Visibility
    visibility: str = "10+"  # Visibility in statute miles or "10+" for 10+ miles
    # Visibility in meters if available
    visibility_meters: Optional[int] = None

    # Pressure
    altimeter_hpa: float = 0.0  # Altimeter setting in hPa
    sea_level_pressure_hpa: Optional[float] = None  # Sea level pressure
    pressure_tendency_hpa: Optional[float] = None  # 3-hour pressure change

    # Sky Conditions
    sky_coverage: str = "CLR"  # Overall sky coverage (CLR, FEW, SCT, BKN, OVC)
    cloud_layers: List[CloudLayer] = field(default_factory=list)

    # Flight Categories
    flight_category: str = "VFR"  # VFR, MVFR, IFR, LIFR

    # Temperature Extremes (if available)
    max_temperature_celsius: Optional[float] = None  # 24-hour maximum
    min_temperature_celsius: Optional[float] = None  # 24-hour minimum

    # Weather Phenomena
    present_weather: List[str] = field(default_factory=list)

    # Quality Control
    quality_control_field: Optional[int] = None  # QC flags

    # Report Information
    report_type: str = "METAR"  # METAR or SPECI
    raw_observation: str = ""  # Original raw METAR text

    def __post_init__(self) -> None:
        """Ensure datetimes remain timezone-aware and lists are unique when provided."""
        if self.observation_time.tzinfo is None:
            self.observation_time = self.observation_time.replace(
                tzinfo=timezone.utc)
        if self.receipt_time.tzinfo is None:
            self.receipt_time = self.receipt_time.replace(tzinfo=timezone.utc)

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'METAR':
        """
        Create METAR object from Aviation Weather API JSON response
        
        Args:
            data: Dictionary from API response containing METAR data
            
        Returns:
            METAR object with populated fields
        """
        # Parse cloud layers
        cloud_layers = []
        if 'clouds' in data and data['clouds']:
            for cloud in data['clouds']:
                layer = CloudLayer(
                    coverage=cloud.get('cover', ''),
                    altitude_feet=cloud.get('base'),
                    cloud_type=cloud.get('type')
                )
                cloud_layers.append(layer)

        # Parse timestamps
        observation_time = _parse_iso8601(data.get('reportTime'))
        receipt_time = _parse_iso8601(data.get('receiptTime'))

        return cls(
            # Station Information
            station_id=data.get('icaoId', ''),
            station_name=data.get('name', ''),
            latitude=data.get('lat', 0.0),
            longitude=data.get('lon', 0.0),
            elevation_meters=data.get('elev', 0),

            # Timing
            observation_time=observation_time,
            receipt_time=receipt_time,
            observation_timestamp=data.get('obsTime', 0),

            # Temperature and Humidity
            temperature_celsius=data.get('temp', 0.0),
            dewpoint_celsius=data.get('dewp', 0.0),

            # Wind
            wind_direction_degrees=data.get('wdir'),
            wind_speed_knots=data.get('wspd'),
            wind_gust_knots=data.get('wgst'),
            wind_variable=data.get('wdir') is None,

            # Visibility
            visibility=str(data.get('visib', '10+')),

            # Pressure
            altimeter_hpa=data.get('altim', 0.0),
            sea_level_pressure_hpa=data.get('slp'),
            pressure_tendency_hpa=data.get('presTend'),

            # Sky Conditions
            sky_coverage=data.get('cover', 'CLR'),
            cloud_layers=cloud_layers,

            # Flight Category
            flight_category=data.get('fltCat', 'VFR'),

            # Temperature Extremes
            max_temperature_celsius=data.get('maxT'),
            min_temperature_celsius=data.get('minT'),

            # Quality Control
            quality_control_field=data.get('qcField'),

            # Report Information
            report_type=data.get('metarType', 'METAR'),
            raw_observation=data.get('rawOb', '')
        )

    @classmethod
    def from_optimized_json(cls, bulletin: str, station_id: str = "", extraction_time: str = "") -> 'METAR':
        """
        Create METAR object from Nav Canada optimized JSON structure
        
        Args:
            bulletin: Raw METAR bulletin text from Nav Canada
            station_id: Station identifier (e.g., 'CYVR')
            extraction_time: ISO timestamp when data was extracted
            
        Returns:
            METAR object with populated fields parsed from raw bulletin
            
        Example:
            data = json.load(open('optimized_example.json'))
            for station, entries in data['weather_data']['METAR'].items():
                for entry in entries:
                    metar = METAR.from_optimized_json(
                        entry['bulletin'], 
                        station,
                        entry['extraction_time']
                    )
        """
        # Parse the raw METAR bulletin
        raw_metar = bulletin.strip()

        # Extract station ID from bulletin if not provided
        if not station_id:
            station_match = re.match(r'^METAR\s+([A-Z]{4})', raw_metar)
            if station_match:
                station_id = station_match.group(1)

        # Parse observation time (DDHHMM format)
        obs_time: Optional[datetime] = None
        obs_timestamp = 0
        time_match = re.search(r'(\d{2})(\d{2})(\d{2})Z', raw_metar)
        if time_match:
            day = int(time_match.group(1))
            hour = int(time_match.group(2))
            minute = int(time_match.group(3))
            # Use current month/year as approximation (UTC)
            now = datetime.now(timezone.utc)
            try:
                obs_time = datetime(now.year, now.month, day,
                                    hour, minute, 0, tzinfo=timezone.utc)
                obs_timestamp = int(obs_time.timestamp())
            except ValueError:
                obs_time = now
                obs_timestamp = int(now.timestamp())

        # Parse wind (e.g., 13005KT, VRB03KT, 36010G20KT)
        wind_dir = None
        wind_speed = None
        wind_gust = None
        wind_variable = False

        wind_match = re.search(
            r'(VRB|[0-9]{3})([0-9]{2,3})(G([0-9]{2,3}))?KT', raw_metar)
        if wind_match:
            if wind_match.group(1) == 'VRB':
                wind_variable = True
                wind_dir = None
            else:
                wind_dir = int(wind_match.group(1))
            wind_speed = int(wind_match.group(2))
            if wind_match.group(4):
                wind_gust = int(wind_match.group(4))

        # Parse visibility (e.g., 20SM, 10SM, 3/4SM)
        visibility = "10+"
        vis_match = re.search(r'\s(\d+(/\d+)?SM|P6SM)\s', raw_metar)
        if vis_match:
            visibility = vis_match.group(1).replace('SM', '')
        elif 'P6SM' in raw_metar:
            visibility = "6+"
        elif re.search(r'\s(\d+)SM\s', raw_metar):
            vis_match = re.search(r'\s(\d+)SM\s', raw_metar)
            visibility = vis_match.group(1)

        # Parse temperature and dewpoint (e.g., 10/06, M02/M05)
        temp_celsius = 0.0
        dewpoint_celsius = 0.0
        temp_match = re.search(r'\s(M?\d{2})/(M?\d{2})\s', raw_metar)
        if temp_match:
            temp_str = temp_match.group(1)
            dewp_str = temp_match.group(2)
            temp_celsius = - \
                float(temp_str[1:]) if temp_str.startswith(
                    'M') else float(temp_str)
            dewpoint_celsius = - \
                float(dewp_str[1:]) if dewp_str.startswith(
                    'M') else float(dewp_str)

        # Parse altimeter (e.g., A2982, Q1013)
        altimeter_hpa = 0.0
        alt_match = re.search(r'A(\d{4})', raw_metar)
        if alt_match:
            # Convert inches Hg to hPa
            inches_hg = int(alt_match.group(1)) / 100.0
            altimeter_hpa = inches_hg * 33.8639
        else:
            # Try Q format (hPa directly)
            q_match = re.search(r'Q(\d{4})', raw_metar)
            if q_match:
                altimeter_hpa = float(q_match.group(1))

        # Parse sky conditions
        sky_coverage = "CLR"
        cloud_layers = []

        # Look for cloud codes (SKC, CLR, FEW, SCT, BKN, OVC)
        cloud_matches = re.findall(
            r'(SKC|CLR|NSC|FEW|SCT|BKN|OVC)(\d{3})?(CB|TCU)?', raw_metar)
        if cloud_matches:
            for match in cloud_matches:
                coverage = match[0]
                altitude = int(match[1]) * 100 if match[1] else None
                cloud_type = match[2] if match[2] else None

                cloud_layers.append(CloudLayer(
                    coverage=coverage,
                    altitude_feet=altitude,
                    cloud_type=cloud_type
                ))

                # Set overall sky coverage to worst condition
                if coverage in ['OVC', 'BKN']:
                    sky_coverage = coverage
                elif coverage in ['SCT', 'FEW'] and sky_coverage == 'CLR':
                    sky_coverage = coverage

        # Determine flight category (simplified)
        flight_category = "VFR"
        try:
            vis_num = float(visibility.replace('SM', '').replace('+', ''))
            if vis_num < 1:
                flight_category = "LIFR"
            elif vis_num < 3:
                flight_category = "IFR"
            elif vis_num < 5:
                flight_category = "MVFR"
        except ValueError:
            pass

        # Check ceiling for flight category
        for layer in cloud_layers:
            if layer.coverage in ['BKN', 'OVC'] and layer.altitude_feet:
                if layer.altitude_feet < 500:
                    flight_category = "LIFR"
                elif layer.altitude_feet < 1000:
                    flight_category = "IFR"
                elif layer.altitude_feet < 3000:
                    flight_category = "MVFR"

        # Parse extraction time
        receipt_time = datetime.now(timezone.utc)
        if extraction_time:
            receipt_time = _parse_iso8601(extraction_time)

        return cls(
            # Station Information
            station_id=station_id,
            # Name not available from raw METAR
            station_name=f"Station {station_id}",
            latitude=0.0,  # Not available from raw METAR
            longitude=0.0,  # Not available from raw METAR
            elevation_meters=0,  # Not available from raw METAR

            # Timing
            observation_time=obs_time or datetime.now(timezone.utc),
            receipt_time=receipt_time,
            observation_timestamp=obs_timestamp,

            # Temperature and Humidity
            temperature_celsius=temp_celsius,
            dewpoint_celsius=dewpoint_celsius,

            # Wind
            wind_direction_degrees=wind_dir,
            wind_speed_knots=wind_speed,
            wind_gust_knots=wind_gust,
            wind_variable=wind_variable,

            # Visibility
            visibility=visibility,

            # Pressure
            altimeter_hpa=altimeter_hpa,

            # Sky Conditions
            sky_coverage=sky_coverage,
            cloud_layers=cloud_layers,

            # Flight Category
            flight_category=flight_category,

            # Report Information
            report_type="METAR",
            raw_observation=raw_metar
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert METAR object to dictionary for JSON serialization"""
        result = {}

        for field_name, field_value in self.__dict__.items():
            if field_value is None:
                continue

            if isinstance(field_value, datetime):
                result[field_name] = field_value.isoformat()
            elif field_name == 'cloud_layers':
                result[field_name] = [
                    {
                        'coverage': layer.coverage,
                        'altitude_feet': layer.altitude_feet,
                        'cloud_type': layer.cloud_type
                    }
                    for layer in field_value
                ]
            else:
                result[field_name] = field_value

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert METAR object to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def is_vfr(self) -> bool:
        """Check if conditions are VFR (Visual Flight Rules)"""
        return self.flight_category == 'VFR'

    def is_ifr(self) -> bool:
        """Check if conditions are IFR (Instrument Flight Rules)"""
        return self.flight_category in ['IFR', 'LIFR']

    def has_precipitation(self) -> bool:
        """Check if precipitation is present"""
        precip_codes = ['RA', 'SN', 'DZ', 'FZ', 'SH', 'TS']
        return any(code in ' '.join(self.present_weather)
                   for code in precip_codes)

    def temperature_fahrenheit(self) -> float:
        """Convert temperature to Fahrenheit"""
        return (self.temperature_celsius * 9/5) + 32

    def dewpoint_fahrenheit(self) -> float:
        """Convert dewpoint to Fahrenheit"""
        return (self.dewpoint_celsius * 9/5) + 32

    def altimeter_inches_hg(self) -> float:
        """Convert altimeter setting to inches of mercury"""
        return self.altimeter_hpa * 0.02953

    def wind_speed_mph(self) -> Optional[float]:
        """Convert wind speed to miles per hour"""
        if self.wind_speed_knots is None:
            return None
        return self.wind_speed_knots * 1.15078

    def __str__(self) -> str:
        """Human readable string representation"""
        return (
            f"METAR {self.station_id} ({self.station_name})\n"
            f"Time: {self.observation_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Temp: {self.temperature_celsius}°C ({self.temperature_fahrenheit():.1f}°F)\n"
            f"Wind: {self.wind_direction_degrees or 'VRB'}° at {self.wind_speed_knots or 0} kts\n"
            f"Visibility: {self.visibility} SM\n"
            f"Sky: {self.sky_coverage}\n"
            f"Altimeter: {self.altimeter_hpa:.1f} hPa ({self.altimeter_inches_hg():.2f}\")\n"
            f"Flight Category: {self.flight_category}\n"
            f"Raw: {self.raw_observation}"
        )


# Example usage and testing
if __name__ == "__main__":
    # Example data from your JSON file
    example_data = {
        "icaoId": "KMCI",
        "receiptTime": "2025-09-26T23:56:21.753Z",
        "obsTime": 1758930780,
        "reportTime": "2025-09-27T00:00:00.000Z",
        "temp": 24.4,
        "dewp": 13.3,
        "wdir": 170,
        "wspd": 4,
        "visib": "10+",
        "altim": 1012.6,
        "slp": 1011.6,
        "qcField": 12,
        "presTend": -0.2,
        "maxT": 28.3,
        "minT": 24.4,
        "metarType": "METAR",
        "rawOb": "METAR KMCI 262353Z 17004KT 10SM CLR 24/13 A2990 RMK AO2 SLP116 T02440133 10283 20244 56002 $",
        "lat": 39.2975,
        "lon": -94.7309,
        "elev": 308,
        "name": "Kansas City Intl, MO, US",
        "cover": "CLR",
        "clouds": [],
        "fltCat": "VFR"
    }

    # Create METAR object from API data
    metar = METAR.from_api_response(example_data)

    # Display the parsed data
    print(metar)
    print("\n" + "="*50 + "\n")

    # Show JSON representation
    print("JSON representation:")
    print(metar.to_json())

    # Show some utility methods
    print(f"\nVFR conditions: {metar.is_vfr()}")
    print(f"Temperature in Fahrenheit: {metar.temperature_fahrenheit():.1f}°F")
    print(f"Wind speed in MPH: {metar.wind_speed_mph():.1f}" if metar.wind_speed_mph(
    ) else "No wind data")
