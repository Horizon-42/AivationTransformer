"""
Data Query Script for Canadian Aviation Weather Stations (Version 2)

This script queries weather data from Canadian stations using the Nav Canada Weather Server.
Features:
- Automatic invalid station detection through iteration
- Rate limiting with configurable delays
- Detailed tracking of invalid stations in reports
- Retry logic for transient failures

Usage:
    python data_query_canada_stations_v2.py
"""

import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime
from navcanada_weather_server import NavCanadaWeatherServer


# Configuration
REQUEST_DELAY = 5.0  # Delay between requests (seconds)
GROUP_SIZE = 20      # Number of stations per batch
MAX_RETRIES = 3      # Max retries for transient failures
VERBOSE = False      # Set to True for detailed output, False for minimal output


# Top Canadian airport stations (ICAO codes)
CANADIAN_STATIONS = ['CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU', 'CYOJ', 'CYQL', 'CYLL', 'CYXH', 'CYPE', 'CYQF', 'CYZH', 'CYZU', 'CYXX', 'CBBC', 'CYBL', 'CYCG', 'CYQQ', 'CYXC', 'CYDQ', 'CYDL', 'CYYE', 'CYXJ', 'CYKA', 'CYLW', 'CYZY', 'CZMT', 'CYCD', 'CYYF', 'CYZT', 'CYXS', 'CYPR', 'CYDC', 'CYQZ', 'CYZP', 'CYYD', 'CYXT', 'CYAZ', 'CYVR', 'CYWH', 'CYYJ', 'CYWL', 'CYBR', 'CYYQ', 'CYDN', 'CYGX', 'CYIV', 'CYYL', 'CYPG', 'CYQD', 'CYTH', 'CYWG', 'CYNE', 'CZBF', 'CYFC', 'CYCX', 'CACQ', 'CYQM', 'CYSJ', 'CYSL', 'CYCA', 'CZUM', 'CYDF', 'CYQX', 'CYYR', 'CWWU', 'CYMH', 'CYDP', 'CYAY', 'CYYT', 'CYJT', 'CYWK', 'CYZX', 'CYHZ', 'CWSA', 'CYSA', 'CYAW', 'CYQY', 'CYQI', 'CYOA', 'CYWJ', 'CYGH', 'CZFM', 'CYFS', 'CYSM', 'CYHY', 'CYHI', 'CYEV', 'CYLK', 'CYVQ', 'CYPC', 'CYRA', 'CYSY', 'CYUB', 'CYWE', 'CYZF', 'CYLT', 'CYAB', 'CYEK', 'CYBK', 'CYVM', 'CYCB', 'CYTE',
                        'CYCO', 'CYZS', 'CYCY', 'CYEU', 'CYFB', 'CYHK', 'CYUX', 'CYGT', 'CYWO', 'CYSR', 'CYXP', 'CYBB', 'CYIO', 'CYRT', 'CYUT', 'CYRB', 'CYYH', 'CYTL', 'CYBN', 'CYLD', 'CYHD', 'CYXR', 'CYEL', 'CYGQ', 'CYZE', 'CYHM', 'CYYU', 'CYQK', 'CYGK', 'CWSN', 'CYXU', 'CYSP', 'CYMO', 'CYQA', 'CYYB', 'CYOW', 'CYWA', 'CYPQ', 'CYPL', 'CYRL', 'CYZR', 'CYAM', 'CYXL', 'CYSN', 'CYSB', 'CYTJ', 'CYQT', 'CYTS', 'CYKZ', 'CYTZ', 'CYYZ', 'CYTR', 'CYKF', 'CYXZ', 'CYVV', 'CYQG', 'CYYG', 'CYBG', 'CYBC', 'CYBX', 'CYMT', 'CYGP', 'CYND', 'CYGV', 'CYGR', 'CYPH', 'CYIK', 'CYVP', 'CYGW', 'CYAH', 'CYGL', 'CYYY', 'CYUL', 'CYMX', 'CYNA', 'CYPX', 'CYHA', 'CYQB', 'CYRJ', 'CYUY', 'CYHU', 'CYKL', 'CYZV', 'CYSC', 'CYTQ', 'CYRQ', 'CYVO', 'CYOY', 'CYKQ', 'CYVT', 'CWVP', 'CYEN', 'CYKJ', 'CYVC', 'CYMJ', 'CYQW', 'CYPA', 'CYQR', 'CYXE', 'CYSF', 'CYYN', 'CYQV', 'CYDB', 'CYDA', 'CZFA', 'CYMA', 'CYOC', 'CYZW', 'CYQH', 'CYXY']


