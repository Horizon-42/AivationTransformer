# Final Optimized CSV Structure

## Design Philosophy

**Your feedback was spot-on:**
1. ✅ **Upper Winds**: Combine dir/speed/temp into one cell per altitude → Much cleaner!
2. ✅ **TAF**: One row per forecast period (no JSON in cells) → Standard CSV approach

This creates **clean, readable CSV files** that work well in Excel, Google Sheets, and data analysis tools without requiring JSON parsing.

---

## 📊 Upper Winds CSV Structure

### Format: One Row Per Period
**12 columns** (was 30 with separate dir/speed/temp columns)

```
station_id, valid_time, use_period, 3000ft, 6000ft, 9000ft, 12000ft, 18000ft, 24000ft, 30000ft, 34000ft, 39000ft
```

### Altitude Column Format: `direction/speed/temperature`
Each altitude cell contains: `270/15/-28`
- Direction: degrees (e.g., 270)
- Speed: knots (e.g., 15)
- Temperature: Celsius (e.g., -28)

### Example Data
```csv
station_id,valid_time,use_period,3000ft,6000ft,9000ft,12000ft,18000ft,24000ft,30000ft,34000ft,39000ft
CYRT,230600Z,00-12,280/8/,260/10/-7,260/12/-13,280/11/-18,330/15/-28,350/20/-37,320/16/-48,280/15/-51,260/17/-51
CYRT,221800Z,15-00,230/10/,210/14/-8,250/13/-14,250/20/-19,240/32/-30,230/35/-40,220/49/-48,230/39/-49,230/30/-49
```

### Benefits
- ✅ **75% fewer columns** (30 → 12)
- ✅ **Clean, readable** - Each altitude is self-contained
- ✅ **Easy to parse** - Split on `/` to get dir/speed/temp
- ✅ **Excel-friendly** - Can still sort/filter by station or time
- ✅ **Compact** - 1.7KB vs 2.2KB (19% smaller)

---

## 📊 TAF CSV Structure

### Format: One Row Per Forecast Period
**22 columns** (no JSON!)

```
Station Info (5):
  station_id, station_name, latitude, longitude, elevation_meters

Bulletin Info (4):
  bulletin_time, issue_time, bulletin_valid_from, bulletin_valid_to

Period Info (4):
  period_valid_from, period_valid_to, forecast_change_type, probability_percent

Wind (3):
  wind_direction_deg, wind_speed_kt, wind_gust_kt

Visibility & Weather (2):
  visibility, weather_phenomena

Sky Conditions (1):
  sky_conditions  (human-readable: "OVC 1200ft; BKN 2500ft CB")

Remarks (1):
  remarks
```

### Forecast Change Types
- `BASE` - Base forecast (first period)
- `FM` - From time (weather change at specific time)
- `TEMPO` - Temporary conditions
- `BECMG` - Becoming (gradual change)
- `PROB` - Probability conditions

### Example Data
```csv
station_id,forecast_change_type,period_valid_from,period_valid_to,wind_direction_deg,wind_speed_kt,visibility,weather_phenomena,sky_conditions
CYIO,BASE,2025-10-22T07:00:00,2025-10-22T19:00:00,VRB,3,1/2,DZ,
CYIO,TEMPO,2025-10-22T07:00:00,2025-10-22T11:00:00,,,3,SN,OVC 1200ft
CYIO,FM,2025-10-22T11:00:00,2025-10-22T19:00:00,220,10,2,SN,OVC 1200ft
CYIO,TEMPO,2025-10-22T11:00:00,2025-10-22T19:00:00,,,6,SN,OVC 2500ft
```

