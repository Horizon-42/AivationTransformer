# METAR_convert Tests and Examples

This directory contains all test files and usage examples for the METAR_convert package.

## Structure

```
tests/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── test_metar_examples.py         # METAR parsing examples
├── test_taf_examples.py           # TAF parsing examples
├── test_upper_wind_examples.py    # Upper wind parsing examples
├── test_navcanada_examples.py     # Nav Canada client examples
└── test_navcanada_server.py       # Nav Canada server examples (NEW)
```

## Running Examples

All test files can be run directly from the tests directory or from the parent METAR_convert directory.

### From the tests directory:

```bash
cd METAR_convert/tests
python test_metar_examples.py
python test_taf_examples.py
python test_upper_wind_examples.py
python test_navcanada_examples.py
python test_navcanada_server.py
```

### From the METAR_convert directory:

```bash
cd METAR_convert
python tests/test_metar_examples.py
python tests/test_taf_examples.py
python tests/test_upper_wind_examples.py
python tests/test_navcanada_examples.py
python tests/test_navcanada_server.py
```

## Example Files Overview

### test_metar_examples.py
Demonstrates METAR (weather observation) parsing:
- Parse single station from optimized JSON
- Parse multiple stations
- Export to formatted JSON
- Extract specific weather parameters

**Required data file:** `weather_data/optimized_weather.json`

### test_taf_examples.py
Demonstrates TAF (forecast) parsing:
- Parse forecasts from optimized JSON
- Parse change periods (FM, TEMPO, BECMG)
- Compare forecasts between stations
- Detect adverse weather conditions
- Export forecast data

**Required data file:** `weather_data/optimized_weather.json`

### test_upper_wind_examples.py
Demonstrates upper wind parsing:
- Parse winds aloft data
- Find strong winds (>50 knots)
- Query winds at specific altitudes
- Export wind data

**Required data file:** `weather_data/optimized_weather.json`

### test_navcanada_examples.py
Demonstrates Nav Canada data extraction:
- Extract optimized weather data from Nav Canada website
- Handle multiple stations
- Analyze extracted data structure
- Save data to JSON files

**Note:** This example requires Selenium WebDriver and internet connection.

### test_navcanada_server.py
Demonstrates the Nav Canada Weather Server (similar interface to weather_data_server):
- Query Nav Canada and get parsed METAR, TAF, Upper Wind objects
- Save intermediate JSON data during extraction
- Get specific weather types (METAR-only, TAF-only, Upper Winds-only)
- Compare weather across multiple stations
- Export parsed objects to JSON

**Input:** List of station IDs (e.g., ['CYVR', 'CYYC'])
**Output:** Parsed METAR, TAF, and Upper Wind objects

**Note:** This example requires Selenium WebDriver and internet connection.

## Import Strategy

All test files use the following pattern to import parent modules:

```python
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now can import from parent package
from metar import METAR
from taf import TAF
```

## Data Files

The examples expect data files in the `weather_data/` directory at the parent level:
- `../weather_data/optimized_weather.json` - Main optimized weather data
- `../weather_data/optimized_example.json` - Nav Canada extraction example
- `../weather_data/multi_station_optimized.json` - Multi-station example

## Dependencies

- Python 3.7+
- Selenium (for Nav Canada examples)
- Chrome/ChromeDriver (for Nav Canada examples)

## Notes

- All paths are resolved relative to the test file location using `Path(__file__)`
- The examples use the optimized JSON structure where METAR/TAF/NOTAM are grouped by station
- Upper Wind data is stored as a list rather than nested structure
- The parsers support both API response format (aviationweather.gov) and bulletin format (Nav Canada)
