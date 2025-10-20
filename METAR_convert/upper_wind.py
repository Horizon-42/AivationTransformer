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


class UpperWindStationPeriod:
    def __init__(self, valid_time: str, use_period: str, levels: List[UpperWindLevel]):
        self.valid_time = valid_time
        self.use_period = use_period
        self.levels = levels  # [UpperWindLevel, ...]

    def __repr__(self):
        return f"UpperWindStationPeriod(valid_time={self.valid_time}, use_period={self.use_period}, levels={len(self.levels)})"

class UpperWind:
    def __init__(self, station: str, periods: List[UpperWindStationPeriod]):
        # single-station object
        self.station: str = station
        self.periods: List[UpperWindStationPeriod] = periods

    @classmethod
    def parse_bulletin_all_stations(cls, bulletin: str) -> List["UpperWind"]:
        """Parse an Upper Wind bulletin and return a list of UpperWind objects (one per station)."""
        stations_map: Dict[str, List[UpperWindStationPeriod]] = {}

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

            # Normalize and split
            lines = block.split('\n')

            # Collect altitude header lines then compute altitudes
            altitude_lines: List[str] = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if re.match(r"^\s*\d{4,5}", line):
                    altitude_lines.append(line)
                    # collect any immediate continuation lines that start with '|'
                    j = i + 1
                    while j < len(lines) and re.match(r"^\s*\|", lines[j]):
                        altitude_lines.append(lines[j])
                        j += 1
                    i = j
                    break
                i += 1

            if not altitude_lines:
                continue
            altitude_text = " ".join(altitude_lines)
            altitudes = [int(a) for a in re.findall(r"\d{4,5}", altitude_text)]

            # Parse all station rows (support wrapped continuation line)
            while i < len(lines):
                line = lines[i]
                m_station = re.match(r"^\s*([A-Z]{3,4})\s+(.+)", line)
                if m_station:
                    station = m_station.group(1)
                    # Normalize 3-letter domestic code to 4-letter ICAO
                    if len(station) == 3:
                        station = 'C' + station
                    rest = m_station.group(2)
                    # If next line is continuation (not a new station/VALID/alt header/'|'), append it
                    if i + 1 < len(lines) and not re.match(r"^\s*([A-Z]{3,4})\b|^VALID|^\s*\d{4,5}|^\s*\|", lines[i+1]):
                        rest += ' ' + lines[i+1].strip()
                        i += 1

                    values = [v.strip() for v in rest.split('|')]
                    levels: List[UpperWindLevel] = []
                    for k, val in enumerate(values):
                        if k >= len(altitudes):
                            break
                        m_val = re.match(
                            r"(\d+)\s+(\d+)(?:\s+([\-+]?\d+))?", val)
                        if m_val:
                            direction = int(m_val.group(1))
                            speed = int(m_val.group(2))
                            temperature = int(m_val.group(
                                3)) if m_val.group(3) else None
                            levels.append(UpperWindLevel(
                                altitudes[k], direction, speed, temperature))
                        else:
                            levels.append(UpperWindLevel(
                                altitudes[k], None, None, None))

                    stations_map.setdefault(station, []).append(
                        UpperWindStationPeriod(valid_time, use_period, levels)
                    )
                i += 1

        # Build one UpperWind per station
        return [UpperWind(station=s, periods=p) for s, p in stations_map.items()]

    @classmethod
    def from_bulletin_for_station(cls, bulletin: str, station: str) -> "UpperWind":
        """Parse a bulletin and return a single-station UpperWind for the specified station (if present)."""
        all_objs = cls.parse_bulletin_all_stations(bulletin)
        for obj in all_objs:
            if obj.station == station:
                return obj
        # If not found, return empty object with no periods
        return UpperWind(station=station, periods=[])

    def for_station(self, station: str) -> "UpperWind":
        """Return a new UpperWind containing only data for the given station.

        - Keeps the same periods, but each period's stations map is reduced to the specified station.
        - Periods without the station are dropped.
        """
        if station == self.station:
            return UpperWind(station=self.station, periods=self.periods.copy())
        return UpperWind(station=station, periods=[])

    @property
    def valid_time(self) -> str:
        """Get the valid time from the first period (for compatibility)"""
        if self.periods:
            return self.periods[0].valid_time
        return ""

    @property
    def for_use_time(self) -> str:
        """Get the for use time from the first period (for compatibility)"""
        if self.periods:
            return self.periods[0].use_period
        return ""

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
        station = self.station
        for period in self.periods:
            if station not in result:
                result[station] = {}
            for level in period.levels:
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
        """Convert UpperWind object to dictionary (station-first)."""
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

    def to_stationwise_dict(self) -> Dict[str, Dict[str, List[dict]]]:
        """Return dict organized by station -> valid periods -> levels.

        Shape:
        {
          'CYVR': {
            'periods': [
               {
                 'valid_time': '131200Z',
                 'use_period': '06-18',
                 'levels': [ { altitude_ft, direction_deg, speed_kt, temperature_c }, ... ]
               }, ...
            ]
          }, ...
        }
        """
        out: Dict[str, Dict[str, List[dict]]] = {}
        out[self.station] = {
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
        return out

    def __repr__(self):
        return f"UpperWind(station={self.station}, periods={len(self.periods)})"

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
