"""
Upper Wind Data Parser for Nav Canada Weather

This module parses upper wind data from the optimized Nav Canada JSON structure.

New Optimized Structure:
    {
        "weather_data": {
            "Upper_Wind": [
                {
                    "bulletin": "VALID 131200Z FOR USE 06-18...",
                    "row_index": 3,
                    "extraction_time": "2025-10-12T16:46:42Z"
                }
            ]
        }
    }

Usage:
    from upper_wind import UpperWind
    import json
    
    # Load optimized data
    with open("weather_data/optimized_example.json", "r") as f:
        data = json.load(f)
    
    # Parse upper wind bulletins
    for entry in data["weather_data"]["Upper_Wind"]:
        upper_wind = UpperWind.from_bulletin(entry["bulletin"])
        # Process the parsed data...
"""

import re
from typing import Dict, List, Optional


class UpperWindLevel:
    """Represents wind and temperature at a single altitude for a period."""
    def __init__(self, altitude_ft: int, direction_deg: Optional[int], speed_kt: Optional[int], temperature_c: Optional[int]):
        self.altitude_ft = altitude_ft
        self.direction_deg = direction_deg
        self.speed_kt = speed_kt
        self.temperature_c = temperature_c

    def __repr__(self):
        return f"{self.altitude_ft}ft: {self.direction_deg or '-'}°/{self.speed_kt or '-'}kt/{self.temperature_c if self.temperature_c is not None else '-'}°C"


class UpperWindPeriod:
    """Represents a single valid time/use period for a station, with all altitude levels."""
    def __init__(self, valid_time: str, use_period: str, levels: List[UpperWindLevel]):
        self.valid_time = valid_time
        self.use_period = use_period
        self.levels = levels

    def __repr__(self):
        return f"UpperWindPeriod(valid_time={self.valid_time}, use_period={self.use_period}, levels={len(self.levels)})"


