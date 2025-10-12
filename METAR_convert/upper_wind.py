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
    def __init__(self, altitude_ft: int, direction_deg: Optional[int], speed_kt: Optional[int], temperature_c: Optional[int]):
        self.altitude_ft = altitude_ft
        self.direction_deg = direction_deg
        self.speed_kt = speed_kt
        self.temperature_c = temperature_c

    def __repr__(self):
        return f"{self.altitude_ft}ft: {self.direction_deg or '-'}°/{self.speed_kt or '-'}kt/{self.temperature_c if self.temperature_c is not None else '-'}°C"

class UpperWindPeriod:
    def __init__(self, valid_time: str, use_period: str, stations: Dict[str, List[UpperWindLevel]]):
        self.valid_time = valid_time
        self.use_period = use_period
        self.stations = stations  # {station_code: [UpperWindLevel, ...]}

    def __repr__(self):
        return f"UpperWindPeriod(valid_time={self.valid_time}, use_period={self.use_period}, stations={list(self.stations.keys())})"

class UpperWind:
    def __init__(self, periods: List[UpperWindPeriod]):
        self.periods = periods

    @classmethod
    def from_bulletin(cls, bulletin: str) -> "UpperWind":
        """Parse upper wind bulletin into structured data"""
        periods = []

        # Split by VALID blocks
        valid_blocks = re.split(r"VALID ", bulletin)

        for block in valid_blocks:
            block = block.strip()
            if not block:
                continue

            # Extract valid time and use period from the first line
            first_line_match = re.match(
                r"(\d{6}Z)\s+FOR\s+USE\s+([\d\-]+)", block)
            if first_line_match:
                valid_time = first_line_match.group(1)
                use_period = first_line_match.group(2)
            else:
                # Skip if we can't parse the header
                continue

            # Find altitude header row - handle multi-line altitudes
            # Normalize whitespace and reconstruct lines
            lines = block.split('\n')
            altitude_line = ""
            station_line = ""

            for i, line in enumerate(lines):
                # Look for altitude header (starts with numbers)
                if re.search(r'^\s*\d{4,5}', line):
                    # This might be altitude header
                    altitude_line = line
                    # Check if next line continues (might be wrapped)
                    if i + 1 < len(lines) and re.search(r'^\s*\|', lines[i + 1]):
                        altitude_line += lines[i + 1]
                # Look for station data (starts with 3-4 letter station code)
                elif re.match(r'^([A-Z]{3,4})\s+', line):
                    station_line = line
                    # Check if next line continues (might be wrapped)
                    if i + 1 < len(lines) and not re.match(r'^([A-Z]{3,4})\s+|^VALID', lines[i + 1]):
                        station_line += lines[i + 1]

            # Extract altitudes
            if not altitude_line:
                continue
            altitudes = [int(a) for a in re.findall(r'\d{4,5}', altitude_line)]

            # Parse station data
            stations = {}
            if station_line:
                station_match = re.match(r'^([A-Z]{3,4})\s+(.+)', station_line)
                if station_match:
                    station = station_match.group(1)
                    # Split by | delimiter
                    values = [v.strip() for v in station_match.group(2).split('|')]

                    levels = []
                    for i, val in enumerate(values):
                        if i >= len(altitudes):
                            break
                        # Match wind direction, speed, and optional temperature
                        # Format: "360 33 -40" or "50 18" or "0 -15"
                        m = re.match(
                            r'(\d+)\s+(\d+)(?:\s+([\-+]?\d+))?', val.strip())
                        if m:
                            direction = int(m.group(1))
                            speed = int(m.group(2))
                            temperature = int(m.group(3)) if m.group(3) else None
                            levels.append(UpperWindLevel(altitudes[i], direction, speed, temperature))
                        else:
                            # No data for this level
                            levels.append(UpperWindLevel(altitudes[i], None, None, None))

                    stations[station] = levels

            if stations:
                periods.append(UpperWindPeriod(
                    valid_time, use_period, stations))

        return cls(periods)

    @property
    def valid_time(self) -> str:
        """Get the valid time from the first period (for compatibility)"""
        return self.periods[0].valid_time if self.periods else ""

    @property
    def for_use_time(self) -> str:
        """Get the for use time from the first period (for compatibility)"""
        return self.periods[0].use_period if self.periods else ""

    @property
    def data_based_on(self) -> str:
        """Get data based on time (for compatibility) - same as valid time"""
        return self.valid_time

    @property
    def station_data(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Get station data in a flat structure (for compatibility)
        Returns: Dict[station, Dict[altitude, Dict[wind/temp]]]
        Example: {'CYVR': {'9000': {'wind': '270/35', 'temp': '-04'}}}
        """
        result = {}
        for period in self.periods:
            for station, levels in period.stations.items():
                if station not in result:
                    result[station] = {}
                for level in levels:
                    alt_str = str(level.altitude_ft)
                    data = {}
                    if level.direction_deg is not None and level.speed_kt is not None:
                        data['wind'] = f"{level.direction_deg:03d}/{level.speed_kt:02d}"
                    if level.temperature_c is not None:
                        data['temp'] = f"{level.temperature_c:+03d}"
                    if data:
                        result[station][alt_str] = data
        return result

    def to_dict(self) -> dict:
        """Convert UpperWind object to dictionary for JSON serialization"""
        return {
            'periods': [
                {
                    'valid_time': period.valid_time,
                    'use_period': period.use_period,
                    'stations': {
                        station: [
                            {
                                'altitude_ft': level.altitude_ft,
                                'direction_deg': level.direction_deg,
                                'speed_kt': level.speed_kt,
                                'temperature_c': level.temperature_c
                            }
                            for level in levels
                        ]
                        for station, levels in period.stations.items()
                    }
                }
                for period in self.periods
            ]
        }

    def __repr__(self):
        return f"UpperWind(periods={len(self.periods)})"

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
            upper_wind = UpperWind.from_bulletin(upper_wind_entry["bulletin"])

            for period in upper_wind.periods:
                print(
                    f"\nVALID {period.valid_time} FOR USE {period.use_period}")
                for station, levels in period.stations.items():
                    print(f"  {station}:")
                    for level in levels:
                        print(f"    {level}")
            print()
    else:
        print("No upper wind data found in the optimized structure.")
