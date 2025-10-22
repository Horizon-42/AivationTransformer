# CSV Export Documentation

## Overview

The aviation weather data query system now exports data to CSV files for easy analysis in spreadsheet applications, data science tools, and databases. Three separate CSV files are generated for each group:

1. **METAR CSV** - Current weather observations
2. **TAF CSV** - Terminal aerodrome forecasts (by forecast period)
3. **Upper Winds CSV** - Upper wind and temperature data (by altitude level)

## File Naming Convention

Files are named with a group number prefix:

```
group_01_metars.csv
group_01_tafs.csv
group_01_upper_winds.csv
group_02_metars.csv
...
```

## METAR CSV Structure

**Schema**: One row per METAR observation

### Columns

#### Station Information
- `station_id` - ICAO identifier (e.g., CYYC)
- `station_name` - Human-readable name
- `latitude` - Decimal degrees
- `longitude` - Decimal degrees
- `elevation_meters` - Station elevation

#### Timing
- `observation_time` - ISO 8601 datetime of observation
- `observation_timestamp` - Unix timestamp
- `receipt_time` - ISO 8601 datetime when report was received

#### Report Info
- `report_type` - METAR or SPECI
- `flight_category` - VFR, MVFR, IFR, or LIFR

#### Temperature
- `temperature_celsius` - Current temperature
- `dewpoint_celsius` - Dewpoint temperature
- `max_temperature_celsius` - 24-hour maximum (if available)
- `min_temperature_celsius` - 24-hour minimum (if available)

#### Wind
- `wind_direction_degrees` - True wind direction (0-360)
- `wind_speed_knots` - Wind speed
- `wind_gust_knots` - Gust speed (if present)
- `wind_variable` - Boolean, true if variable

#### Visibility
- `visibility` - Visibility in statute miles or "10+" 
- `visibility_meters` - Visibility in meters (if available)

#### Pressure
- `altimeter_hpa` - Altimeter setting in hectopascals
- `sea_level_pressure_hpa` - Sea level pressure (if available)
- `pressure_tendency_hpa` - 3-hour pressure change (if available)

#### Sky Conditions
- `sky_coverage` - Overall coverage (CLR, FEW, SCT, BKN, OVC)
- `cloud_layers_json` - JSON array of cloud layers with coverage, base altitude, and type

#### Weather
- `present_weather` - Comma-separated list of weather phenomena codes

#### Quality & Raw
- `quality_control_field` - Quality control flags
- `raw_observation` - Original raw METAR text

### Example Row
```csv
station_id,station_name,latitude,longitude,observation_time,temperature_celsius,wind_direction_degrees,wind_speed_knots,visibility,sky_coverage,flight_category
CYYC,Calgary Intl,51.113889,-114.020278,2025-10-22T14:00:00+00:00,15.0,270,25,10+,FEW,VFR
```

## TAF CSV Structure

**Schema**: One row per forecast period (not per TAF bulletin)

This normalized structure allows easy analysis of forecast conditions over time periods.

### Columns

#### Station Information
- `station_id` - ICAO identifier
- `station_name` - Human-readable name
- `latitude` - Decimal degrees
- `longitude` - Decimal degrees
- `elevation_meters` - Station elevation

#### TAF Bulletin Info
- `bulletin_time` - ISO 8601 datetime when bulletin was created
- `issue_time` - ISO 8601 datetime when TAF was issued
- `database_time` - ISO 8601 datetime when stored
- `taf_valid_from` - Start of entire TAF validity period
- `taf_valid_to` - End of entire TAF validity period
- `taf_valid_from_timestamp` - Unix timestamp
- `taf_valid_to_timestamp` - Unix timestamp
- `is_most_recent` - Boolean, true if this is the most recent TAF

#### Forecast Period Info
- `period_valid_from` - Start of this forecast period
- `period_valid_to` - End of this forecast period
- `period_valid_from_timestamp` - Unix timestamp
- `period_valid_to_timestamp` - Unix timestamp
- `becomes_time` - When change becomes effective (for FM)
- `forecast_change_type` - FM, BECMG, TEMPO, or PROB
- `probability_percent` - Probability percentage (for PROB)

#### Wind Forecast
- `wind_direction_degrees` - Forecast wind direction
- `wind_speed_knots` - Forecast wind speed
- `wind_gust_knots` - Forecast gust speed
- `wind_shear_height_feet` - Wind shear altitude
- `wind_shear_direction_degrees` - Wind shear direction
- `wind_shear_speed_knots` - Wind shear speed

#### Visibility Forecast
- `visibility` - Forecast visibility string (e.g., "6+", "3SM", "P6SM")
- `vertical_visibility_feet` - Vertical visibility (obscured sky)

#### Weather Forecast
- `weather_phenomena` - Weather string (e.g., "-RA", "TSRA", "VCSH")

#### Sky Conditions Forecast
- `cloud_layers_json` - JSON array of forecast cloud layers

#### Hazards
- `icing_turbulence_json` - JSON array of icing/turbulence forecasts
- `temperature_forecasts_json` - JSON array of temperature forecasts with times

