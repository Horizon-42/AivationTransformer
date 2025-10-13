# Data Query Scripts - Quick Summary

## What Was Created

Three scripts for automated collection of Canadian aviation weather data:

### 1. **data_query_canada_stations.py** - Production Script
- Queries 100 Canadian airport stations
- Groups of 10 stations per batch
- Saves raw + parsed data for each group
- Generates comprehensive summary report
- ~5-10 minutes total runtime

### 2. **data_query_test.py** - Test Script  
- Test version with 20 stations (2 groups)
- Validates functionality before full run
- Quick test (~1-2 minutes)
- **Run this first!**

### 3. **DATA_QUERY_README.md** - Documentation
- Complete usage instructions
- Troubleshooting guide
- Customization options
- Performance tips

## Quick Start

```bash
# Step 1: Test (recommended)
cd METAR_convert
python data_query_test.py

# Step 2: Full query (after test succeeds)
python data_query_canada_stations.py
```

## What It Does

```
Input: 100 Canadian station codes
  ↓
Split into 10 groups of 10 stations
  ↓
For each group:
  1. Query Nav Canada for METAR/TAF/Upper Winds
  2. Save raw JSON: canada_group_XX_raw.json
  3. Parse into objects
  4. Save parsed JSON: canada_group_XX_parsed.json
  ↓
Generate summary report with statistics
```

## Output Files

Per group (10 total):
- `canada_group_01_raw.json` - Raw Nav Canada data
- `canada_group_01_parsed.json` - Parsed METAR/TAF objects
- (Same for groups 02-10)

Summary:
- `canada_query_summary_YYYYMMDD_HHMMSS.json` - Complete statistics

## Key Features

✅ **Automated grouping** - Handles 10 stations at a time
✅ **Progress tracking** - Shows status for each group  
✅ **Error handling** - Continues on failures, reports errors
✅ **Rate limiting** - 5-second delay between groups
✅ **Statistics** - Comprehensive metrics and timing
✅ **Dual outputs** - Both raw and parsed data saved

## Expected Results

- **Groups**: 10 (100 stations ÷ 10)
- **Success rate**: ~90-95%
- **Total METARs**: ~95-98
- **Total TAFs**: ~85-90
- **Upper Winds**: ~10 reports
- **Total time**: 5-10 minutes
- **Total files**: 21 (10 raw + 10 parsed + 1 summary)

## Station Coverage

- 20 Major International (CYYZ, CYVR, CYUL, CYYC, etc.)
- 20 Regional (CYKA, CYCD, CYPQ, etc.)
- 20 Northern/Remote (CYLT, CYZP, CYFB, etc.)
- 20 Smaller Regional (CYQV, CYXL, CYXN, etc.)
- 20 Additional (CYAB, CYAC, CYAD, etc.)

## Usage Example

```python
# After running data_query_canada_stations.py

import json

# Load group 1 parsed data
with open('weather_data/canada_group_01_parsed.json') as f:
    data = json.load(f)

# Access Toronto (CYYZ) weather
if 'CYYZ' in data['metars']:
    for metar in data['metars']['CYYZ']:
        print(f"Toronto: {metar['temperature_celsius']}°C")

# Load summary for statistics
with open('weather_data/canada_query_summary_*.json') as f:
    summary = json.load(f)
    print(f"Total METARs collected: {summary['total_metars_collected']}")
```

## Customization

```python
# Change group size (in script)
group_size = 10  # Change to 5, 15, 20

# Change delay between groups
delay = 5  # seconds

# Change timeout
server = NavCanadaWeatherServer(timeout=60)  # Change to 90, 120, etc.

# Custom station list
CANADIAN_STATIONS = ['CYYZ', 'CYVR', ...]  # Your stations
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Timeouts | Increase timeout to 90 seconds |
| Browser crash | Update ChromeDriver |
| Some stations no data | Normal - not all report all types |
| Slow performance | Check internet connection |

## Next Steps

1. ✅ Run test script first
2. ✅ Verify test output looks good
3. ✅ Run full production script
4. ✅ Check summary report
5. ✅ Analyze collected data
6. ✅ Customize as needed

## File Locations

```
METAR_convert/
├── data_query_canada_stations.py    # Production script
├── data_query_test.py                # Test script
├── DATA_QUERY_README.md              # Full documentation
├── weather_data/                     # Output directory
│   ├── canada_group_01_raw.json
│   ├── canada_group_01_parsed.json
│   └── canada_query_summary_*.json
```

Ready to use! Start with the test script to verify everything works.