def validate_single_station(server, station, verbose=VERBOSE):
    """
    Test if a single station returns valid data.
    
    Args:
        server: NavCanadaWeatherServer instance
        station: Station code to test
        verbose: If True, print detailed output
    
    Returns:
        tuple: (is_valid, data_count, error_message)
    """
    try:
        if verbose:
            print(f"    Testing {station}...", end=" ", flush=True)

        result = server.get_weather([station])
        
        # Count data entries from NavCanadaWeatherResponse object
        data_count = 0
        
        # Count METARs
        for station_metars in result.metars.values():
            data_count += len(station_metars)
        
        # Count TAFs
        for station_tafs in result.tafs.values():
            data_count += len(station_tafs)
        
        # Count Upper Winds
        data_count += len(result.upper_winds)
        
        if data_count > 0:
            if verbose:
                print(f"✓ Valid ({data_count} entries)", flush=True)
            return True, data_count, None
        else:
            if verbose:
                print(f"✗ Invalid (0 reports)", flush=True)
            return False, 0, "No data returned"
            
    except Exception as e:
        error_msg = str(e)
        # Check if it's a parsing error (has data but parsing failed)
        if "NoneType" in error_msg or "timestamp" in error_msg or "attribute" in error_msg:
            if verbose:
                print(f"⚠️ Parsing error: {error_msg[:60]}", flush=True)
            return False, 0, f"Parsing error: {error_msg[:100]}"
        else:
            if verbose:
                print(f"✗ Error: {error_msg[:80]}", flush=True)
            return False, 0, error_msg


def test_batch_has_data(server, stations, verbose=VERBOSE):
    """
    Test if a batch of stations returns any data.
    IMPORTANT: 0 reports is a significant flag indicating invalid station(s).
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to test
        verbose: If True, print detailed output
    
    Returns:
        tuple: (has_data: bool, data_count: int)
            has_data: True if data_count > 0, False if 0 reports
            data_count: Total number of reports returned
    """
    try:
        result = server.get_weather(stations)
        
        # Count data entries from NavCanadaWeatherResponse object
        data_count = 0
        
        # Count METARs
        for station_metars in result.metars.values():
            data_count += len(station_metars)
        
        # Count TAFs
        for station_tafs in result.tafs.values():
            data_count += len(station_tafs)
        
        # Count Upper Winds
        data_count += len(result.upper_winds)
        
        # 0 reports means invalid station(s) present
        return (data_count > 0, data_count)
    except Exception as e:
        # Exception also means failure
        if verbose:
            print(f"    Exception during test: {str(e)[:80]}", flush=True)
        return (False, 0)


