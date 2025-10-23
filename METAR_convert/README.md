# Nav Canada Simple Weather Client

A simplified client for extracting weather data from Nav Canada's Weather Recall service.

## Overview

This client uses a simple approach:
- **Metadata column** → **Key** (e.g., "METAR\nCYVR", "TAF\nCYVR", "Upper Wind")
- **Bulletin column** → **Value** (the actual weather data text)
- No complex parsing or data transformation

### Database Integration

The toolchain now ships with an **optional SQLite persistence layer** powered by SQLAlchemy. When you run `data_query_canada_stations_v2.py`, decoded METAR/TAF/Upper-Wind/SIGMET objects are saved to `weather_data/weather.db`. Existing workflows remain unchanged—if you instantiate `NavCanadaWeatherServer` without a repository, no database is touched.

```python
from storage import SQLiteWeatherRepository
from navcanada_weather_server import NavCanadaWeatherServer

repository = SQLiteWeatherRepository("weather_data/weather.db")
server = NavCanadaWeatherServer(repository=repository)
response = server.get_weather(["CYVR", "CYYC"])
repository.close()
```

The repository now persists the decoded objects themselves:

- `stations` contains a canonical record for each ICAO identifier (name, coordinates, elevation). It is automatically seeded with the validated Canadian station catalog.
- `metar_observations`, `metar_cloud_layers`, and `metar_weather` capture the structured `METAR` dataclass plus its nested cloud layers and weather codes.
- `taf_bulletins` with child tables (`taf_forecast_periods`, `taf_cloud_layers`, `taf_icing_turbulence`, `taf_temperature_forecasts`) retain each parsed forecast period from `taf.py`.
- `upper_wind_periods` and `upper_wind_levels` store the parsed altitude grids from `upper_wind.py`.
- `sigmet_reports` and `sigmet_area_points` persist the parsed polygons from `sigmet.py`.

During initialization the repository backfills any legacy databases—creating the `stations` table, rewiring METAR/TAF/Upper-Wind tables to reference it, and migrating old coordinate columns. Fresh installs simply reuse the seeded catalog, but you can still extend it by writing additional `Station` rows in the database.

## Files

- `navcanada_simple_client.py` - Main simple client class
- `navcanada_simple_examples.py` - Usage examples and demonstrations
- `weather_data/` - Output directory for JSON files

## Quick Start

```python
from navcanada_simple_client import NavCanadaSimpleClient

# Single station
with NavCanadaSimpleClient(headless=True) as client:
    results = client.get_simple_weather_data(['CYVR'])
    client.save_simple_data(results, "my_weather_data.json")
```

## Example Output Structure

```json
{
  "session_info": {
    "timestamp": "2025-10-11T13:39:05.632654+00:00",
    "stations_requested": ["CYVR"],
    "source": "Nav Canada Weather Recall",
    "extraction_method": "simple_metadata_bulletin"
  },
  "weather_data": {
    "entry_000_METAR\\nCYVR": {
      "metadata": "METAR\\nCYVR",
      "bulletin": "METAR CYVR 111300Z 12004KT 6SM -RA BR FEW005 BKN056 OVC071 11/11 A2980 RMK SF1SC6AC1 SLP093=",
      "row_index": 1,
      "extraction_time": "2025-10-11T13:39:08.703609+00:00"
    },
    "entry_002_Upper_Wind": {
      "metadata": "Upper Wind",
      "bulletin": "VALID 120600Z FOR USE 00-12\\n  3000 | 6000 | 9000 | 12000 | 18000 | 24000 | 30000...\\nYVR 300 16 | 300 16 0 | 300 15 -4 | 310 20 -9...",
      "row_index": 3,
      "extraction_time": "2025-10-11T13:39:08.727488+00:00"
    }
  },
  "extraction_summary": {
    "total_entries": 41,
    "stations_found": ["CYVR"],
    "extraction_time": "2025-10-11T13:39:08.998426+00:00"
  }
}
```

## Data Types Extracted

- **METAR**: Current weather observations
- **TAF**: Terminal Aerodrome Forecasts
- **Upper Wind**: Upper winds data with altitude levels
- **NOTAM**: Notices to Airmen
- **RSC**: Runway Surface Conditions (within NOTAMs)

## Usage Examples

Run the examples:
```bash
python3 navcanada_simple_examples.py
```

## Sample Data Files

- `simple_example.json` - Single station (CYVR) data
- `multi_station_simple.json` - Multi-station (CYVR + CYYC) data

## Requirements

- Python 3.7+
- Selenium WebDriver
- Chrome browser
- webdriver-manager

## Installation Dependencies

```bash
pip install selenium webdriver-manager
```

## Features

✅ **Simple Structure**: Metadata → Key, Bulletin → Value  
✅ **Complete Data**: Captures all search results exactly as displayed  
✅ **Upper Winds**: Successfully extracts upper winds data with altitude levels  
✅ **Multi-Station**: Supports searching multiple stations simultaneously  
✅ **No Data Loss**: Direct extraction without complex parsing  
✅ **Fast Processing**: Minimal overhead, direct table extraction  

## Test Results

- ✅ **Single station (CYVR)**: 41 entries extracted
- ✅ **Multi-station (CYVR+CYYC)**: 61 entries extracted  
- ✅ **Success rate**: 100% station coverage
- ✅ **Data types**: METAR, TAF, Upper Winds, NOTAMs, RSC data

## Advantages Over Complex Parsers

1. **Simplicity**: No complex data structures or parsing logic
2. **Reliability**: Direct extraction reduces parsing errors  
3. **Completeness**: Captures all data exactly as shown on the website
4. **Maintainability**: Simple code, easy to understand and modify
5. **Performance**: Faster execution with minimal processing overhead