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
GROUP_SIZE = 10      # Number of stations per batch
MAX_RETRIES = 3      # Max retries for transient failures


# Top Canadian airport stations (ICAO codes)
CANADIAN_STATIONS = ['CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU', 'CYOJ', 'CYQL', 'CYLL', 'CYXH', 'CYPE', 'CYQF', 'CYZH', 'CYZU', 'CYXX', 'CBBC', 'CYBL', 'CYCG', 'CYQQ', 'CYXC', 'CYDQ', 'CYDL', 'CYYE', 'CYXJ', 'CYKA', 'CYLW', 'CYZY', 'CZMT', 'CYCD', 'CYYF', 'CYZT', 'CYXS', 'CYPR', 'CYDC', 'CYQZ', 'CYZP', 'CYYD', 'CYXT', 'CYAZ', 'CYVR', 'CYWH', 'CYYJ', 'CYWL', 'CYBR', 'CYYQ', 'CYDN', 'CYGX', 'CYIV', 'CYYL', 'CYPG', 'CYQD', 'CYTH', 'CYWG', 'CYNE', 'CZBF', 'CYFC', 'CYCX', 'CACQ', 'CYQM', 'CYSJ', 'CYSL', 'CYCA', 'CZUM', 'CYDF', 'CYQX', 'CYYR', 'CWWU', 'CYMH', 'CYDP', 'CYAY', 'CYYT', 'CYJT', 'CYWK', 'CYZX', 'CYHZ', 'CWSA', 'CYSA', 'CYAW', 'CYQY', 'CYQI', 'CYOA', 'CYWJ', 'CYGH', 'CZFM', 'CYFS', 'CYSM', 'CYHY', 'CYHI', 'CYEV', 'CYLK', 'CYVQ', 'CYPC', 'CYRA', 'CYSY', 'CYUB', 'CYWE', 'CYZF', 'CYLT', 'CYAB', 'CYEK', 'CYBK', 'CYVM', 'CYCB', 'CYTE',
                        'CYCO', 'CYZS', 'CYCY', 'CYEU', 'CYFB', 'CYHK', 'CYUX', 'CYGT', 'CYWO', 'CYSR', 'CYXP', 'CYBB', 'CYIO', 'CYRT', 'CYUT', 'CYRB', 'CYYH', 'CYTL', 'CYBN', 'CYLD', 'CYHD', 'CYXR', 'CYEL', 'CYGQ', 'CYZE', 'CYHM', 'CYYU', 'CYQK', 'CYGK', 'CWSN', 'CYXU', 'CYSP', 'CYMO', 'CYQA', 'CYYB', 'CYOW', 'CYWA', 'CYPQ', 'CYPL', 'CYRL', 'CYZR', 'CYAM', 'CYXL', 'CYSN', 'CYSB', 'CYTJ', 'CYQT', 'CYTS', 'CYKZ', 'CYTZ', 'CYYZ', 'CYTR', 'CYKF', 'CYXZ', 'CYVV', 'CYQG', 'CYYG', 'CYBG', 'CYBC', 'CYBX', 'CYMT', 'CYGP', 'CYND', 'CYGV', 'CYGR', 'CYPH', 'CYIK', 'CYVP', 'CYGW', 'CYAH', 'CYGL', 'CYYY', 'CYUL', 'CYMX', 'CYNA', 'CYPX', 'CYHA', 'CYQB', 'CYRJ', 'CYUY', 'CYHU', 'CYKL', 'CYZV', 'CYSC', 'CYTQ', 'CYRQ', 'CYVO', 'CYOY', 'CYKQ', 'CYVT', 'CWVP', 'CYEN', 'CYKJ', 'CYVC', 'CYMJ', 'CYQW', 'CYPA', 'CYQR', 'CYXE', 'CYSF', 'CYYN', 'CYQV', 'CYDB', 'CYDA', 'CZFA', 'CYMA', 'CYOC', 'CYZW', 'CYQH', 'CYXY']


def validate_single_station(server, station):
    """
    Test if a single station returns valid data.
    
    Args:
        server: NavCanadaWeatherServer instance
        station: Station code to test
    
    Returns:
        tuple: (is_valid, data_count, error_message)
    """
    try:
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
            print(f"✓ Valid ({data_count} entries)", flush=True)
            return True, data_count, None
        else:
            print(f"✗ Invalid (0 reports)", flush=True)
            return False, 0, "No data returned"
            
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error: {error_msg[:80]}", flush=True)
        return False, 0, error_msg


