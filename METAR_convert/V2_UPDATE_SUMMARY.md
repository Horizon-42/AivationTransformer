# V2 Script Update Summary

## Changes Made

### 1. Per-Group File Output
- **Raw Data Files**: Each group now saves raw JSON data as `canada_group_{XX}_raw.json`
- **Parsed Data Files**: Each group now saves parsed data as `canada_group_{XX}_parsed.json`
- Files are saved during the query process, not at the end

### 2. Parsed Data Export
- Using `server.export_to_json()` to export structured, parsed weather data
- Parsed files contain:
  - METAR objects (parsed, not raw text)
  - TAF objects (parsed, not raw text)
  - Upper Wind objects (parsed, not raw text)
- This matches the v1 script behavior

### 3. Enhanced Group Statistics
Each group now tracks:
- `stations_with_metar`: List of station codes that had METAR data
- `stations_with_taf`: List of station codes that had TAF data
- `raw_data_file`: Path to raw JSON file for this group
- `parsed_data_file`: Path to parsed JSON file for this group

### 4. Invalid Stations File
- Separate text file: `invalid_stations_{timestamp}.txt`
- Categorized by error type:
  - No Data Stations
  - Parsing Error Stations
  - Other Error Stations

### 5. Group-Wise Summary Report
Terminal output now shows:
1. **GROUP-WISE SUMMARY** - Individual details for each group
   - Stations requested/valid
   - Invalid stations list
   - Data counts
   - File paths for raw and parsed data
   - Elapsed time
2. **OVERALL SUMMARY** - Aggregated statistics

## File Structure

After running the script, the `weather_data/` directory will contain:

```
weather_data/
├── canada_group_01_raw.json      # Raw data from Nav Canada
├── canada_group_01_parsed.json   # Parsed/structured data
├── canada_group_02_raw.json
├── canada_group_02_parsed.json
├── ...
├── query_results_{timestamp}.json      # Full summary JSON
└── invalid_stations_{timestamp}.txt    # Invalid stations report
```

## Example Output

```
================================================================================
📊 GROUP-WISE SUMMARY
================================================================================

✅ Group 1:
   Stations: 20 requested, 19 valid
   Invalid: CYXD
   Data: 45 reports (18 METAR, 16 TAF, 11 Upper)
   Files:
      • Raw: weather_data/canada_group_01_raw.json
      • Parsed: weather_data/canada_group_01_parsed.json
   Time: 15.2s

✅ Group 2:
   Stations: 20 requested, 20 valid
   Data: 50 reports (20 METAR, 18 TAF, 12 Upper)
   Files:
      • Raw: weather_data/canada_group_02_raw.json
      • Parsed: weather_data/canada_group_02_parsed.json
   Time: 12.5s

================================================================================
📊 OVERALL SUMMARY
================================================================================

✅ Groups: 10/10 successful
📍 Stations: 198/200 valid
❌ Invalid Stations: 2 total

📈 Data Collected:
   • METAR: 180
   • TAF: 160
   • Upper Winds: 110
   • Total entries: 450

⏱️  Total Time: 125.5s

📄 Files saved:
   • Results: weather_data/query_results_20251022_143025.json
   • Invalid stations: weather_data/invalid_stations_20251022_143025.txt
================================================================================
```

## Usage

```bash
python3 data_query_canada_stations_v2.py
```

Set `VERBOSE = True` in the script for detailed debugging output.
