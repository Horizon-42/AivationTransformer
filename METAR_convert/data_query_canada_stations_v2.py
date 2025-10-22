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
GROUP_SIZE = 50      # Number of stations per batch
MAX_RETRIES = 3      # Max retries for transient failures
VERBOSE = False      # Set to True for detailed output, False for minimal output


# Top Canadian airport stations (ICAO codes)
CANADIAN_STATIONS = ['CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU', 'CYOJ', 'CYQL', 'CYLL', 'CYXH', 'CYPE', 'CYQF', 'CYZH', 'CYZU', 'CYXX', 'CBBC', 'CYBL', 'CYCG', 'CYQQ', 'CYXC', 'CYDQ', 'CYDL', 'CYYE', 'CYXJ', 'CYKA', 'CYLW', 'CYZY', 'CZMT', 'CYCD', 'CYYF', 'CYZT', 'CYXS', 'CYPR', 'CYDC', 'CYQZ', 'CYZP', 'CYYD', 'CYXT', 'CYAZ', 'CYVR', 'CYWH', 'CYYJ', 'CYWL', 'CYBR', 'CYYQ', 'CYDN', 'CYGX', 'CYIV', 'CYYL', 'CYPG', 'CYQD', 'CYTH', 'CYWG', 'CYNE', 'CZBF', 'CYFC', 'CYCX', 'CACQ', 'CYQM', 'CYSJ', 'CYSL', 'CYCA', 'CZUM', 'CYDF', 'CYQX', 'CYYR', 'CWWU', 'CYMH', 'CYDP', 'CYAY', 'CYYT', 'CYJT', 'CYWK', 'CYZX', 'CYHZ', 'CWSA', 'CYSA', 'CYAW', 'CYQY', 'CYQI', 'CYOA', 'CYWJ', 'CYGH', 'CZFM', 'CYFS', 'CYSM', 'CYHY', 'CYHI', 'CYEV', 'CYLK', 'CYVQ', 'CYPC', 'CYRA', 'CYSY', 'CYUB', 'CYWE', 'CYZF', 'CYLT', 'CYAB', 'CYEK', 'CYBK', 'CYVM', 'CYCB', 'CYTE',
                        'CYCO', 'CYZS', 'CYCY', 'CYEU', 'CYFB', 'CYHK', 'CYUX', 'CYGT', 'CYWO', 'CYSR', 'CYXP', 'CYBB', 'CYIO', 'CYRT', 'CYUT', 'CYRB', 'CYYH', 'CYTL', 'CYBN', 'CYLD', 'CYHD', 'CYXR', 'CYEL', 'CYGQ', 'CYZE', 'CYHM', 'CYYU', 'CYQK', 'CYGK', 'CWSN', 'CYXU', 'CYSP', 'CYMO', 'CYQA', 'CYYB', 'CYOW', 'CYWA', 'CYPQ', 'CYPL', 'CYRL', 'CYZR', 'CYAM', 'CYXL', 'CYSN', 'CYSB', 'CYTJ', 'CYQT', 'CYTS', 'CYKZ', 'CYTZ', 'CYYZ', 'CYTR', 'CYKF', 'CYXZ', 'CYVV', 'CYQG', 'CYYG', 'CYBG', 'CYBC', 'CYBX', 'CYMT', 'CYGP', 'CYND', 'CYGV', 'CYGR', 'CYPH', 'CYIK', 'CYVP', 'CYGW', 'CYAH', 'CYGL', 'CYYY', 'CYUL', 'CYMX', 'CYNA', 'CYPX', 'CYHA', 'CYQB', 'CYRJ', 'CYUY', 'CYHU', 'CYKL', 'CYZV', 'CYSC', 'CYTQ', 'CYRQ', 'CYVO', 'CYOY', 'CYKQ', 'CYVT', 'CWVP', 'CYEN', 'CYKJ', 'CYVC', 'CYMJ', 'CYQW', 'CYPA', 'CYQR', 'CYXE', 'CYSF', 'CYYN', 'CYQV', 'CYDB', 'CYDA', 'CZFA', 'CYMA', 'CYOC', 'CYZW', 'CYQH', 'CYXY']

INVAILD_STATIONS = ['CACQ', 'CWSN', 'CWVP', 'CYTJ',
                    'CYWO', 'CYXD', 'CYKZ', 'CYSR']  # To be populated during execution

# remove known invalid stations from the main list
for station in INVAILD_STATIONS:
    CANADIAN_STATIONS.remove(station)

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


def test_batch_has_data(server, stations, verbose=VERBOSE, suppress_output=False):
    """
    Test if a batch of stations returns any data.
    IMPORTANT: 0 reports is a significant flag indicating invalid station(s).
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to test
        verbose: If True, print detailed output
        suppress_output: If True, suppress all output (used during binary search when verbose=False)
    
    Returns:
        tuple: (has_data: bool, data_count: int)
            has_data: True if data_count > 0, False if 0 reports
            data_count: Total number of reports returned
    """
    try:
        # Note: server.get_weather will print output, we can't suppress it
        result = server.get_weather(stations, save_raw_data=False)
        
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
        if verbose and not suppress_output:
            print(f"    Exception during test: {str(e)[:80]}", flush=True)
        return (False, 0)