def test_batch_has_data(server, stations):
    """
    Test if a batch of stations returns any data.
    IMPORTANT: 0 reports is a significant flag indicating invalid station(s).
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to test
    
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
        print(f"    Exception during test: {str(e)[:80]}", flush=True)
        return (False, 0)


def find_invalid_stations_in_batch(server, stations, delay=REQUEST_DELAY):
    """
    Use binary search to efficiently identify invalid stations within this batch only.
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes in THIS GROUP ONLY (max 10)
        delay: Delay between tests (seconds)
    
    Returns:
        tuple: (valid_stations, invalid_stations_dict)
            invalid_stations_dict: {station_code: error_message}
    """
    print(f"\n  🔍 Binary search for invalid station(s) in this group of {len(stations)}")
    
    invalid_stations = {}
    remaining = stations.copy()
    search_count = 0
    max_iterations = len(stations) * 2  # Prevent infinite loops
    
    while remaining and search_count < max_iterations:
        search_count += 1
        
        # Base case: single station
        if len(remaining) == 1:
            station = remaining[0]
            print(f"  [{search_count}] Testing final station: {station}...", end=" ", flush=True)
            time.sleep(delay)
            is_valid, data_count, error = validate_single_station(server, station)
            print()  # newline after validation output
            
            if not is_valid:
                invalid_stations[station] = error or "No data"
                print(f"      ❌ {station} is INVALID")
            else:
                print(f"      ✓ {station} is valid")
            break
        
        # Binary search: split in half
        mid = len(remaining) // 2
        left_half = remaining[:mid]
        right_half = remaining[mid:]
        
        print(f"  [{search_count}] Testing left half ({len(left_half)} stations): {', '.join(left_half)}...", end=" ", flush=True)
        time.sleep(delay)
        left_has_data, left_count = test_batch_has_data(server, left_half)
        left_status = f"✓ Has data ({left_count} reports)" if left_has_data else f"✗ No data (0 reports = INVALID)"
        print(left_status)
        
        print(f"  [{search_count}] Testing right half ({len(right_half)} stations): {', '.join(right_half)}...", end=" ", flush=True)
        time.sleep(delay)
        right_has_data, right_count = test_batch_has_data(server, right_half)
        right_status = f"✓ Has data ({right_count} reports)" if right_has_data else f"✗ No data (0 reports = INVALID)"
        print(right_status)
        
        # Determine next search space
        # KEY FIX: 0 reports means failure, so we search that half
        if not left_has_data and not right_has_data:
            # Both halves fail - search both (could be multiple invalid stations)
            print(f"  → Both halves failed (0 reports) - testing each station individually")
            time.sleep(delay)
            for station in remaining:
                is_valid, data_count, error = validate_single_station(server, station)
                time.sleep(delay)
                if not is_valid:
                    invalid_stations[station] = error or "No data"
            break
        elif not left_has_data:
            # Only left fails - search left half
            print(f"  → Left half has problem (0 reports), searching there")
            remaining = left_half
        elif not right_has_data:
            # Only right fails - search right half
            print(f"  → Right half has problem (0 reports), searching there")
            remaining = right_half
        else:
            # Both halves work individually but original batch didn't
            # This is an edge case - test individually to be safe
            print(f"  ⚠️  Both halves work separately (edge case) - testing individually...")
            time.sleep(delay)
            for station in remaining:
                is_valid, data_count, error = validate_single_station(server, station)
                time.sleep(delay)
                if not is_valid:
                    invalid_stations[station] = error or "No data"
            break
        
        # Safety check: if remaining didn't change, we're stuck
        if len(remaining) == len(stations):
            print(f"  ⚠️  Loop detected - falling back to individual testing")
            for station in remaining:
                time.sleep(delay)
                is_valid, data_count, error = validate_single_station(server, station)
                if not is_valid:
                    invalid_stations[station] = error or "No data"
            break
    
    # Check if we hit max iterations
    if search_count >= max_iterations:
        print(f"  ⚠️  Max iterations reached - testing remaining stations individually")
        for station in remaining:
            if station not in invalid_stations:
                time.sleep(delay)
                is_valid, data_count, error = validate_single_station(server, station)
                if not is_valid:
                    invalid_stations[station] = error or "No data"
    
    # Determine valid stations
    valid_stations = [s for s in stations if s not in invalid_stations]
    
    print(f"\n  ✓ Binary search complete in {search_count} steps")
    print(f"    Valid: {len(valid_stations)}, Invalid: {len(invalid_stations)}")
    if invalid_stations:
        print(f"    Invalid stations: {', '.join(invalid_stations.keys())}")
    
    return valid_stations, invalid_stations


def query_station_batch(server, stations, group_num, total_groups, 
                       all_invalid_stations, delay=REQUEST_DELAY):
    """
    Query a batch of stations with automatic invalid station detection.
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to query
        group_num: Current group number
        total_groups: Total number of groups
        all_invalid_stations: Dict tracking all invalid stations found
        delay: Delay after request (seconds)
    
    Returns:
        dict: Query results with statistics
    """
    print(f"\n{'='*80}")
    print(f"📦 Group {group_num}/{total_groups}")
    print(f"📍 Stations: {', '.join(stations)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # First, try querying all stations together
    try:
        print("\n🔄 Attempting batch query...")
        result = server.get_weather(stations)
        
        # Count entries from NavCanadaWeatherResponse object
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_wind_count = len(result.upper_winds)
        total_count = metar_count + taf_count + upper_wind_count
        
        print(f"   Result: {total_count} total reports (METAR: {metar_count}, TAF: {taf_count}, Upper: {upper_wind_count})")
        
        if total_count == 0:
            print("⚠️  Batch query returned 0 reports - searching for invalid station(s)...")
            time.sleep(delay)
            
            # Binary search within THIS GROUP ONLY (not all stations)
            # 'stations' parameter contains only the current group's 10 stations
            valid_stations, invalid_dict = find_invalid_stations_in_batch(
                server, stations, delay  # stations = current group only
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
                    'error': 'All stations invalid'
                }
            
            # Retry with valid stations only
            print(f"\n🔄 Retrying with {len(valid_stations)} valid stations...")
            time.sleep(delay)
            result = server.get_weather(valid_stations)
            
            # Recount from retry
            metar_count = sum(len(metars) for metars in result.metars.values())
            taf_count = sum(len(tafs) for tafs in result.tafs.values())
            upper_wind_count = len(result.upper_winds)
            total_count = metar_count + taf_count + upper_wind_count
            print(f"   Retry result: {total_count} total reports")
        
        elapsed = time.time() - start_time
        
        # Determine which stations from this batch are invalid
        batch_invalid = [s for s in stations if s in all_invalid_stations]
        batch_valid = [s for s in stations if s not in all_invalid_stations]
        
        print(f"\n✅ Success!")
        print(f"   • METAR: {metar_count}")
        print(f"   • TAF: {taf_count}")
        print(f"   • Upper Winds: {upper_wind_count}")
        print(f"   • Total entries: {total_count}")
        if batch_invalid:
            print(f"   • Invalid stations excluded: {', '.join(batch_invalid)}")
        print(f"   • Time: {elapsed:.1f}s")
        
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
            'error': None,
            'data': result
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        
        # On error, also try to identify invalid stations
        print("🔍 Checking for invalid stations after error...")
        time.sleep(delay)
        
        valid_stations, invalid_dict = find_invalid_stations_in_batch(
            server, stations, delay
        )
        all_invalid_stations.update(invalid_dict)
        
        return {
            'group_num': group_num,
            'stations_requested': stations,
            'valid_stations': valid_stations,
            'invalid_stations': list(invalid_dict.keys()),
            'metar_count': 0,
            'taf_count': 0,
            'upper_wind_count': 0,
            'total_count': 0,
            'elapsed_time': elapsed,
            'success': False,
            'error': error_msg
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
        print(f"\n❌ Invalid Stations Found ({len(all_invalid_stations)}):")
        for station, error in sorted(all_invalid_stations.items()):
            print(f"   • {station}: {error}")
    
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
            all_invalid_stations, REQUEST_DELAY
        )
        group_stats.append(stats)
        
        # Delay between groups
        if i < len(groups):
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