def find_invalid_stations_in_batch(server, stations, delay=REQUEST_DELAY, verbose=VERBOSE):
    """
    Use TRUE binary search to efficiently identify invalid stations within this batch.
    
    Binary Search Strategy:
    - We know the full batch failed (returned 0 reports)
    - Test only LEFT half per iteration - if it fails, invalid is in left; if succeeds, invalid is in right
    - This achieves O(log n) complexity with 1 query per iteration instead of 2
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes in THIS GROUP ONLY (max 20)
        delay: Delay between tests (seconds)
        verbose: If True, print detailed search steps
    
    Returns:
        tuple: (valid_stations, invalid_stations_dict)
            invalid_stations_dict: {station_code: error_message}
    """
    if verbose:
        print(
            f"\n  🔍 Binary search for invalid station(s) in this group of {len(stations)}")
    else:
        print(f"  🔍 Finding invalid station(s)...", end=" ", flush=True)
    
    invalid_stations = {}
    remaining = stations.copy()
    search_count = 0
    max_iterations = len(stations) * 2  # Safety limit
    
    while remaining and search_count < max_iterations:
        search_count += 1
        
        # Base case: single station
        if len(remaining) == 1:
            station = remaining[0]
            if verbose:
                print(
                    f"  [{search_count}] Testing final station: {station}...", end=" ", flush=True)
            time.sleep(delay)
            is_valid, data_count, error = validate_single_station(
                server, station, verbose)
            if verbose:
                print()  # newline after validation output
            
            if not is_valid:
                invalid_stations[station] = error or "No data"
                if verbose:
                    print(f"      ❌ {station} is INVALID")
            else:
                if verbose:
                    print(f"      ✓ {station} is valid")
            break
        
        # Binary search: test only LEFT half (KEY OPTIMIZATION!)
        mid = len(remaining) // 2
        left_half = remaining[:mid]
        right_half = remaining[mid:]
        
        if verbose:
            print(f"  [{search_count}] Testing left half ({len(left_half)}/{len(remaining)}): {', '.join(left_half)}...", end=" ", flush=True)
        time.sleep(delay)
        left_has_data, left_count = test_batch_has_data(
            server, left_half, verbose)

        if verbose:
            left_status = f"✓ Valid ({left_count} reports)" if left_has_data else f"✗ Failed (0 reports)"
            print(left_status)
        
        # Decision logic - ONLY 1 query per iteration achieves O(log n)
        if not left_has_data:
            # Left half failed → invalid station(s) in LEFT
            if verbose:
                print(f"  → Invalid station in LEFT half, searching there")
            remaining = left_half
        else:
            # Left half succeeded → invalid station(s) must be in RIGHT
            if verbose:
                print(f"  → LEFT valid, invalid station must be in RIGHT half")
            remaining = right_half

    # Check if we hit max iterations (shouldn't happen with correct logic)
    if search_count >= max_iterations:
        if verbose:
            print(f"  ⚠️  Max iterations reached - testing remaining individually")
        for station in remaining:
            if station not in invalid_stations:
                time.sleep(delay)
                is_valid, data_count, error = validate_single_station(
                    server, station, verbose)
                if not is_valid:
                    invalid_stations[station] = error or "No data"
    
    # Determine valid stations
    valid_stations = [s for s in stations if s not in invalid_stations]
    
    if verbose:
        print(f"\n  ✓ Binary search complete in {search_count} steps")
        print(
            f"    Valid: {len(valid_stations)}, Invalid: {len(invalid_stations)}")
        if invalid_stations:
            print(
                f"    Invalid stations: {', '.join(invalid_stations.keys())}")
    else:
        if invalid_stations:
            print(
                f"Found {len(invalid_stations)} invalid: {', '.join(invalid_stations.keys())}")
        else:
            print(f"No invalid stations found")
    
    return valid_stations, invalid_stations