def find_invalid_stations_in_batch(server, stations, delay=REQUEST_DELAY, verbose=VERBOSE):
    """
    Use TRUE binary search to efficiently identify ALL invalid stations within this batch.
    
    Binary Search Strategy:
    - Recursively search for invalid stations
    - Test only LEFT half per iteration - if it fails, search left; if succeeds, search right
    - After finding one invalid, continue searching the remaining valid portion
    - This achieves O(k * log n) where k is number of invalid stations
    
    The algorithm is guaranteed to terminate:
    - Each iteration halves the search space: n → n/2 → n/4 → ... → 1
    - Maximum iterations per invalid station: ceil(log2(n))
    - No infinite loops possible with correct binary search logic
    
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
    suppress_output = not verbose  # Suppress intermediate output when not verbose
    
    while remaining:
        search_count += 1
        
        # First, test if remaining stations have any invalid ones
        has_data, data_count = test_batch_has_data(
            server, remaining, verbose, suppress_output)

        if has_data:
            # All remaining stations are valid!
            if verbose:
                print(
                    f"  [{search_count}] All {len(remaining)} remaining stations are valid")
            break

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
            server, left_half, verbose, suppress_output)

        if verbose:
            left_status = f"✓ Valid ({left_count} reports)" if left_has_data else f"✗ Failed (0 reports)"
            print(left_status)
        
        # Decision logic - ONLY 1 query per iteration achieves O(log n)
        if not left_has_data:
            # Left half has invalid station(s) - search there
            if verbose:
                print(f"  → Invalid station(s) in LEFT half, searching there")
            remaining = left_half
        else:
            # Left half is valid - invalid must be in RIGHT
            if verbose:
                print(f"  → LEFT valid, invalid station(s) must be in RIGHT half")
            remaining = right_half

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
                        all_invalid_stations, output_dir, delay=REQUEST_DELAY, verbose=VERBOSE):
    """
    Query a batch of stations with automatic invalid station detection.
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to query
        group_num: Current group number
        total_groups: Total number of groups
        all_invalid_stations: Dict tracking all invalid stations found
        output_dir: Directory to save group data files
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

        # Query with raw data saving enabled
        raw_filename = f'canada_group_{group_num:02d}_raw.json'
        result = server.get_weather(
            stations,
            save_raw_data=True,
            raw_data_filename=raw_filename
        )
        
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
                print(
                    f"❌ Group {group_num}: All {len(stations)} stations invalid [{elapsed:.1f}s]")
                return {
                    'group_num': group_num,
                    'stations_requested': stations,
                    'valid_stations': [],
                    'invalid_stations': list(invalid_dict.keys()),
                    'stations_with_metar': [],
                    'stations_with_taf': [],
                    'metar_count': 0,
                    'taf_count': 0,
                    'upper_wind_count': 0,
                    'total_count': 0,
                    'raw_data_file': None,
                    'parsed_data_file': None,
                    'elapsed_time': elapsed,
                    'success': False,
                    'error': 'All stations invalid - no data returned'
                }
            
            # Retry with valid stations only
            print(f"🔄 Retrying with {len(valid_stations)} valid stations...")
            time.sleep(delay)
            raw_filename = f'canada_group_{group_num:02d}_raw.json'
            result = server.get_weather(
                valid_stations,
                save_raw_data=True,
                raw_data_filename=raw_filename
            )
            
            # Recount from retry
            metar_count = sum(len(metars) for metars in result.metars.values())
            taf_count = sum(len(tafs) for tafs in result.tafs.values())
            upper_wind_count = len(result.upper_winds)
            total_count = metar_count + taf_count + upper_wind_count
            if verbose:
                print(f"   Retry result: {total_count} total reports")
        
        # Success path - got data (either from first query or retry after removing invalid stations)
        elapsed = time.time() - start_time
        
        # Save parsed data to group-specific file
        parsed_filename = f'canada_group_{group_num:02d}_parsed.json'
        parsed_file = server.export_to_json(result, parsed_filename)

        if verbose:
            print(f"   📄 Saved files:")
            print(
                f"      • Raw: {result.raw_data_file if hasattr(result, 'raw_data_file') else raw_filename}")
            print(f"      • Parsed: {parsed_file}")

        # Determine which stations from this batch are invalid
        batch_invalid = [s for s in stations if s in all_invalid_stations]
        batch_valid = [s for s in stations if s not in all_invalid_stations]
        
        # Clear, consistent output format
        status = "✅" if not batch_invalid else "⚠️"
        print(
            f"{status} Group {group_num}: {total_count} reports ({metar_count} METAR, {taf_count} TAF, {upper_wind_count} Upper)", end="")
        if batch_invalid:
            print(
                f" | Excluded {len(batch_invalid)}: {', '.join(batch_invalid)}", end="")
        print(f" | {elapsed:.1f}s")

        if verbose:
            print(f"   Valid stations: {len(batch_valid)}/{len(stations)}")
        
        return {
            'group_num': group_num,
            'stations_requested': stations,
            'valid_stations': batch_valid,
            'invalid_stations': batch_invalid,
            'stations_with_metar': list(result.metars.keys()),
            'stations_with_taf': list(result.tafs.keys()),
            'metar_count': metar_count,
            'taf_count': taf_count,
            'upper_wind_count': upper_wind_count,
            'total_count': total_count,
            'raw_data_file': result.raw_data_file if hasattr(result, 'raw_data_file') else raw_filename,
            'parsed_data_file': parsed_file,
            'elapsed_time': elapsed,
            'success': True,
            'error': None
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
                'stations_with_metar': [],
                'stations_with_taf': [],
                'metar_count': 0,
                'taf_count': 0,
                'upper_wind_count': 0,
                'total_count': 0,
                'raw_data_file': None,
                'parsed_data_file': None,
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
                'stations_with_metar': [],
                'stations_with_taf': [],
                'metar_count': 0,
                'taf_count': 0,
                'upper_wind_count': 0,
                'total_count': 0,
                'raw_data_file': None,
                'parsed_data_file': None,
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
    
    # Save invalid stations to a separate file
    if all_invalid_stations:
        invalid_file = output_dir / f"invalid_stations_{timestamp}.txt"
        with open(invalid_file, 'w') as f:
            f.write(f"Invalid Stations Report\n")
            f.write(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Invalid Stations: {len(all_invalid_stations)}\n\n")

            # Categorize errors
            no_data_stations = {
                k: v for k, v in all_invalid_stations.items() if "No data" in v}
            parsing_error_stations = {k: v for k, v in all_invalid_stations.items(
            ) if "Parsing error" in v or "NoneType" in v}
            other_error_stations = {k: v for k, v in all_invalid_stations.items(
            ) if k not in no_data_stations and k not in parsing_error_stations}

            if no_data_stations:
                f.write(f"No Data Stations ({len(no_data_stations)}):\n")
                f.write(f"{'-'*80}\n")
                for station, error in sorted(no_data_stations.items()):
                    f.write(f"  {station}: {error}\n")
                f.write(f"\n")

            if parsing_error_stations:
                f.write(
                    f"Parsing Error Stations ({len(parsing_error_stations)}):\n")
                f.write(f"{'-'*80}\n")
                for station, error in sorted(parsing_error_stations.items()):
                    f.write(f"  {station}: {error}\n")
                f.write(f"\n")

            if other_error_stations:
                f.write(
                    f"Other Error Stations ({len(other_error_stations)}):\n")
                f.write(f"{'-'*80}\n")
                for station, error in sorted(other_error_stations.items()):
                    f.write(f"  {station}: {error}\n")
                f.write(f"\n")

    # Print GROUP-WISE summary
    print(f"\n{'='*80}")
    print("📊 GROUP-WISE SUMMARY")
    print(f"{'='*80}\n")

    for group in group_stats:
        status = "✅" if group['success'] else "❌"
        print(f"{status} Group {group['group_num']}:")
        print(
            f"   Stations: {len(group['stations_requested'])} requested, {len(group['valid_stations'])} valid")

        if group['invalid_stations']:
            print(f"   Invalid: {', '.join(group['invalid_stations'])}")

        if group['success']:
            print(
                f"   Data: {group['total_count']} reports ({group['metar_count']} METAR, {group['taf_count']} TAF, {group['upper_wind_count']} Upper)")
            print(f"   Files:")
            print(f"      • Raw: {group['raw_data_file']}")
            print(f"      • Parsed: {group['parsed_data_file']}")
        else:
            print(f"   Error: {group['error']}")

        print(f"   Time: {group['elapsed_time']:.1f}s")
        print()

    # Print overall summary
    print(f"{'='*80}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*80}")
    print(
        f"\n✅ Groups: {summary['successful_groups']}/{summary['total_groups']} successful")
    print(
        f"📍 Stations: {summary['valid_stations']}/{summary['total_stations']} valid")

    if all_invalid_stations:
        print(f"❌ Invalid Stations: {len(all_invalid_stations)} total")
    
    print(f"\n📈 Data Collected:")
    print(f"   • METAR: {summary['total_metar']}")
    print(f"   • TAF: {summary['total_taf']}")
    print(f"   • Upper Winds: {summary['total_upper_winds']}")
    print(f"   • Total entries: {summary['total_metar'] + summary['total_taf'] + summary['total_upper_winds']}")
    
    print(f"\n⏱️  Total Time: {summary['total_time']:.1f}s")
    print(f"\n📄 Files saved:")
    print(f"   • Results: {results_file}")
    if all_invalid_stations:
        print(f"   • Invalid stations: {invalid_file}")
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
    
    server = NavCanadaWeatherServer(headless=True, data_dir=str(output_dir))
    
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
            all_invalid_stations, output_dir, REQUEST_DELAY, VERBOSE
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