#### Raw
- `raw_taf` - Original raw TAF text
- `remarks` - TAF remarks section

### Example Row
```csv
station_id,period_valid_from,period_valid_to,forecast_change_type,wind_direction_degrees,wind_speed_knots,visibility,weather_phenomena
CYYC,2025-10-22T18:00:00+00:00,2025-10-23T00:00:00+00:00,FM,280,20,3SM,-SN
```

### Analysis Tips
- Filter by `forecast_change_type` to analyze different types of changes
- Group by `station_id` and `taf_valid_from` to reconstruct complete TAFs
- Use `period_valid_from` and `period_valid_to` for time-series analysis
- Parse JSON columns for detailed cloud/icing/temperature analysis

## Upper Winds CSV Structure

**Schema**: One row per altitude level per period per station

This normalized structure is ideal for vertical profile analysis and altitude-specific queries.

### Columns

- `station_id` - Station identifier
- `valid_time` - Valid time (e.g., "221200Z")
- `use_period` - Usage period range (e.g., "1800-0000")
- `altitude_ft` - Altitude in feet (e.g., 3000, 6000, 9000, etc.)
- `wind_direction_deg` - Wind direction at this altitude (0-360)
- `wind_speed_kt` - Wind speed at this altitude in knots
- `temperature_c` - Temperature at this altitude in Celsius

### Example Rows
```csv
station_id,valid_time,use_period,altitude_ft,wind_direction_deg,wind_speed_kt,temperature_c
CYYC,221200Z,1800-0000,3000,270,25,-5
CYYC,221200Z,1800-0000,6000,280,35,-15
CYYC,221200Z,1800-0000,9000,290,45,-25
CYYC,221200Z,1800-0000,12000,300,55,-35
```

### Analysis Tips
- Filter by `altitude_ft` to analyze conditions at specific flight levels
- Group by `station_id` and `valid_time` to reconstruct complete vertical profiles
- Use for wind shear analysis by comparing adjacent altitude levels
- Ideal for flight planning calculations

## JSON Field Formats

### Cloud Layers JSON
```json
[
  {"coverage": "BKN", "base_feet": 2500, "cloud_type": "CU"},
  {"coverage": "OVC", "base_feet": 8000, "cloud_type": null}
]
```

### Icing/Turbulence JSON
```json
[
  {"intensity": "MOD", "type": "ICE", "base_feet": 5000, "top_feet": 12000},
  {"intensity": "SEV", "type": "TURB", "base_feet": 20000, "top_feet": 30000}
]
```

### Temperature Forecasts JSON
```json
[
  {"temperature_celsius": -5, "time": "2025-10-22T18:00:00+00:00"},
  {"temperature_celsius": 10, "time": "2025-10-23T06:00:00+00:00"}
]
```

## Data Analysis Examples

### Using Python/Pandas

```python
import pandas as pd
import json

# Load METAR data
metars = pd.read_csv('group_01_metars.csv')

# Filter for IFR conditions
ifr_metars = metars[metars['flight_category'] == 'IFR']

# Parse cloud layers
metars['clouds'] = metars['cloud_layers_json'].apply(json.loads)

# Load TAF data
tafs = pd.read_csv('group_01_tafs.csv', parse_dates=['period_valid_from', 'period_valid_to'])

# Find TEMPO periods
tempo_periods = tafs[tafs['forecast_change_type'] == 'TEMPO']

# Load upper winds
winds = pd.read_csv('group_01_upper_winds.csv')

# Get winds at 9000 ft
winds_9k = winds[winds['altitude_ft'] == 9000]
```

### Using SQL

```sql
-- Load into SQLite, PostgreSQL, etc.

-- Find all METARs with low visibility
SELECT station_id, observation_time, visibility, flight_category
FROM metars
WHERE visibility < 3.0;

-- Find TAF periods with strong winds
SELECT station_id, period_valid_from, wind_speed_knots, wind_gust_knots
FROM tafs
WHERE wind_speed_knots > 30 OR wind_gust_knots > 40;

-- Analyze wind profiles
SELECT station_id, valid_time, altitude_ft, wind_direction_deg, wind_speed_kt
FROM upper_winds
WHERE station_id = 'CYYC'
ORDER BY altitude_ft;
```

## Best Practices

1. **Time Zones**: All timestamps are in UTC
2. **Missing Data**: Empty strings indicate missing/unavailable data
3. **JSON Parsing**: Use appropriate JSON parser for cloud layers and other complex fields
4. **Normalization**: TAF and Upper Wind CSVs are normalized - join on station/time for full records
5. **Large Files**: For processing many groups, consider using chunked reading or database import
6. **Data Types**: Convert timestamp columns to datetime objects for time-series analysis

## Output Location

All CSV files are saved to the `weather_data/` directory along with:
- Raw JSON files (`canada_group_XX_raw.json`)
- Parsed JSON files (`canada_group_XX_parsed.json`)
- Summary files (`query_results_{timestamp}.json`)
- Invalid stations list (`invalid_stations_{timestamp}.txt`)
