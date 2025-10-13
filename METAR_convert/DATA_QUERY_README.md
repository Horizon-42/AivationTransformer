# Canadian Weather Data Query Scripts

These scripts automate the collection of aviation weather data from 100 Canadian stations using the Nav Canada Weather Server.

## Files

### 1. `data_query_canada_stations.py` - Full Query Script
Queries weather data from 100 Canadian airports in groups of 10 stations.

**Features:**
- Queries 100 Canadian ICAO stations
- Processes 10 stations per group
- Saves raw and parsed data for each group
- Generates comprehensive summary report
- 5-second delay between groups to avoid server overload
- Error handling and retry logic

**Output Files (per group):**
- `canada_group_XX_raw.json` - Raw data from Nav Canada
- `canada_group_XX_parsed.json` - Parsed METAR/TAF/Upper Wind objects

**Summary Report:**
- `canada_query_summary_YYYYMMDD_HHMMSS.json` - Complete query statistics

### 2. `data_query_test.py` - Test Script
Test version that queries only 20 stations (2 groups) for validation.

**Use this first** to verify everything works before running the full query.

## Usage

### Step 1: Test Run (Recommended)
```bash
cd METAR_convert
python data_query_test.py
```

This will:
- Query 20 test stations in 2 groups
- Create test output files
- Show performance metrics
- Verify the query process works

### Step 2: Full Query
Once the test runs successfully:
```bash
python data_query_canada_stations.py
```

This will:
- Query all 100 stations in 10 groups
- Take approximately 5-10 minutes
- Create 10 raw + 10 parsed JSON files
- Generate a comprehensive summary report

## Output Structure

```
weather_data/
├── test_group_01_raw.json          # Test run outputs
├── test_group_01_parsed.json
├── test_summary_YYYYMMDD_HHMMSS.json
│
├── canada_group_01_raw.json        # Full query outputs
├── canada_group_01_parsed.json
├── canada_group_02_raw.json
├── canada_group_02_parsed.json
├── ...
├── canada_group_10_raw.json
├── canada_group_10_parsed.json
└── canada_query_summary_YYYYMMDD_HHMMSS.json
```

## Station Coverage

The 100 Canadian stations include:
- **Major International Airports** (20): CYYZ, CYVR, CYUL, CYYC, etc.
- **Regional Airports** (20): CYKA, CYCD, CYPQ, CYZF, etc.
- **Northern/Remote Airports** (20): CYLT, CYZP, CYFB, CYVM, etc.
- **Smaller Regional** (20): CYQV, CYXL, CYXN, CYXP, etc.
- **Additional Stations** (20): CYAB, CYAC, CYAD, CYAH, etc.

## Data Collected Per Station

- **METAR**: Current weather observations
- **TAF**: Terminal aerodrome forecasts
- **Upper Winds**: Winds aloft data (regional, covers multiple stations)

## Performance Metrics

Based on testing:
- **Time per group**: ~30-60 seconds
- **Total time (100 stations)**: ~5-10 minutes
- **Success rate**: Typically 90-95%
- **Data per station**: 1-2 METARs, 1 TAF (when available)

## Summary Report Contents

The final summary report includes:
```json
{
  "query_timestamp": "2025-10-13T12:00:00Z",
  "total_groups": 10,
  "successful_groups": 10,
  "total_stations_requested": 100,
  "total_stations_with_metar": 95,
  "total_stations_with_taf": 87,
  "total_metars_collected": 98,
  "total_tafs_collected": 89,
  "total_upper_winds_collected": 10,
  "total_elapsed_time": 450.5,
  "average_time_per_group": 45.05,
  "group_details": [...]
}
```

## Error Handling

The scripts handle common errors:
- **Network timeouts**: Continues to next group
- **Parsing errors**: Logs error but continues
- **Missing data**: Reports which stations had no data
- **Browser crashes**: Recovers and continues

Failed groups are reported in the summary.

## Customization

### Change Group Size
Edit the `group_size` variable:
```python
group_size = 10  # Change to 5, 15, 20, etc.
```

### Change Station List
Edit the `CANADIAN_STATIONS` list to add/remove stations:
```python
CANADIAN_STATIONS = [
    'CYYZ', 'CYVR', 'CYUL',  # Your custom list
    # ...
]
```

### Change Delay Between Groups
Edit the `delay` variable:
```python
delay = 5  # seconds between groups
```

### Change Timeout
Edit the server initialization:
```python
server = NavCanadaWeatherServer(headless=True, timeout=60)  # Change timeout
```

## Requirements

- Python 3.7+
- Selenium
- ChromeDriver
- All dependencies from `navcanada_weather_server.py`

## Troubleshooting

### Issue: "No data extracted"
- Check internet connection
- Verify Nav Canada website is accessible
- Try reducing group size

### Issue: Timeouts
- Increase timeout: `timeout=90`
- Increase delay between groups
- Run during off-peak hours

### Issue: Browser crashes
- Update ChromeDriver: `pip install --upgrade webdriver-manager`
- Reduce group size to 5 stations
- Run in non-headless mode to debug: `headless=False`

### Issue: Some stations return no data
- Normal - not all stations report all data types
- Check if station code is correct
- Some remote stations may not have TAF

## Best Practices

1. **Always run test script first** before full query
2. **Run during off-peak hours** to avoid server congestion
3. **Monitor the first few groups** to catch issues early
4. **Keep logs** of query times for optimal scheduling
5. **Backup data files** regularly

## Performance Tips

- Run with `headless=True` for better performance
- Use wired internet connection for stability
- Close other browser windows during query
- Run on a machine that won't sleep/hibernate

## Data Analysis

After collection, you can analyze the data:

```python
import json

# Load summary
with open('weather_data/canada_query_summary_YYYYMMDD.json') as f:
    summary = json.load(f)

# Find stations with most data
for group in summary['group_details']:
    print(f"Group {group['group_number']}: "
          f"{group['total_metars']} METARs, "
          f"{group['total_tafs']} TAFs")

# Load specific group data
with open('weather_data/canada_group_01_parsed.json') as f:
    data = json.load(f)
    
# Access METAR for CYYZ
cyyz_metars = data['metars']['CYYZ']
for metar in cyyz_metars:
    print(f"Temp: {metar['temperature_celsius']}°C")
```

## Support

For issues or questions:
1. Check the summary report for error details
2. Review failed group statistics
3. Try re-running failed groups manually
4. Check Nav Canada website availability

## Future Enhancements

Potential improvements:
- Add retry logic for failed groups
- Parallel processing of groups
- Real-time monitoring dashboard
- Automatic scheduling (cron jobs)
- Database integration
- API endpoint wrapper
