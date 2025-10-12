# Upper Wind Parser - Updated for Optimized Structure

## Overview
The `upper_wind.py` module has been updated to parse upper wind data from the new optimized Nav Canada JSON structure.

## Changes Made

### 1. **Updated Data Access Pattern**

**Old Structure (Flat):**
```python
# Had to search through all entries
upper_wind_entry = next(
    (v for k, v in data["weather_data"].items() if "Upper Wind" in k), None
)
```

**New Structure (Optimized):**
```python
# Direct access to Upper_Wind list
upper_wind_list = data["weather_data"].get("Upper_Wind", [])

for entry in upper_wind_list:
    upper_wind = UpperWind.from_bulletin(entry["bulletin"])
```

### 2. **Improved Parsing Logic**

The parser now correctly handles:
- ✅ Multi-line altitude headers (wrapped text)
- ✅ Multi-line station data (wrapped text)
- ✅ Multiple forecast periods (VALID blocks)
- ✅ Missing data indicators (e.g., "0 -15" format)
- ✅ Temperature with/without data

### 3. **Key Classes**

```python
class UpperWindLevel:
    # Represents wind data at a single altitude
    - altitude_ft: int
    - direction_deg: Optional[int]  # 0-360
    - speed_kt: Optional[int]       # knots
    - temperature_c: Optional[int]  # Celsius

class UpperWindPeriod:
    # Represents one forecast period
    - valid_time: str              # e.g., "131200Z"
    - use_period: str              # e.g., "06-18"
    - stations: Dict[str, List[UpperWindLevel]]

class UpperWind:
    # Container for all periods
    - periods: List[UpperWindPeriod]
    - from_bulletin(bulletin: str) -> UpperWind  # Parser
```

## Usage Examples

### Basic Parsing
```python
import json
from upper_wind import UpperWind

# Load optimized data
with open("weather_data/optimized_example.json", "r") as f:
    data = json.load(f)

# Parse upper winds
for entry in data["weather_data"]["Upper_Wind"]:
    upper_wind = UpperWind.from_bulletin(entry["bulletin"])
    
    for period in upper_wind.periods:
        print(f"VALID {period.valid_time} FOR USE {period.use_period}")
        for station, levels in period.stations.items():
            print(f"  {station}: {len(levels)} altitude levels")
```

### Find Strong Winds
```python
# Find all winds >50kt
for entry in data["weather_data"]["Upper_Wind"]:
    upper_wind = UpperWind.from_bulletin(entry["bulletin"])
    
    for period in upper_wind.periods:
        for station, levels in period.stations.items():
            strong_winds = [l for l in levels if l.speed_kt and l.speed_kt > 50]
            if strong_winds:
                print(f"{station} @ {period.valid_time}:")
                for wind in strong_winds:
                    print(f"  FL{wind.altitude_ft//100}: {wind.speed_kt}kt")
```

### Get Wind at Specific Altitude
```python
# Get winds at FL300 (30,000ft)
target_altitude = 30000

for entry in data["weather_data"]["Upper_Wind"]:
    upper_wind = UpperWind.from_bulletin(entry["bulletin"])
    
    for period in upper_wind.periods:
        for station, levels in period.stations.items():
            fl300_wind = next((l for l in levels if l.altitude_ft == target_altitude), None)
            if fl300_wind and fl300_wind.speed_kt:
                print(f"{station} FL300: {fl300_wind.direction_deg}° {fl300_wind.speed_kt}kt")
```

### Export to Dictionary
```python
# Convert parsed data to dictionary for further processing
parsed_winds = []

for entry in data["weather_data"]["Upper_Wind"]:
    upper_wind = UpperWind.from_bulletin(entry["bulletin"])
    
    for period in upper_wind.periods:
        parsed_winds.append({
            "valid_time": period.valid_time,
            "use_period": period.use_period,
            "stations": {
                station: [
                    {
                        "altitude_ft": l.altitude_ft,
                        "direction_deg": l.direction_deg,
                        "speed_kt": l.speed_kt,
                        "temperature_c": l.temperature_c
                    }
                    for l in levels
                ]
                for station, levels in period.stations.items()
            }
        })
```

## Sample Output

### Parsed Data Format
```
VALID 131200Z FOR USE 06-18
  Station: YVR
  Altitude   Direction    Speed      Temperature 
  --------------------------------------------------
  3000ft     50°          18kt       N/A         
  6000ft     70°          30kt       -2°C        
  9000ft     80°          14kt       -7°C        
  12000ft    50°          19kt       -13°C       
  18000ft    50°          17kt       -26°C       
  24000ft    30°          57kt       -32°C       
  30000ft    30°          118kt      -39°C       ⚠️ STRONG WIND!
  34000ft    30°          114kt      -45°C       ⚠️ STRONG WIND!
```

## Aviation Context

### Altitude Levels
Standard upper wind reporting levels (in feet):
- 3,000 - Low level winds
- 6,000 - Low altitude cruise
- 9,000-12,000 - Mid-level winds
- 18,000-24,000 - High altitude cruise (FL180-FL240)
- 30,000-39,000 - Jet stream levels (FL300-FL390)
- 45,000-53,000 - Very high altitude (FL450-FL530)

### Wind Speed Interpretation
- **Light:** <15kt
- **Moderate:** 15-25kt
- **Strong:** 25-50kt
- **Very Strong:** >50kt (Jet stream winds)

### Valid Time Format
- **131200Z**: Day 13, 1200 UTC (Zulu time)
- **FOR USE 06-18**: Use for operations between 0600-1800 UTC

## Testing

Run the examples:
```bash
cd METAR_convert
python upper_wind_examples.py
```

Or test the basic parser:
```bash
python upper_wind.py
```

## Integration with Flight Planning

The parsed upper wind data can be used for:
1. **Route Planning**: Optimize routes to use tailwinds or avoid headwinds
2. **Fuel Calculations**: More accurate fuel burn estimates
3. **Flight Level Selection**: Choose optimal cruising altitude
4. **Turbulence Avoidance**: Strong winds often indicate turbulence
5. **Time Estimates**: Calculate ground speed for ETA calculations

## Next Steps

Potential enhancements:
- [ ] Add wind component calculations (headwind/tailwind for specific routes)
- [ ] Interpolate winds for altitudes between reported levels
- [ ] Calculate crosswind components
- [ ] Add wind shear detection
- [ ] Generate visual wind profile charts
