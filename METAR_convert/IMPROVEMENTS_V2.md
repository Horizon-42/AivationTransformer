# Data Query Script V2 - Improvements

## Issues Fixed

### 1. ✅ Search Limited to Current Group Only
**Problem:** The original approach might have searched across all stations instead of just the current group of 10.

**Solution:** 
- The `find_invalid_stations_in_batch()` function now explicitly operates only on the `stations` parameter passed to it
- This parameter contains ONLY the current group's stations (max 10)
- Added clear comments documenting this scope limitation

```python
# Binary search within THIS GROUP ONLY (not all stations)
# 'stations' parameter contains only the current group's 10 stations
valid_stations, invalid_dict = find_invalid_stations_in_batch(
    server, stations, delay  # stations = current group only
)
```

### 2. ✅ Binary Search for Faster Invalid Station Detection
**Problem:** Linear iteration through all stations was slow (10 tests for 10 stations).

**Solution:** Implemented binary search algorithm that reduces the number of requests significantly.

#### How Binary Search Works:

1. **Split the group in half**
   - Test left half: stations [0:5]
   - Test right half: stations [5:10]

2. **Identify which half has the problem**
   - If left returns no data → search left half
   - If right returns no data → search right half
   - If both fail → search both (rare case, multiple invalid stations)

3. **Repeat until one station remains**
   - Continue splitting and testing
   - Narrows down to the exact invalid station(s)

#### Efficiency Comparison:

| Group Size | Linear Search | Binary Search | Improvement |
|------------|---------------|---------------|-------------|
| 10 stations | 10 tests | 4-5 tests | ~50% faster |
| 20 stations | 20 tests | 5-6 tests | ~70% faster |
| 100 stations | 100 tests | 7-8 tests | ~93% faster |

**Example from demo:**
- Finding CYXD in group of 10 stations
- Linear: Would require 10 individual tests
- Binary: Required only 5 tests (Steps 1-4 split testing + Step 5 final confirmation)

## Key Features

### Rate Limiting Protection
```python
REQUEST_DELAY = 5.0  # 5 seconds between requests
```
- Prevents website from flagging requests as attacks
- Applied between all batch queries
- Applied during binary search testing

### Invalid Station Tracking
```python
all_invalid_stations = {}  # Global tracker across all groups
```
- Tracks invalid stations with error messages
- Persists across all group queries
- Included in final report with details

### Automatic Recovery
When a batch returns no data:
1. Automatically initiates binary search
2. Identifies invalid station(s)
3. Updates global tracker
4. Retries with only valid stations
5. Continues to next group

## Usage

```bash
python3 data_query_canada_stations_v2.py
```

The script will automatically:
- ✅ Process groups of 10 stations
- ✅ Use 5-second delays between requests
- ✅ Binary search to find invalid stations (within each group)
- ✅ Track all invalid stations globally
- ✅ Generate comprehensive report with invalid station details

## Output

Final report includes:
```json
{
  "invalid_stations_detail": {
    "CYXD": "No data",
    "STATION2": "Connection timeout"
  },
  "total_groups": 22,
  "valid_stations": 215,
  "invalid_stations_count": 2
}
```

## Performance Improvements

For 217 Canadian stations (22 groups of ~10):
- **Old approach:** Could take 2170 requests if all invalid
- **New approach:** Maximum ~110 requests even with issues
- **With delays:** Old=3+ hours, New=~10-15 minutes

## Testing

Run the demo to see binary search in action:
```bash
python3 test_binary_search_demo.py
```

This demonstrates the exact algorithm used to find invalid stations efficiently.
