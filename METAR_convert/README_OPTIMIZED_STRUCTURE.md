# Nav Canada Optimized JSON Structure

## Overview
The optimized structure groups weather data by **type** first, then by **station code**, making it much easier to parse and access specific information.

## Structure Format

```json
{
  "session_info": {
    "timestamp": "2025-10-12T16:46:43Z",
    "stations_requested": ["CYVR", "CYYC"],
    "source": "Nav Canada Weather Recall",
    "extraction_method": "optimized_structure"
  },
  "weather_data": {
    "METAR": {
      "CYVR": [
        {
          "bulletin": "METAR CYVR 121600Z 13005KT 20SM...",
          "row_index": 1,
          "extraction_time": "2025-10-12T16:46:42Z"
        }
      ],
      "CYYC": [...]
    },
    "TAF": {
      "CYVR": [...],
      "CYYC": [...]
    },
    "Upper_Wind": [
      {
        "bulletin": "VALID 131200Z FOR USE 06-18...",
        "row_index": 3,
        "extraction_time": "2025-10-12T16:46:42Z"
      }
    ],
    "NOTAM": {
      "CYVR": [...],
      "CYYC": [...],
      "Other": [...]
    }
  },
  "extraction_summary": {
    "total_entries": 61,
    "metar_records": 2,
    "taf_records": 2,
    "notam_records": 56,
    "upper_wind_records": 1,
    "stations_found": ["CYVR", "CYYC", "CYDC", "CYYJ"]
  }
}
```

## Key Features

### 1. **Type-Based Organization**
Data is organized into four main categories:
- **METAR**: Current weather observations
- **TAF**: Terminal Aerodrome Forecasts
- **Upper_Wind**: Upper winds aloft (covers multiple stations)
- **NOTAM**: Notices to Airmen

### 2. **Station Grouping**
- METAR, TAF, and NOTAM are grouped by **station code** (ICAO identifier)
- Upper_Wind is kept as a **flat list** since it covers multiple stations in a single bulletin

### 3. **Easy Access Patterns**

```python
# Load data
with open('weather_data/optimized_example.json', 'r') as f:
    data = json.load(f)

weather_data = data['weather_data']

# Access METAR for specific station
cyvr_metar = weather_data['METAR']['CYVR']
print(f"CYVR has {len(cyvr_metar)} METAR observation(s)")
print(cyvr_metar[0]['bulletin'])

# Access all TAF stations
for station, taf_entries in weather_data['TAF'].items():
    print(f"{station}: {len(taf_entries)} forecast(s)")

# Access upper winds
upper_winds = weather_data['Upper_Wind']
for wind in upper_winds:
    print(wind['bulletin'])

# Access NOTAMs by station
if 'CYYC' in weather_data['NOTAM']:
    cyyc_notams = weather_data['NOTAM']['CYYC']
    print(f"CYYC has {len(cyyc_notams)} NOTAM(s)")
```

## Advantages Over Flat Structure

### Old Structure (Simple)
```json
{
  "weather_data": {
    "entry_1": {
      "metadata": "METAR CYVR",
      "bulletin": "METAR CYVR 121600Z..."
    },
    "entry_2": {
      "metadata": "TAF CYVR",
      "bulletin": "TAF CYVR 121440Z..."
    }
  }
}
```
**Issues:**
- ❌ Need to iterate all entries to find specific data type
- ❌ Need to parse metadata to extract station codes
- ❌ No clear grouping by station
- ❌ Hard to count records by type

### New Structure (Optimized)
```json
{
  "weather_data": {
    "METAR": {
      "CYVR": [{...}]
    },
    "TAF": {
      "CYVR": [{...}]
    }
  }
}
```
**Benefits:**
- ✅ Direct access: `data['METAR']['CYVR']`
- ✅ Easy to iterate by type or station
- ✅ Clear hierarchical structure
- ✅ Summary provides quick counts

## Usage Examples

### Example 1: Extract Single Station
```python
from navcanada_simple_client import NavCanadaSimpleClient

client = NavCanadaSimpleClient()
data = client.get_simple_weather_data(['CYVR'])
client.save_simple_data(data, 'cyvr_weather.json')
```

### Example 2: Extract Multiple Stations
```python
client = NavCanadaSimpleClient()
data = client.get_simple_weather_data(['CYVR', 'CYYC', 'CYEG'])
client.save_simple_data(data, 'multi_station.json')
```

### Example 3: Access Specific Data
```python
import json

with open('multi_station.json', 'r') as f:
    data = json.load(f)

# Get all METAR stations
metar_stations = data['weather_data']['METAR'].keys()
print(f"METAR available for: {', '.join(metar_stations)}")

# Get specific station's TAF
if 'CYYC' in data['weather_data']['TAF']:
    cyyc_taf = data['weather_data']['TAF']['CYYC'][0]['bulletin']
    print(f"Calgary TAF: {cyyc_taf}")
```

## Data Fields

Each bulletin entry contains:
- **bulletin**: The actual weather data text
- **row_index**: Position in the original table
- **extraction_time**: UTC timestamp when extracted

## Summary Information

The `extraction_summary` provides:
- **total_entries**: Total number of data entries extracted
- **metar_records**: Count of METAR observations
- **taf_records**: Count of TAF forecasts
- **notam_records**: Count of NOTAMs
- **upper_wind_records**: Count of upper wind reports
- **stations_found**: List of all station codes discovered

## Special Cases

### Upper Winds
Upper winds are kept as a **flat list** (not grouped by station) because:
- A single upper wind bulletin covers **multiple stations** (e.g., YVR, YYC, YEG)
- The bulletin contains a grid/table format with data for many locations
- Station-level grouping would require parsing the bulletin content

### NOTAM Categories
NOTAMs may include an "Other" category for:
- NOTAMs without clear station identifiers
- Administrative NOTAMs (e.g., J4935/25)
- System-wide notices

## Migration from Simple Structure

If you have code using the old flat structure:

**Old Code:**
```python
for key, entry in weather_data.items():
    metadata = entry['metadata']
    bulletin = entry['bulletin']
    if 'METAR' in metadata and 'CYVR' in metadata:
        process_metar(bulletin)
```

**New Code:**
```python
for entry in weather_data['METAR'].get('CYVR', []):
    bulletin = entry['bulletin']
    process_metar(bulletin)
```

## Files Generated

Running the examples creates:
- `weather_data/optimized_example.json` - Single station example (CYVR)
- `weather_data/multi_station_optimized.json` - Multiple stations (CYVR, CYYC)

## Performance

The optimized structure provides:
- **Faster lookups**: O(1) access to specific station/type vs O(n) iteration
- **Better organization**: Clear separation of data types
- **Easier parsing**: No need to parse metadata strings
- **Cleaner code**: More readable data access patterns