### Benefits
- ✅ **No JSON in cells** - Standard CSV structure
- ✅ **Easy filtering** - Filter by station, time, or change type
- ✅ **Readable in Excel** - No parsing needed
- ✅ **Repeats bulletin info** - Each row is self-contained (yes, some duplication, but that's OK!)
- ✅ **Much smaller** - 10KB vs 42KB (76% smaller than JSON version!)

---

## Comparison: Old vs New

### Upper Winds
```
Old Structure (3 columns per altitude):
- 30 columns total
- wind_3000ft_dir, wind_3000ft_speed_kt, temp_3000ft_c, wind_6000ft_dir, ...
- Hard to read at a glance

New Structure (1 column per altitude):
- 12 columns total  
- 3000ft, 6000ft, 9000ft, ...
- Each cell: "280/15/-28"
- Easy to scan visually ✅
```

### TAF
```
Old Structure (JSON in cell):
- 12 rows (one per bulletin)
- 21 columns
- forecast_periods_json contains all periods
- Requires JSON parsing
- 42KB file size

New Structure (one period per row):
- 55 rows (one per forecast period)
- 22 columns
- All data in CSV columns (no JSON!)
- Works directly in Excel ✅
- 10KB file size (76% smaller!) ✅
```

---

## File Statistics

### Test Data (Group 7: 17 METARs, 12 TAF bulletins, 5 stations with upper winds)

```
File              Rows    Columns    Size       Notes
─────────────────────────────────────────────────────────────
test_metars.csv    18      22        4.8KB     Clean, no raw data
test_tafs.csv      56      22       10.0KB     One row per period
test_upper_winds   16      12        1.7KB     Combined altitude data
```

### Space Efficiency
- **TAF**: 76% smaller than JSON version (10KB vs 42KB)
- **Upper Winds**: 19% smaller than separate columns (1.7KB vs 2.2KB)

---

## Usage Examples

### Upper Winds - Parse altitude data
```python
import csv

with open('upper_winds.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Parse 9000ft altitude: "260/12/-13"
        altitude_data = row['9000ft'].split('/')
        direction = int(altitude_data[0]) if altitude_data[0] else None
        speed = int(altitude_data[1]) if altitude_data[1] else None
        temp = float(altitude_data[2]) if altitude_data[2] else None
        
        print(f"{row['station_id']}: 9000ft wind {direction}° at {speed}kt, {temp}°C")
```

### TAF - Filter by change type
```python
import csv

with open('tafs.csv') as f:
    reader = csv.DictReader(f)
    
    # Find all TEMPO periods with low visibility
    for row in reader:
        if row['forecast_change_type'] == 'TEMPO':
            vis = row['visibility']
            if vis and any(char.isdigit() for char in vis):
                vis_num = float(''.join(c for c in vis if c.isdigit() or c == '.'))
                if vis_num < 3:
                    print(f"{row['station_id']}: TEMPO low vis {vis}, wx: {row['weather_phenomena']}")
```

### TAF - Group by bulletin (reconstruct TAF bulletins)
```python
import csv
from itertools import groupby

with open('tafs.csv') as f:
    reader = csv.DictReader(f)
    data = list(reader)
    
    # Group by station and bulletin time
    for (station, bulletin_time), periods in groupby(data, 
                                                      key=lambda r: (r['station_id'], r['bulletin_time'])):
        periods_list = list(periods)
        print(f"\n{station} TAF issued at {bulletin_time}:")
        print(f"  {len(periods_list)} forecast periods")
        for p in periods_list:
            print(f"  - {p['forecast_change_type']:6s}: {p['period_valid_from'][11:16]}-{p['period_valid_to'][11:16]}")
```

---

## Excel/Google Sheets Usage

### Upper Winds
1. Open CSV in Excel
2. Select altitude column (e.g., `9000ft`)
3. **Data → Text to Columns → Delimited → Delimiter: `/`**
4. Creates 3 columns: direction, speed, temperature
5. Now you can chart, analyze, filter by wind speed, etc.

### TAF
1. Open CSV in Excel
2. Use **AutoFilter** on `forecast_change_type` to see only BASE, TEMPO, etc.
3. Use **AutoFilter** on `station_id` to analyze one station
4. Sort by `period_valid_from` to see chronological order
5. **No special processing needed** - all data is in columns!

---

## Summary

### Design Principles Applied
1. ✅ **No JSON in CSV cells** - Keep it simple
2. ✅ **One entity per row** - One period per row (TAF), one time period per row (upper winds)
3. ✅ **Combine related data** - dir/speed/temp together (upper winds)
4. ✅ **Human readable** - Sky conditions as text, not codes
5. ✅ **Tool friendly** - Works in Excel, Pandas, R, SQL without parsing
6. ✅ **Self-contained rows** - Repeat bulletin info so each row stands alone

### Trade-offs Accepted
- **TAF repeats bulletin info** (station, bulletin time) in each period row
  - This is **intentional** and **good** - makes each row self-contained
  - Small size overhead (10KB) vs massive usability gain
  - This is how well-designed CSV exports work!

### The Result
Clean, professional CSV files that anyone can use with standard tools. No custom parsing logic needed. ✅

---

*Test data: canada_group_07_parsed.json*  
*Generated: 2025-10-22*
