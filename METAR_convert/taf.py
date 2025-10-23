"""TAF data model and parsing helpers for the Aviation Weather Transformer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
import json
import re

__all__ = [
    "TAFCloudLayer",
    "IcingTurbulence",
    "TemperatureForecast",
    "TAFForecastPeriod",
    "TAF",
]


def _parse_iso8601(value: Optional[str]) -> datetime:
    """Parse ISO-8601 strings into timezone aware datetimes."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


def _from_timestamp(value: Optional[float]) -> datetime:
    """Convert epoch seconds into a UTC datetime."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (ValueError, OSError):
        return datetime.now(timezone.utc)


@dataclass
class TAFCloudLayer:
    """Represents a single cloud layer in TAF forecast"""
    coverage: str  # SKC, CLR, FEW, SCT, BKN, OVC
    base_altitude_feet: Optional[int] = None  # Cloud base altitude in feet AGL
    # CB (cumulonimbus), TCU (towering cumulus)
    cloud_type: Optional[str] = None


@dataclass
class IcingTurbulence:
    """Represents icing and turbulence information"""
    intensity: Optional[str] = None  # Light, moderate, severe
    type: Optional[str] = None  # Icing or turbulence type
    base_altitude_feet: Optional[int] = None
    top_altitude_feet: Optional[int] = None


@dataclass
class TemperatureForecast:
    """Temperature forecast information"""
    temperature_celsius: Optional[float] = None
    time: Optional[datetime] = None


@dataclass
class TAFForecastPeriod:
    """
    Individual forecast period within a TAF
    
    Represents a specific time period with forecast conditions
    """

    # Time Information
    valid_from: datetime  # Start of forecast period
    valid_to: datetime  # End of forecast period
    valid_from_timestamp: int  # Unix timestamp
    valid_to_timestamp: int  # Unix timestamp
    becomes_time: Optional[datetime] = None  # BECMG time if applicable

    # Change Information
    forecast_change_type: Optional[str] = None  # FM, BECMG, TEMPO, PROB
    probability_percent: Optional[int] = None  # Probability for PROB groups

    # Wind Information
    # Direction or "VRB"
    wind_direction_degrees: Optional[Union[int, str]] = None
    wind_speed_knots: Optional[int] = None
    wind_gust_knots: Optional[int] = None

    # Wind Shear
    wind_shear_height_feet: Optional[int] = None
    wind_shear_direction_degrees: Optional[int] = None
    wind_shear_speed_knots: Optional[int] = None

    # Visibility and Weather
    visibility: str = "6+"  # Visibility in statute miles
    vertical_visibility_feet: Optional[int] = None
    weather_phenomena: Optional[str] = None  # Weather string (RA, SN, etc.)

    # Pressure
    altimeter_hpa: Optional[float] = None

    # Sky Conditions
    cloud_layers: List[TAFCloudLayer] = field(default_factory=list)

    # Icing and Turbulence
    icing_turbulence: List[IcingTurbulence] = field(default_factory=list)

    # Temperature Forecasts
    temperature_forecasts: List[TemperatureForecast] = field(
        default_factory=list)

    # Decoding Issues
    not_decoded: Optional[str] = None  # Any parts that couldn't be decoded

    def is_significant_weather(self) -> bool:
        """Check if period contains significant weather phenomena"""
        if not self.weather_phenomena:
            return False

        significant = ['TS', 'SH', 'FZ', 'SN', 'IC', 'PL', 'GR', 'GS']
        return any(wx in self.weather_phenomena for wx in significant)

    def has_low_visibility(self) -> bool:
        """Check if visibility is less than 3 statute miles"""
        try:
            if self.visibility == "6+" or self.visibility == "P6SM":
                return False
            vis_value = float(self.visibility.replace(
                "SM", "").replace("+", ""))
            return vis_value < 3.0
        except (ValueError, AttributeError):
            return False

    def wind_speed_mph(self) -> Optional[float]:
        """Convert wind speed to miles per hour"""
        if self.wind_speed_knots is None:
            return None
        return self.wind_speed_knots * 1.15078


@dataclass
class TAF:
    """
    TAF (Terminal Aerodrome Forecast) data structure
    
    Represents structured aviation weather forecasts with human-readable property names.
    """

    # Station Information
    station_id: str  # ICAO identifier (e.g., 'KORD')
    station_name: str  # Human readable name
    latitude: float  # Decimal degrees
    longitude: float  # Decimal degrees
    elevation_meters: int  # Station elevation in meters

    # TAF Timing Information
    bulletin_time: datetime  # When TAF bulletin was created
    issue_time: datetime  # When TAF was issued
    database_time: datetime  # When stored in database

    # Validity Period
    valid_from: datetime  # Start of TAF validity
    valid_to: datetime  # End of TAF validity
    valid_from_timestamp: int  # Unix timestamp
    valid_to_timestamp: int  # Unix timestamp

    # TAF Metadata
    is_most_recent: bool = True  # If this is the most recent TAF
    is_prior_version: bool = False  # If this is a prior version
    raw_taf: str = ""  # Original raw TAF text
    remarks: str = ""  # TAF remarks section

    # Forecast Periods
    forecast_periods: List[TAFForecastPeriod] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'TAF':
        """
        Create TAF object from Aviation Weather API JSON response
        
        Args:
            data: Dictionary from API response containing TAF data
            
        Returns:
            TAF object with populated fields
        """

        # Parse main TAF timing
        bulletin_time = _parse_iso8601(data.get('bulletinTime'))
        issue_time = _parse_iso8601(data.get('issueTime'))
        database_time = _parse_iso8601(data.get('dbPopTime'))

        valid_from = _from_timestamp(data.get('validTimeFrom', 0))
        valid_to = _from_timestamp(data.get('validTimeTo', 0))

        # Parse forecast periods
        forecast_periods = []
        if 'fcsts' in data:
            for fcst in data['fcsts']:
                # Parse cloud layers
                cloud_layers = []
                if fcst.get('clouds'):
                    for cloud in fcst['clouds']:
                        layer = TAFCloudLayer(
                            coverage=cloud.get('cover', ''),
                            base_altitude_feet=cloud.get('base'),
                            cloud_type=cloud.get('type')
                        )
                        cloud_layers.append(layer)

                # Parse icing/turbulence
                icing_turb = []
                if fcst.get('icgTurb'):
                    for item in fcst['icgTurb']:
                        it = IcingTurbulence(
                            intensity=item.get('intensity'),
                            type=item.get('type'),
                            base_altitude_feet=item.get('base'),
                            top_altitude_feet=item.get('top')
                        )
                        icing_turb.append(it)

                # Parse temperature forecasts
                temp_forecasts = []
                if fcst.get('temp'):
                    for temp in fcst['temp']:
                        tf = TemperatureForecast(
                            temperature_celsius=temp.get('value'),
                            time=_from_timestamp(
                                temp.get('time')) if temp.get('time') else None
                        )
                        temp_forecasts.append(tf)

                period = TAFForecastPeriod(
                    valid_from=_from_timestamp(fcst.get('timeFrom', 0)),
                    valid_to=_from_timestamp(fcst.get('timeTo', 0)),
                    valid_from_timestamp=fcst.get('timeFrom', 0),
                    valid_to_timestamp=fcst.get('timeTo', 0),
                    becomes_time=_from_timestamp(
                        fcst.get('timeBec')) if fcst.get('timeBec') else None,

                    forecast_change_type=fcst.get('fcstChange'),
                    probability_percent=fcst.get('probability'),

                    wind_direction_degrees=fcst.get('wdir'),
                    wind_speed_knots=fcst.get('wspd'),
                    wind_gust_knots=fcst.get('wgst'),

                    wind_shear_height_feet=fcst.get('wshearHgt'),
                    wind_shear_direction_degrees=fcst.get('wshearDir'),
                    wind_shear_speed_knots=fcst.get('wshearSpd'),

                    visibility=str(fcst.get('visib', '6+')),
                    vertical_visibility_feet=fcst.get('vertVis'),
                    weather_phenomena=fcst.get('wxString'),
                    altimeter_hpa=fcst.get('altim'),

                    cloud_layers=cloud_layers,
                    icing_turbulence=icing_turb,
                    temperature_forecasts=temp_forecasts,

                    not_decoded=fcst.get('notDecoded')
                )
                forecast_periods.append(period)

        return cls(
            # Station Information
            station_id=data.get('icaoId', ''),
            station_name=data.get('name', ''),
            latitude=data.get('lat', 0.0),
            longitude=data.get('lon', 0.0),
            elevation_meters=data.get('elev', 0),

            # Timing
            bulletin_time=bulletin_time,
            issue_time=issue_time,
            database_time=database_time,

            # Validity
            valid_from=valid_from,
            valid_to=valid_to,
            valid_from_timestamp=data.get('validTimeFrom', 0),
            valid_to_timestamp=data.get('validTimeTo', 0),

            # Metadata
            is_most_recent=data.get('mostRecent', 0) == 1,
            is_prior_version=data.get('prior', 0) == 1,
            raw_taf=data.get('rawTAF', ''),
            remarks=data.get('remarks', ''),

            # Forecasts
            forecast_periods=forecast_periods
        )

    @classmethod
    def from_optimized_json(cls, bulletin: str, station_id: str = "", extraction_time: str = "") -> 'TAF':
        """
        Create TAF object from Nav Canada optimized JSON structure
        
        Args:
            bulletin: Raw TAF bulletin text from Nav Canada
            station_id: Station identifier (e.g., 'CYVR')
            extraction_time: ISO timestamp when data was extracted
            
        Returns:
            TAF object with populated fields parsed from raw bulletin
            
        Example:
            data = json.load(open('optimized_example.json'))
            for station, entries in data['weather_data']['TAF'].items():
                for entry in entries:
                    taf = TAF.from_optimized_json(
                        entry['bulletin'], 
                        station,
                        entry['extraction_time']
                    )
        """
        # Parse the raw TAF bulletin
        raw_taf = bulletin.strip()

        # Extract station ID from bulletin if not provided
        if not station_id:
            station_match = re.match(r'^TAF\s+([A-Z]{4})', raw_taf)
            if station_match:
                station_id = station_match.group(1)

        # Parse issue time (DDHHMM format after station ID)
        issue_time = None
        time_match = re.search(
            r'TAF\s+[A-Z]{4}\s+(\d{2})(\d{2})(\d{2})Z', raw_taf)
        if time_match:
            day = int(time_match.group(1))
            hour = int(time_match.group(2))
            minute = int(time_match.group(3))
            now = datetime.now(timezone.utc)
            try:
                issue_time = datetime(
                    now.year, now.month, day, hour, minute, 0, tzinfo=timezone.utc)
            except ValueError:
                issue_time = now

        # Parse validity period (DDHH/DDHH format)
        valid_from = None
        valid_to = None
        valid_from_timestamp = 0
        valid_to_timestamp = 0

        validity_match = re.search(r'(\d{2})(\d{2})/(\d{2})(\d{2})', raw_taf)
        if validity_match:
            from_day = int(validity_match.group(1))
            from_hour = int(validity_match.group(2))
            to_day = int(validity_match.group(3))
            to_hour = int(validity_match.group(4))

            now = datetime.now(timezone.utc)
            try:
                valid_from = datetime(
                    now.year, now.month, from_day, from_hour, 0, 0, tzinfo=timezone.utc)
                valid_to = datetime(now.year, now.month,
                                    to_day, to_hour, 0, 0, tzinfo=timezone.utc)

                # Handle month rollover
                if to_day < from_day:
                    if now.month == 12:
                        valid_to = datetime(
                            now.year + 1, 1, to_day, to_hour, 0, 0, tzinfo=timezone.utc)
                    else:
                        valid_to = datetime(
                            now.year, now.month + 1, to_day, to_hour, 0, 0, tzinfo=timezone.utc)

                valid_from_timestamp = int(valid_from.timestamp())
                valid_to_timestamp = int(valid_to.timestamp())
            except ValueError:
                valid_from = now
                valid_to = now

        # Parse forecast periods
        forecast_periods = []

        # Split by FM (FROM), TEMPO, BECMG, PROB
        # This is a simplified parser - full TAF parsing is complex
        lines = raw_taf.split('\n')
        current_period_text = ""

        for line in lines:
            # Check for period markers
            if re.search(r'(FM\d{6}|TEMPO|BECMG|PROB\d{2})', line):
                if current_period_text:
                    # Parse previous period
                    period = cls._parse_taf_period(
                        current_period_text, valid_from, valid_to)
                    if period:
                        forecast_periods.append(period)
                current_period_text = line
            else:
                current_period_text += " " + line

        # Parse last period
        if current_period_text:
            period = cls._parse_taf_period(
                current_period_text, valid_from, valid_to)
            if period:
                forecast_periods.append(period)

        # Parse extraction time
        database_time = datetime.now(timezone.utc)
        if extraction_time:
            try:
                database_time = _parse_iso8601(extraction_time)
            except (ValueError, AttributeError):
                pass

        return cls(
            # Station Information
            station_id=station_id,
            station_name=f"Station {station_id}",
            latitude=0.0,
            longitude=0.0,
            elevation_meters=0,

            # Timing
            bulletin_time=issue_time or datetime.now(timezone.utc),
            issue_time=issue_time or datetime.now(timezone.utc),
            database_time=database_time,

            # Validity
            valid_from=valid_from or datetime.now(timezone.utc),
            valid_to=valid_to or datetime.now(timezone.utc),
            valid_from_timestamp=valid_from_timestamp,
            valid_to_timestamp=valid_to_timestamp,

            # Metadata
            is_most_recent=True,
            is_prior_version=False,
            raw_taf=raw_taf,
            remarks="",

            # Forecasts
            forecast_periods=forecast_periods
        )

    @staticmethod
    def _parse_taf_period(period_text: str, taf_start: datetime, taf_end: datetime) -> Optional[TAFForecastPeriod]:
        """
        Parse a single TAF forecast period
        
        Args:
            period_text: Text of the forecast period
            taf_start: TAF validity start time
            taf_end: TAF validity end time
            
        Returns:
            TAFForecastPeriod object or None if parsing fails
        """
        if not period_text.strip():
            return None

        # Parse change type
        change_type = None
        probability = None

        if 'FM' in period_text:
            change_type = 'FM'
        elif 'TEMPO' in period_text:
            change_type = 'TEMPO'
        elif 'BECMG' in period_text:
            change_type = 'BECMG'
        elif 'PROB' in period_text:
            change_type = 'PROB'
            prob_match = re.search(r'PROB(\d{2})', period_text)
            if prob_match:
                probability = int(prob_match.group(1))

        # Parse period time
        # Handle None values for taf_start/taf_end - use current time as fallback
        if taf_start is None:
            taf_start = datetime.now()
        if taf_end is None:
            taf_end = datetime.now()

        period_start = taf_start
        period_end = taf_end

        # FM format: FM270200 (DDHHMM)
        fm_match = re.search(r'FM(\d{2})(\d{2})(\d{2})', period_text)
        if fm_match:
            day = int(fm_match.group(1))
            hour = int(fm_match.group(2))
            minute = int(fm_match.group(3))
            try:
                period_start = datetime(
                    taf_start.year, taf_start.month, day, hour, minute, 0)
            except (ValueError, AttributeError):
                pass

        # TEMPO/BECMG format: TEMPO 1215/1224 (DDHH/DDHH)
        temp_match = re.search(r'(\d{2})(\d{2})/(\d{2})(\d{2})', period_text)
        if temp_match and change_type in ['TEMPO', 'BECMG']:
            from_day = int(temp_match.group(1))
            from_hour = int(temp_match.group(2))
            to_day = int(temp_match.group(3))
            to_hour = int(temp_match.group(4))
            try:
                period_start = datetime(
                    taf_start.year, taf_start.month, from_day, from_hour, 0, 0)
                period_end = datetime(
                    taf_start.year, taf_start.month, to_day, to_hour, 0, 0)
            except (ValueError, AttributeError):
                pass

        # Parse wind (e.g., 27010KT, VRB04KT, 36010G20KT)
        wind_dir = None
        wind_speed = None
        wind_gust = None

        wind_match = re.search(
            r'(VRB|[0-9]{3})([0-9]{2,3})(G([0-9]{2,3}))?KT', period_text)
        if wind_match:
            if wind_match.group(1) == 'VRB':
                wind_dir = 'VRB'
            else:
                wind_dir = int(wind_match.group(1))
            wind_speed = int(wind_match.group(2))
            if wind_match.group(4):
                wind_gust = int(wind_match.group(4))

        # Parse visibility (e.g., P6SM, 5SM, 3/4SM)
        visibility = "6+"
        vis_match = re.search(r'P?(\d+(/\d+)?SM|\d+SM)', period_text)
        if vis_match:
            vis_str = vis_match.group(0)
            if vis_str.startswith('P'):
                visibility = vis_str[1:].replace('SM', '') + "+"
            else:
                visibility = vis_str.replace('SM', '')

        # Parse sky conditions
        cloud_layers = []
        cloud_matches = re.findall(
            r'(SKC|CLR|FEW|SCT|BKN|OVC)(\d{3})?(CB|TCU)?', period_text)
        for match in cloud_matches:
            coverage = match[0]
            altitude = int(match[1]) * 100 if match[1] else None
            cloud_type = match[2] if match[2] else None

            cloud_layers.append(TAFCloudLayer(
                coverage=coverage,
                base_altitude_feet=altitude,
                cloud_type=cloud_type
            ))

        # Parse weather phenomena (e.g., -SHRA, TSRA, BR)
        weather_phenomena = None
        wx_codes = ['RA', 'SN', 'DZ', 'FZ', 'SH', 'TS', 'BR',
                    'FG', 'HZ', 'VA', 'DU', 'SA', 'PL', 'GR', 'GS']
        for wx in wx_codes:
            if wx in period_text:
                weather_phenomena = wx
                break

        # Safety check: ensure period_start and period_end are valid datetime objects
        if period_start is None:
            period_start = datetime.now()
        if period_end is None:
            period_end = datetime.now()

        return TAFForecastPeriod(
            valid_from=period_start,
            valid_to=period_end,
            valid_from_timestamp=int(period_start.timestamp()),
            valid_to_timestamp=int(period_end.timestamp()),
            forecast_change_type=change_type,
            probability_percent=probability,
            wind_direction_degrees=wind_dir,
            wind_speed_knots=wind_speed,
            wind_gust_knots=wind_gust,
            visibility=visibility,
            weather_phenomena=weather_phenomena,
            cloud_layers=cloud_layers
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert TAF object to dictionary for JSON serialization"""
        result = {}

        for field_name, field_value in self.__dict__.items():
            if field_value is None:
                continue

            if isinstance(field_value, datetime):
                result[field_name] = field_value.isoformat()
            elif field_name == 'forecast_periods':
                result[field_name] = []
                for period in field_value:
                    period_dict = {}
                    for p_field, p_value in period.__dict__.items():
                        if p_value is None:
                            continue
                        if isinstance(p_value, datetime):
                            period_dict[p_field] = p_value.isoformat()
                        elif p_field == 'cloud_layers':
                            period_dict[p_field] = [
                                {
                                    'coverage': layer.coverage,
                                    'base_altitude_feet': layer.base_altitude_feet,
                                    'cloud_type': layer.cloud_type
                                }
                                for layer in p_value
                            ]
                        elif p_field in ['icing_turbulence', 'temperature_forecasts']:
                            period_dict[p_field] = [
                                item.__dict__ for item in p_value]
                        else:
                            period_dict[p_field] = p_value
                    result[field_name].append(period_dict)
            else:
                result[field_name] = field_value

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert TAF object to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def get_current_conditions(self) -> Optional[TAFForecastPeriod]:
        """Get the forecast period valid for current time"""
        now = datetime.now()
        for period in self.forecast_periods:
            if period.valid_from <= now <= period.valid_to:
                return period
        return None

    def get_periods_with_weather(self) -> List[TAFForecastPeriod]:
        """Get all forecast periods with significant weather"""
        return [period for period in self.forecast_periods
                if period.is_significant_weather()]

    def get_lowest_visibility(self) -> str:
        """Get the lowest visibility forecast in any period"""
        visibilities = []
        for period in self.forecast_periods:
            if period.visibility and period.visibility not in ["6+", "P6SM"]:
                try:
                    vis_num = float(period.visibility.replace(
                        "SM", "").replace("+", ""))
                    visibilities.append(vis_num)
                except ValueError:
                    continue

        if not visibilities:
            return "6+"

        return str(min(visibilities))

    def get_highest_wind_speed(self) -> Optional[int]:
        """Get the highest wind speed forecast in any period"""
        speeds = [period.wind_speed_knots for period in self.forecast_periods
                  if period.wind_speed_knots is not None]
        return max(speeds) if speeds else None

    def validity_hours(self) -> float:
        """Get TAF validity period in hours"""
        delta = self.valid_to - self.valid_from
        return delta.total_seconds() / 3600

    def __str__(self) -> str:
        """Human readable string representation"""
        current = self.get_current_conditions()
        current_info = ""
        if current:
            current_info = (f"\nCurrent: {current.wind_direction_degrees}° at {current.wind_speed_knots} kts, "
                            f"Vis: {current.visibility}, Sky: {[layer.coverage for layer in current.cloud_layers]}")

        return (
            f"TAF {self.station_id} ({self.station_name})\n"
            f"Issued: {self.issue_time.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Valid: {self.valid_from.strftime('%Y-%m-%d %H:%M')} to {self.valid_to.strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"Periods: {len(self.forecast_periods)}\n"
            f"Validity: {self.validity_hours():.1f} hours{current_info}\n"
            f"Raw: {self.raw_taf[:100]}{'...' if len(self.raw_taf) > 100 else ''}"
        )


