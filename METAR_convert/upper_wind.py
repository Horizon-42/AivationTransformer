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
        periods = []
        # Split by VALID blocks
        valid_blocks = re.split(r"\nVALID ", bulletin)
        for block in valid_blocks:
            block = block.strip()
            if not block:
                continue
            # Extract valid time and use period
            valid_match = re.match(r"VALID (\d{6}Z) FOR USE ([\d\-]+)", block)
            if valid_match:
                valid_time = valid_match.group(1)
                use_period = valid_match.group(2)
            else:
                valid_time = "UNKNOWN"
                use_period = "UNKNOWN"
            # Find altitude header row
            altitude_row = re.search(r"\n\s*(\d{4,5}(?:\s*\|\s*\d{4,5})+)", block)
            if not altitude_row:
                continue
            altitudes = [int(a) for a in re.findall(r"\d{4,5}", altitude_row.group(1))]
            # Find station rows (e.g., YVR, YYC)
            stations = {}
            for line in block.splitlines():
                station_match = re.match(r"^([A-Z]{3,4})\s+(.+)", line)
                if station_match:
                    station = station_match.group(1)
                    values = [v.strip() for v in station_match.group(2).split('|')]
                    levels = []
                    for i, val in enumerate(values):
                        m = re.match(r"(\d{3})\s+(\d{1,2})(?:\s+([\-+]?\d+))?", val)
                        if m:
                            direction = int(m.group(1))
                            speed = int(m.group(2))
                            temperature = int(m.group(3)) if m.group(3) else None
                            levels.append(UpperWindLevel(altitudes[i], direction, speed, temperature))
                        else:
                            levels.append(UpperWindLevel(altitudes[i], None, None, None))
                    stations[station] = levels
            periods.append(UpperWindPeriod(valid_time, use_period, stations))
        return cls(periods)

    def __repr__(self):
        return f"UpperWind(periods={len(self.periods)})"

# Example usage:
if __name__ == "__main__":
    import json
    with open("METAR_convert/weather_data/multi_station_simple.json", "r") as f:
        data = json.load(f)
    upper_wind_entry = next(
        (v for k, v in data["weather_data"].items() if "Upper Wind" in k), None
    )
    if upper_wind_entry:
        upper_wind = UpperWind.from_bulletin(upper_wind_entry["bulletin"])
        for period in upper_wind.periods:
            print(f"VALID {period.valid_time} FOR USE {period.use_period}")
            for station, levels in period.stations.items():
                print(f"  {station}:")
                for level in levels:
                    print(f"    {level}")