def query_station_batch(server, stations, group_num, total_groups, 
                        all_invalid_stations, delay=REQUEST_DELAY, verbose=VERBOSE):
    """
    Query a batch of stations with automatic invalid station detection.
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to query
        group_num: Current group number
        total_groups: Total number of groups
        all_invalid_stations: Dict tracking all invalid stations found
        delay: Delay after request (seconds)
        verbose: If True, print detailed output
    
    Returns:
        dict: Query results with statistics
    """
    print(f"\n{'='*80}")
    print(f"📦 Group {group_num}/{total_groups}: {len(stations)} stations")
    if verbose:
        print(f"📍 Stations: {', '.join(stations)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # First, try querying all stations together
    try:
        if verbose:
            print("\n🔄 Attempting batch query...")
        result = server.get_weather(stations)
        
        # Count entries from NavCanadaWeatherResponse object
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_wind_count = len(result.upper_winds)
        total_count = metar_count + taf_count + upper_wind_count
        
        if verbose:
            print(
                f"   Result: {total_count} total reports (METAR: {metar_count}, TAF: {taf_count}, Upper: {upper_wind_count})")
        
        # Check for 0 reports - indicates invalid station(s) present
        if total_count == 0:
            print("⚠️  Batch returned 0 reports - searching for invalid station(s)...")
            time.sleep(delay)
            
            # Binary search within THIS GROUP ONLY (not all stations)
            valid_stations, invalid_dict = find_invalid_stations_in_batch(
                server, stations, delay, verbose
            )
            
            # Update global invalid stations tracker
            all_invalid_stations.update(invalid_dict)
            
            if not valid_stations:
                elapsed = time.time() - start_time
                return {
                    'group_num': group_num,
                    'stations_requested': stations,
                    'valid_stations': [],
                    'invalid_stations': list(invalid_dict.keys()),
                    'metar_count': 0,
                    'taf_count': 0,
                    'upper_wind_count': 0,
                    'total_count': 0,
                    'elapsed_time': elapsed,
                    'success': False,
                    'error': 'All stations invalid - no data returned'
                }
            
            # Retry with valid stations only
            print(f"🔄 Retrying with {len(valid_stations)} valid stations...")
            time.sleep(delay)
            result = server.get_weather(valid_stations)
            
            # Recount from retry
            metar_count = sum(len(metars) for metars in result.metars.values())
            taf_count = sum(len(tafs) for tafs in result.tafs.values())
            upper_wind_count = len(result.upper_winds)
            total_count = metar_count + taf_count + upper_wind_count
            if verbose:
                print(f"   Retry result: {total_count} total reports")
        
        # Success path - got data (either from first query or retry after removing invalid stations)
        elapsed = time.time() - start_time
        
        # Determine which stations from this batch are invalid
        batch_invalid = [s for s in stations if s in all_invalid_stations]
        batch_valid = [s for s in stations if s not in all_invalid_stations]
        
        print(
            f"✅ Group {group_num}: {total_count} reports ({metar_count} METAR, {taf_count} TAF, {upper_wind_count} Upper)", end="")
        if batch_invalid:
            print(f" - Excluded: {', '.join(batch_invalid)}", end="")
        print(f" [{elapsed:.1f}s]")

        if verbose:
            print(f"   Valid stations: {len(batch_valid)}/{len(stations)}")
        
        return {
            'group_num': group_num,
            'stations_requested': stations,
            'valid_stations': batch_valid,
            'invalid_stations': batch_invalid,
            'metar_count': metar_count,
            'taf_count': taf_count,
            'upper_wind_count': upper_wind_count,
            'total_count': total_count,
            'elapsed_time': elapsed,
            'success': True,
            'error': None
            # Note: 'data' object removed - NavCanadaWeatherResponse is not JSON serializable
        }
        
    except Exception as e:
        # Exception during query/parsing - this is a real error, not just "no data"
        elapsed = time.time() - start_time
        error_msg = str(e)

        # Check if this is a PARSING error (data was fetched successfully but parsing failed)
        is_parsing_error = any(keyword in error_msg for keyword in [
            "NoneType", "timestamp", "attribute", "AttributeError", "KeyError"
        ])
        
        if is_parsing_error:
            # PARSING ERROR: Query succeeded, data was fetched, but parser broke
            print(f"❌ Parsing Error: {error_msg}")
            print(
                "⚠️  This is a parser bug - data was fetched successfully but parsing failed")
            print("⚠️  All stations in this batch are valid, the parser needs fixing")

            # Don't search for invalid stations - this is a code bug, not a data issue
            return {
                'group_num': group_num,
                'stations_requested': stations,
                'valid_stations': stations,  # All stations are actually valid
                'invalid_stations': [],
                'metar_count': 0,
                'taf_count': 0,
                'upper_wind_count': 0,
                'total_count': 0,
                'elapsed_time': elapsed,
                'success': False,
                'error': f"Parser bug: {error_msg}"
            }
        else:
            # QUERY ERROR: Network issue, timeout, connection problem, etc.
            print(f"❌ Query Error: {error_msg}")
            print(
                "⚠️  Query failed - this might indicate network issues or invalid stations")

            # In this case, it's unclear if it's network or invalid stations
            # Return error without attempting binary search (too unreliable with network issues)
            return {
                'group_num': group_num,
                'stations_requested': stations,
                'valid_stations': [],
                'invalid_stations': [],
                'metar_count': 0,
                'taf_count': 0,
                'upper_wind_count': 0,
                'total_count': 0,
                'elapsed_time': elapsed,
                'success': False,
                'error': f"Query failed: {error_msg}"
            }


def save_results(output_dir, group_stats, all_invalid_stations):
    """
    Save query results and summary report.
    
    Args:
        output_dir: Output directory path
        group_stats: List of statistics from all groups
        all_invalid_stations: Dict of all invalid stations found
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    results_file = output_dir / f"query_results_{timestamp}.json"
    
    summary = {
        'timestamp': timestamp,
        'total_groups': len(group_stats),
        'successful_groups': sum(1 for g in group_stats if g['success']),
        'failed_groups': sum(1 for g in group_stats if not g['success']),
        'total_stations': sum(len(g['stations_requested']) for g in group_stats),
        'valid_stations': sum(len(g['valid_stations']) for g in group_stats),
        'invalid_stations_count': len(all_invalid_stations),
        'invalid_stations_detail': all_invalid_stations,
        'total_metar': sum(g['metar_count'] for g in group_stats),
        'total_taf': sum(g['taf_count'] for g in group_stats),
        'total_upper_winds': sum(g['upper_wind_count'] for g in group_stats),
        'total_time': sum(g['elapsed_time'] for g in group_stats),
        'group_details': group_stats
    }
    
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"\n✅ Groups: {summary['successful_groups']}/{summary['total_groups']} successful")
    print(f"📍 Stations: {summary['valid_stations']}/{summary['total_stations']} valid")
    
    if all_invalid_stations:
        # Categorize errors
        no_data_stations = {
            k: v for k, v in all_invalid_stations.items() if "No data" in v}
        parsing_error_stations = {k: v for k, v in all_invalid_stations.items(
        ) if "Parsing error" in v or "NoneType" in v}
        other_error_stations = {k: v for k, v in all_invalid_stations.items(
        ) if k not in no_data_stations and k not in parsing_error_stations}

        print(f"\n❌ Problem Stations Found ({len(all_invalid_stations)}):")

        if no_data_stations:
            print(f"\n   No Data ({len(no_data_stations)}):")
            for station, error in sorted(no_data_stations.items()):
                print(f"      • {station}: {error}")

        if parsing_error_stations:
            print(f"\n   Parsing Errors ({len(parsing_error_stations)}):")
            for station, error in sorted(parsing_error_stations.items()):
                print(f"      • {station}: {error[:80]}")

        if other_error_stations:
            print(f"\n   Other Errors ({len(other_error_stations)}):")
            for station, error in sorted(other_error_stations.items()):
                print(f"      • {station}: {error[:80]}")
    
    print(f"\n📈 Data Collected:")
    print(f"   • METAR: {summary['total_metar']}")
    print(f"   • TAF: {summary['total_taf']}")
    print(f"   • Upper Winds: {summary['total_upper_winds']}")
    print(f"   • Total entries: {summary['total_metar'] + summary['total_taf'] + summary['total_upper_winds']}")
    
    print(f"\n⏱️  Total Time: {summary['total_time']:.1f}s")
    print(f"📄 Results saved to: {results_file}")
    print(f"{'='*80}\n")
    
    return results_file


def main():
    """Main execution function"""
    print("\n🌤️  Canadian Weather Stations Data Query v2")
    print(f"{'='*80}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Total stations: {len(CANADIAN_STATIONS)}")
    print(f"📦 Group size: {GROUP_SIZE}")
    print(f"⏱️  Request delay: {REQUEST_DELAY}s")
    print(f"{'='*80}")
    
    # Setup
    output_dir = Path("weather_data")
    output_dir.mkdir(exist_ok=True)
    
    server = NavCanadaWeatherServer(headless=True)
    
    # Split into groups
    groups = [CANADIAN_STATIONS[i:i+GROUP_SIZE] 
              for i in range(0, len(CANADIAN_STATIONS), GROUP_SIZE)]
    
    print(f"\n📦 Created {len(groups)} groups")
    
    # Track invalid stations globally
    all_invalid_stations = {}
    group_stats = []
    
    # Process each group
    for i, stations in enumerate(groups, 1):
        stats = query_station_batch(
            server, stations, i, len(groups), 
            all_invalid_stations, REQUEST_DELAY, VERBOSE
        )
        group_stats.append(stats)
        
        # Delay between groups
        if i < len(groups):
            if VERBOSE:
                print(f"\n⏸️  Waiting {REQUEST_DELAY}s before next group...")
            time.sleep(REQUEST_DELAY)
    
    # Save results
    save_results(output_dir, group_stats, all_invalid_stations)
    
    print("✅ Query complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