class UpperWind:
    def to_stationwise_dict(self) -> Dict[str, Dict[str, List[dict]]]:
        """Return dict organized by station -> valid periods -> levels (for compatibility)."""
        return {
            self.station: {
                'periods': [
                    {
                        'valid_time': p.valid_time,
                        'use_period': p.use_period,
                        'levels': [
                            {
                                'altitude_ft': lvl.altitude_ft,
                                'direction_deg': lvl.direction_deg,
                                'speed_kt': lvl.speed_kt,
                                'temperature_c': lvl.temperature_c
                            } for lvl in p.levels
                        ]
                    }
                    for p in self.periods
                ]
            }
        }
    """Represents all upper wind periods for a single station."""

    def __init__(self, station: str, periods: List[UpperWindPeriod]):
        self.station: str = station
        self.periods: List[UpperWindPeriod] = periods

    @classmethod
    def parse_bulletin_all_stations(cls, bulletin: str) -> List["UpperWind"]:
        """Parse a bulletin and return a list of UpperWind objects (one per station, all periods)."""
        stations_map: Dict[str, List[UpperWindPeriod]] = {}
        valid_blocks = re.split(r"(?=VALID )", bulletin)
        for block in valid_blocks:
            lines = block.split("\n")
            block = block.strip()
            if not block:
                continue
            first_line_match = re.match(
                r"VALID (\d{6}Z)\s+FOR\s+USE\s+([\d\-]+)", block)
            if not first_line_match:
                continue
            valid_time = first_line_match.group(1)
            use_period = first_line_match.group(2)
            i = 0
            altitude_line = None
            while i < len(lines):
                line = lines[i]
                if len(re.findall(r"\d{4,5}", line)) >= 2:
                    altitude_line = line
                    i += 1
                    break
                i += 1
            if not altitude_line:
                continue
            altitudes = [int(x) for x in re.findall(r"\d{4,5}", altitude_line)]
            while i < len(lines):
                line = lines[i]
                m_station = re.match(r"^\s*([A-Z]{3,4})\s+(.+)", line)
                if m_station:
                    station = m_station.group(1).upper()
                    if len(station) == 3:
                        station = 'C' + station
                    rest = m_station.group(2)
                    while i + 1 < len(lines) and not re.match(r"^\s*([A-Z]{3,4})\b|^VALID|^\s*\d{4,5}|^\s*\|", lines[i+1]):
                        rest += ' ' + lines[i+1].strip()
                        i += 1
                    values = [v.strip() for v in rest.split('|')]
                    if len(values) < len(altitudes):
                        values += [''] * (len(altitudes) - len(values))
                    elif len(values) > len(altitudes):
                        values = values[:len(altitudes)]
                    levels = []
                    for k, alt in enumerate(altitudes):
                        val = values[k] if k < len(values) else ''
                        m_val = re.match(
                            r"(\d{1,3})\s+(\d{1,3})(?:\s+([\-+]?\d+))?", val)
                        if m_val:
                            direction = int(m_val.group(1))
                            speed = int(m_val.group(2))
                            temperature = int(m_val.group(
                                3)) if m_val.group(3) else None
                            levels.append(UpperWindLevel(
                                alt, direction, speed, temperature))
                        else:
                            levels.append(UpperWindLevel(
                                alt, None, None, None))
                    stations_map.setdefault(station, []).append(
                        UpperWindPeriod(valid_time, use_period, levels)
                    )
                i += 1
        return [UpperWind(station=s, periods=p) for s, p in stations_map.items()]


    @classmethod
    def from_bulletin_for_station(cls, bulletin: str, station: str) -> "UpperWind":
        """Parse a bulletin and return UpperWind for the specified station (if present), else empty."""
        for obj in cls.parse_bulletin_all_stations(bulletin):
            if obj.station == station:
                return obj
        return UpperWind(station=station, periods=[])


    @property
    def valid_time(self) -> str:
        """Return valid time from the first period, or empty string."""
        return self.periods[0].valid_time if self.periods else ""

    @property
    def use_period(self) -> str:
        """Return use period from the first period, or empty string."""
        return self.periods[0].use_period if self.periods else ""


    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            'station': self.station,
            'periods': [
                {
                    'valid_time': p.valid_time,
                    'use_period': p.use_period,
                    'levels': [
                        {
                            'altitude_ft': lvl.altitude_ft,
                            'direction_deg': lvl.direction_deg,
                            'speed_kt': lvl.speed_kt,
                            'temperature_c': lvl.temperature_c
                        } for lvl in p.levels
                    ]
                }
                for p in self.periods
            ]
        }


    def __repr__(self):
        return f"UpperWind(station={self.station}, periods={len(self.periods)})"


class UpperWindMerger:
    """Utility to merge multiple bulletins into station-wise periods."""
    @staticmethod
    def merge_bulletins(bulletins: List[str]) -> Dict[str, List[UpperWindPeriod]]:
        from collections import defaultdict
        station_map = defaultdict(list)
        for bulletin in bulletins:
            for uw in UpperWind.parse_bulletin_all_stations(bulletin):
                station_map[uw.station].extend(uw.periods)
        return station_map

# Example usage:
if __name__ == "__main__":
    import json

    # Load data from optimized structure
    with open("weather_data/optimized_example.json", "r") as f:
        data = json.load(f)

    # Access Upper_Wind from the new optimized structure
    upper_wind_list = data["weather_data"].get("Upper_Wind", [])

    if upper_wind_list:
        print(f"Found {len(upper_wind_list)} upper wind report(s)\n")

        # Parse each upper wind bulletin
        for i, upper_wind_entry in enumerate(upper_wind_list, 1):
            print(f"=== Upper Wind Report #{i} ===")
            winds = UpperWind.parse_bulletin_all_stations(
                upper_wind_entry["bulletin"])

            for uw in winds:
                print(f"\nStation {uw.station}:")
                for p in uw.periods:
                    print(f"  VALID {p.valid_time} FOR USE {p.use_period}")
                    for level in p.levels:
                        print(f"    {level}")
            print()
    else:
        print("No upper wind data found in the optimized structure.")