# Example usage and testing
if __name__ == "__main__":
    # Example data from your JSON file
    example_data = {
        "icaoId": "KORD",
        "dbPopTime": "2025-09-26T23:20:42.176Z",
        "bulletinTime": "2025-09-26T23:20:00.000Z",
        "issueTime": "2025-09-26T23:20:00.000Z",
        "validTimeFrom": 1758931200,
        "validTimeTo": 1759039200,
        "rawTAF": "TAF KORD 262320Z 2700/2806 20008KT P6SM FEW060 FM270200 VRB04KT P6SM SKC FM271500 26011KT P6SM FEW060 FM280100 25006KT P6SM FEW060",
        "mostRecent": 0,
        "remarks": "",
        "lat": 41.96017,
        "lon": -87.93161,
        "elev": 202,
        "prior": 0,
        "name": "Chicago/O'Hare Intl",
        "fcsts": [
            {
                "timeFrom": 1758931200,
                "timeTo": 1758938400,
                "timeBec": None,
                "fcstChange": None,
                "probability": None,
                "wdir": 200,
                "wspd": 8,
                "wgst": None,
                "visib": "6+",
                "clouds": [{"cover": "FEW", "base": 6000, "type": None}],
                "icgTurb": [],
                "temp": []
            }
        ]
    }

    # Create TAF object from API data
    taf = TAF.from_api_response(example_data)

    # Display the parsed data
    print(taf)
    print("\n" + "="*60 + "\n")

    # Show JSON representation
    print("JSON representation:")
    print(taf.to_json())

    # Show some utility methods
    print(f"\nTAF validity: {taf.validity_hours():.1f} hours")
    print(f"Number of forecast periods: {len(taf.forecast_periods)}")
    print(f"Highest wind speed: {taf.get_highest_wind_speed()} knots" if taf.get_highest_wind_speed(
    ) else "No wind data")
    print(f"Lowest visibility: {taf.get_lowest_visibility()}")
