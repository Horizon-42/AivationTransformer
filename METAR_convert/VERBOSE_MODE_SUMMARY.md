# Verbose Mode Implementation

## Overview

Added a `VERBOSE` configuration parameter to control the level of output during data query operations. By default, the script now prints minimal, essential information. Verbose mode can be enabled for detailed debugging.

## Configuration

```python
# At the top of the script
VERBOSE = False  # Set to True for detailed output, False for minimal output
```

## Output Comparison

### Default Mode (VERBOSE = False)

**Clean, concise output focused on progress and results:**

```
================================================================================
📦 Group 1/11: 20 stations
================================================================================
✅ Group 1: 45 reports (18 METAR, 16 TAF, 11 Upper) [23.4s]

================================================================================
📦 Group 2/11: 20 stations
================================================================================
⚠️  Batch returned 0 reports - searching for invalid station(s)...
  🔍 Finding invalid station(s)... Found 1 invalid: CYXD
🔄 Retrying with 19 valid stations...
✅ Group 2: 42 reports (17 METAR, 15 TAF, 10 Upper) - Excluded: CYXD [31.2s]

================================================================================
📦 Group 3/11: 20 stations
================================================================================
✅ Group 3: 47 reports (19 METAR, 17 TAF, 11 Upper) [22.8s]
```

**Key features:**
- ✅ One-line summary per group
- ✅ Shows only essential info (counts, time, invalid stations)
- ✅ Progress tracking (Group X/Total)
- ✅ Invalid station detection is still shown but condensed
- ✅ Easy to scan for problems

### Verbose Mode (VERBOSE = True)

**Detailed output for debugging:**

```
================================================================================
📦 Group 1/11: 20 stations
📍 Stations: CYYC, CYBW, CYOD, CYXD, CYEG, CYED, CZVL, CYPY, CYMM, CYQU...
================================================================================

🔄 Attempting batch query...
   Result: 45 total reports (METAR: 18, TAF: 16, Upper: 11)
✅ Group 1: 45 reports (18 METAR, 16 TAF, 11 Upper) [23.4s]
   Valid stations: 20/20

================================================================================
📦 Group 2/11: 20 stations
📍 Stations: CYOJ, CYQL, CYLL, CYXH, CYPE, CYQF, CYZH, CYZU, CYXX, CBBC...
================================================================================

🔄 Attempting batch query...
   Result: 0 total reports (METAR: 0, TAF: 0, Upper: 0)
⚠️  Batch returned 0 reports - searching for invalid station(s)...

  🔍 Binary search for invalid station(s) in this group of 20
  [1] Testing left half (10 stations): CYOJ, CYQL, CYLL, CYXH, CYPE... ✓ Has data (23 reports)
  [1] Testing right half (10 stations): CYQF, CYZH, CYZU, CYXX, CBBC... ✗ No data (0 reports = INVALID)
  → Right half has problem (0 reports), searching there
  [2] Testing left half (5 stations): CYQF, CYZH, CYZU, CYXX... ✓ Has data (12 reports)
  [2] Testing right half (5 stations): CBBC, CYXD, CYBL, CYCG... ✗ No data (0 reports = INVALID)
  → Right half has problem (0 reports), searching there
  [3] Testing final station: CYXD...     ✗ Invalid (0 reports)

      ❌ CYXD is INVALID

  ✓ Binary search complete in 3 steps
    Valid: 19, Invalid: 1
    Invalid stations: CYXD

🔄 Retrying with 19 valid stations...
   Retry result: 42 total reports
✅ Group 2: 42 reports (17 METAR, 15 TAF, 10 Upper) - Excluded: CYXD [31.2s]
   Valid stations: 19/20
```

**Key features:**
- ✅ Full station lists
- ✅ Detailed binary search steps
- ✅ Individual test results
- ✅ Retry confirmations
- ✅ Complete debugging information

## Benefits

### Default Mode Benefits:
1. **Cleaner terminal output** - Easy to read and follow
2. **Focus on results** - Shows what matters (counts, time, problems)
3. **Production-ready** - Suitable for automated runs
4. **Easy troubleshooting** - Problems are still highlighted
5. **Faster scanning** - One-line per group makes it easy to see progress

### Verbose Mode Benefits:
1. **Full debugging** - See every test and decision
2. **Binary search visibility** - Understand how invalid stations are found
3. **Development aid** - Helpful when developing or troubleshooting
4. **Educational** - Shows the algorithm in action
5. **Audit trail** - Complete record of what happened

## When to Use Each Mode

### Use Default Mode (VERBOSE = False):
- ✅ Production data collection runs
- ✅ Automated/scheduled queries
- ✅ When you just want results
- ✅ When processing many groups (>10)
- ✅ When terminal output needs to be clean

### Use Verbose Mode (VERBOSE = True):
- ✅ Debugging issues
- ✅ Understanding how binary search works
- ✅ Troubleshooting parsing errors
- ✅ Development and testing
- ✅ First-time runs to verify behavior

## Implementation Details

### Modified Functions:

1. **`validate_single_station(server, station, verbose=VERBOSE)`**
   - Prints test results only in verbose mode
   - Silent progress otherwise

2. **`test_batch_has_data(server, stations, verbose=VERBOSE)`**
   - Prints exceptions only in verbose mode

3. **`find_invalid_stations_in_batch(server, stations, delay, verbose=VERBOSE)`**
   - Verbose: Shows detailed binary search steps
   - Default: One-line summary with invalid stations found

4. **`query_station_batch(server, stations, group_num, total_groups, all_invalid_stations, delay, verbose=VERBOSE)`**
   - Verbose: Shows full details, all stations, all steps
   - Default: One-line summary per group with key metrics

## Example Complete Run Output (Default Mode)

```
🌤️  Canadian Weather Stations Data Query v2
================================================================================
📅 Started: 2025-10-22 10:15:30
📍 Total stations: 217
📦 Group size: 20
⏱️  Request delay: 5.0s
================================================================================

📦 Created 11 groups

================================================================================
📦 Group 1/11: 20 stations
================================================================================
✅ Group 1: 45 reports (18 METAR, 16 TAF, 11 Upper) [23.4s]

================================================================================
📦 Group 2/11: 20 stations
================================================================================
⚠️  Batch returned 0 reports - searching for invalid station(s)...
  🔍 Finding invalid station(s)... Found 1 invalid: CYXD
🔄 Retrying with 19 valid stations...
✅ Group 2: 42 reports (17 METAR, 15 TAF, 10 Upper) - Excluded: CYXD [31.2s]

... (groups 3-10) ...

================================================================================
📦 Group 11/11: 17 stations
================================================================================
✅ Group 11: 38 reports (15 METAR, 13 TAF, 10 Upper) [20.1s]

================================================================================
📊 FINAL SUMMARY
================================================================================

✅ Groups: 11/11 successful
📍 Stations: 216/217 valid

❌ Problem Stations Found (1):

   No Data (1):
      • CYXD: No data returned

📈 Data Collected:
   • METAR: 198
   • TAF: 175
   • Upper Winds: 119
   • Total entries: 492

⏱️  Total Time: 287.3s
📄 Results saved to: weather_data/query_results_20251022_101822.json
================================================================================

✅ Query complete!
```

Much cleaner! 🎉

## Switching Modes

To enable verbose mode, simply change one line at the top of the script:

```python
# Change this:
VERBOSE = False

# To this:
VERBOSE = True
```

Then run the script normally:
```bash
python3 data_query_canada_stations_v2.py
```
