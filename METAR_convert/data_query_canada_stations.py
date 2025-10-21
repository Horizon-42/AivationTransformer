"""
Data Query Script for Canadian Aviation Weather Stations

This script queries weather data from 100 Canadian stations using the Nav Canada Weather Server.
Stations are processed in groups of 10, with each group saved to a separate file.

Usage:
    python data_query_canada_stations.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from navcanada_weather_server import NavCanadaWeatherServer


# Top Canadian airport stations (ICAO codes)
# Note: CYXD has been identified as invalid/no data and is excluded
CANADIAN_STATIONS = ['CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU', 'CYOJ', 'CYQL', 'CYLL', 'CYXH', 'CYPE', 'CYQF', 'CYZH', 'CYZU', 'CYXX', 'CBBC', 'CYBL', 'CYCG', 'CYQQ', 'CYXC', 'CYDQ', 'CYDL', 'CYYE', 'CYXJ', 'CYKA', 'CYLW', 'CYZY', 'CZMT', 'CYCD', 'CYYF', 'CYZT', 'CYXS', 'CYPR', 'CYDC', 'CYQZ', 'CYZP', 'CYYD', 'CYXT', 'CYAZ', 'CYVR', 'CYWH', 'CYYJ', 'CYWL', 'CYBR', 'CYYQ', 'CYDN', 'CYGX', 'CYIV', 'CYYL', 'CYPG', 'CYQD', 'CYTH', 'CYWG', 'CYNE', 'CZBF', 'CYFC', 'CYCX', 'CACQ', 'CYQM', 'CYSJ', 'CYSL', 'CYCA', 'CZUM', 'CYDF', 'CYQX', 'CYYR', 'CWWU', 'CYMH', 'CYDP', 'CYAY', 'CYYT', 'CYJT', 'CYWK', 'CYZX', 'CYHZ', 'CWSA', 'CYSA', 'CYAW', 'CYQY', 'CYQI', 'CYOA', 'CYWJ', 'CYGH', 'CZFM', 'CYFS', 'CYSM', 'CYHY', 'CYHI', 'CYEV', 'CYLK', 'CYVQ', 'CYPC', 'CYRA', 'CYSY', 'CYUB', 'CYWE', 'CYZF', 'CYLT', 'CYAB', 'CYEK', 'CYBK', 'CYVM', 'CYCB', 'CYTE',
                     'CYCO', 'CYZS', 'CYCY', 'CYEU', 'CYFB', 'CYHK', 'CYUX', 'CYGT', 'CYWO', 'CYSR', 'CYXP', 'CYBB', 'CYIO', 'CYRT', 'CYUT', 'CYRB', 'CYYH', 'CYTL', 'CYBN', 'CYLD', 'CYHD', 'CYXR', 'CYEL', 'CYGQ', 'CYZE', 'CYHM', 'CYYU', 'CYQK', 'CYGK', 'CWSN', 'CYXU', 'CYSP', 'CYMO', 'CYQA', 'CYYB', 'CYOW', 'CYWA', 'CYPQ', 'CYPL', 'CYRL', 'CYZR', 'CYAM', 'CYXL', 'CYSN', 'CYSB', 'CYTJ', 'CYQT', 'CYTS', 'CYKZ', 'CYTZ', 'CYYZ', 'CYTR', 'CYKF', 'CYXZ', 'CYVV', 'CYQG', 'CYYG', 'CYBG', 'CYBC', 'CYBX', 'CYMT', 'CYGP', 'CYND', 'CYGV', 'CYGR', 'CYPH', 'CYIK', 'CYVP', 'CYGW', 'CYAH', 'CYGL', 'CYYY', 'CYUL', 'CYMX', 'CYNA', 'CYPX', 'CYHA', 'CYQB', 'CYRJ', 'CYUY', 'CYHU', 'CYKL', 'CYZV', 'CYSC', 'CYTQ', 'CYRQ', 'CYVO', 'CYOY', 'CYKQ', 'CYVT', 'CWVP', 'CYEN', 'CYKJ', 'CYVC', 'CYMJ', 'CYQW', 'CYPA', 'CYQR', 'CYXE', 'CYSF', 'CYYN', 'CYQV', 'CYDB', 'CYDA', 'CZFA', 'CYMA', 'CYOC', 'CYZW', 'CYQH', 'CYXY']

# Known invalid stations (excluded from queries)
# Returns no data and causes empty results when queried in batch
# import pandas as pd

# Delay between requests to avoid rate limiting (in seconds)
REQUEST_DELAY = 3.0

# Known invalid stations that return no data
KNOWN_INVALID_STATIONS = set()
KNOWN_INVALID_STATIONS = []


def query_station_group(server: NavCanadaWeatherServer, 
                        stations: list, 
                        group_number: int,
                        output_dir: Path,
                        max_retries: int = 3) -> dict:
    """
    Query weather data for a group of stations with retry logic for invalid stations
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to query
        group_number: Group number for identification
        output_dir: Directory to save output files
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with query results and statistics
    """
    print(f"\n{'='*80}")
    print(f"📊 Processing Group {group_number}")
    print(f"📍 Stations: {', '.join(stations)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    invalid_stations = []
    attempt = 1
    remaining_stations = stations.copy()
    
    while attempt <= max_retries:
        try:
            print(f"\n🔄 Attempt {attempt}/{max_retries}")
            if invalid_stations:
                print(
                    f"⚠️  Excluding invalid stations: {', '.join(invalid_stations)}")

            # Query weather data
            response = server.get_weather(
                station_ids=remaining_stations,
                save_raw_data=True,
                raw_data_filename=f'canada_group_{group_number:02d}_raw.json'
            )

            # Check if the query succeeded
            if hasattr(response, 'extraction_summary'):
                # Check for error messages in the extraction summary
                summary = response.extraction_summary
                if 'error' in summary or 'invalid_stations' in summary:
                    # Extract invalid stations from error message
                    # This depends on how the Nav Canada website reports errors
                    print(
                        "⚠️  Error detected in response, checking for invalid stations...")
                    attempt += 1
                    continue

            # Export parsed data
            parsed_filename = f'canada_group_{group_number:02d}_parsed.json'
            parsed_file = server.export_to_json(response, parsed_filename)

            elapsed_time = time.time() - start_time

            # Collect statistics
            stats = {
                'group_number': group_number,
                'stations_requested': stations,
                'stations_queried': remaining_stations,
                'invalid_stations': invalid_stations,
                'stations_with_metar': list(response.metars.keys()),
                'stations_with_taf': list(response.tafs.keys()),
                'total_metars': sum(len(v) for v in response.metars.values()),
                'total_tafs': sum(len(v) for v in response.tafs.values()),
                'total_upper_winds': len(response.upper_winds),
                'raw_data_file': response.raw_data_file,
                'parsed_data_file': parsed_file,
                'elapsed_time': elapsed_time,
                'attempts': attempt,
                'success': True,
                'error': None
            }

            print(f"\n✅ Group {group_number} Complete!")
            print(
                f"   • METARs: {stats['total_metars']} from {len(stats['stations_with_metar'])} stations")
            print(
                f"   • TAFs: {stats['total_tafs']} from {len(stats['stations_with_taf'])} stations")
            print(f"   • Upper Winds: {stats['total_upper_winds']} reports")
            if invalid_stations:
                print(
                    f"   • Invalid stations excluded: {', '.join(invalid_stations)}")
            print(f"   • Time elapsed: {elapsed_time:.2f} seconds")
            print(f"   • Files saved:")
            print(f"     - {response.raw_data_file}")
            print(f"     - {parsed_file}")

            return stats

        except Exception as e:
            error_str = str(e)
            print(f"\n⚠️  Error on attempt {attempt}: {error_str}")

            # Check if error indicates invalid station(s)
            # Common patterns: "invalid station", "not found", etc.
            if any(keyword in error_str.lower() for keyword in ['invalid', 'not found', 'does not exist']):
                # Try to identify which station is invalid
                # This is a heuristic approach - you may need to adjust based on actual error messages
                if attempt < max_retries:
                    print("🔍 Attempting to identify invalid station...")
                    # Try removing one station at a time (binary search approach)
                    if len(remaining_stations) == 1:
                        invalid_stations.append(remaining_stations[0])
                        print(
                            f"❌ Identified invalid station: {remaining_stations[0]}")
                        remaining_stations = []
                        break
                    else:
                        # Try first half
                        mid = len(remaining_stations) // 2
                        print(f"🔍 Testing first {mid} stations...")
                        remaining_stations = remaining_stations[:mid]
                        attempt += 1
                        time.sleep(2)
                        continue

            # If max retries reached or non-invalid-station error
            if attempt >= max_retries:
                elapsed_time = time.time() - start_time
                error_msg = f"Failed to query group {group_number} after {max_retries} attempts: {error_str}"
                print(f"\n❌ {error_msg}")

                stats = {
                    'group_number': group_number,
                    'stations_requested': stations,
                    'stations_queried': remaining_stations,
                    'invalid_stations': invalid_stations,
                    'stations_with_metar': [],
                    'stations_with_taf': [],
                    'total_metars': 0,
                    'total_tafs': 0,
                    'total_upper_winds': 0,
                    'raw_data_file': None,
                    'parsed_data_file': None,
                    'elapsed_time': elapsed_time,
                    'attempts': attempt,
                    'success': False,
                    'error': error_msg
                }

                return stats

            attempt += 1
            time.sleep(2)

    # If we exit the loop without success
    elapsed_time = time.time() - start_time
    stats = {
        'group_number': group_number,
        'stations_requested': stations,
        'stations_queried': remaining_stations,
        'invalid_stations': invalid_stations,
        'stations_with_metar': [],
        'stations_with_taf': [],
        'total_metars': 0,
        'total_tafs': 0,
        'total_upper_winds': 0,
        'raw_data_file': None,
        'parsed_data_file': None,
        'elapsed_time': elapsed_time,
        'attempts': attempt - 1,
        'success': False,
        'error': f"Failed after {attempt - 1} attempts"
    }

    return stats


def save_summary_report(all_stats: list, output_dir: Path):
    """
    Save a summary report of all queries
    
    Args:
        all_stats: List of statistics dictionaries from all groups
        output_dir: Directory to save the report
    """
    import json
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f'canada_query_summary_{timestamp}.json'
    
    # Calculate totals
    all_invalid_stations = set(
        station for s in all_stats for station in s.get('invalid_stations', []))

    total_stats = {
        'query_timestamp': datetime.now(timezone.utc).isoformat(),
        'total_groups': len(all_stats),
        'successful_groups': sum(1 for s in all_stats if s['success']),
        'failed_groups': sum(1 for s in all_stats if not s['success']),
        'total_stations_requested': sum(len(s['stations_requested']) for s in all_stats),
        'total_invalid_stations': len(all_invalid_stations),
        'invalid_stations_list': list(all_invalid_stations),
        'total_stations_with_metar': len(set(station for s in all_stats for station in s['stations_with_metar'])),
        'total_stations_with_taf': len(set(station for s in all_stats for station in s['stations_with_taf'])),
        'total_metars_collected': sum(s['total_metars'] for s in all_stats),
        'total_tafs_collected': sum(s['total_tafs'] for s in all_stats),
        'total_upper_winds_collected': sum(s['total_upper_winds'] for s in all_stats),
        'total_elapsed_time': sum(s['elapsed_time'] for s in all_stats),
        'average_time_per_group': sum(s['elapsed_time'] for s in all_stats) / len(all_stats) if all_stats else 0,
        'group_details': all_stats
    }
    
    # Save report
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(total_stats, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*80}")
    print("📋 FINAL SUMMARY REPORT")
    print(f"{'='*80}")
    print(f"\n📊 Overall Statistics:")
    print(f"   • Total groups processed: {total_stats['total_groups']}")
    print(f"   • Successful: {total_stats['successful_groups']}")
    print(f"   • Failed: {total_stats['failed_groups']}")
    print(f"   • Total stations requested: {total_stats['total_stations_requested']}")
    print(
        f"   • Invalid stations found: {total_stats['total_invalid_stations']}")
    if total_stats['invalid_stations_list']:
        print(
            f"     Invalid: {', '.join(total_stats['invalid_stations_list'])}")
    print(f"   • Stations with METAR data: {total_stats['total_stations_with_metar']}")
    print(f"   • Stations with TAF data: {total_stats['total_stations_with_taf']}")
    print(f"\n📈 Data Collected:")
    print(f"   • METARs: {total_stats['total_metars_collected']}")
    print(f"   • TAFs: {total_stats['total_tafs_collected']}")
    print(f"   • Upper Wind Reports: {total_stats['total_upper_winds_collected']}")
    print(f"\n⏱️  Performance:")
    print(f"   • Total time: {total_stats['total_elapsed_time']:.2f} seconds")
    print(f"   • Average per group: {total_stats['average_time_per_group']:.2f} seconds")
    print(f"\n📄 Summary report saved to: {report_file}")
    print(f"{'='*80}\n")
    
    return report_file


def main():
    """Main execution function"""
    print("🌤️  Canadian Weather Stations Data Query")
    print("="*80)
    print(f"📅 Query started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Total stations to query: {len(CANADIAN_STATIONS)}")
    print(f"📦 Group size: 10 stations per group")
    print(f"📁 Total groups: {(len(CANADIAN_STATIONS) + 9) // 10}")
    print("="*80)
    
    # Initialize server
    output_dir = Path("weather_data")
    output_dir.mkdir(exist_ok=True)
    
    server = NavCanadaWeatherServer(headless=True, timeout=60, data_dir=str(output_dir))
    
    # Split stations into groups of 10
    group_size = 10
    station_groups = [
        CANADIAN_STATIONS[i:i + group_size] 
        for i in range(0, len(CANADIAN_STATIONS), group_size)
    ]
    
    print(f"\n📦 Created {len(station_groups)} groups")
    
    # Query each group
    all_stats = []
    
    for group_num, stations in enumerate(station_groups[:1], start=1):
        # Query the group
        stats = query_station_group(server, stations, group_num, output_dir)
        all_stats.append(stats)
        
        # Add delay between groups to avoid overwhelming the server
        if group_num < len(station_groups):
            delay = 5  # 5 seconds between groups
            print(f"\n⏸️  Waiting {delay} seconds before next group...")
            time.sleep(delay)
    
    # Save summary report
    report_file = save_summary_report(all_stats, output_dir)
    
    # Print failed groups if any
    failed_groups = [s for s in all_stats if not s['success']]
    if failed_groups:
        print(f"\n⚠️  Warning: {len(failed_groups)} group(s) failed:")
        for stats in failed_groups:
            print(f"   • Group {stats['group_number']}: {stats['error']}")
    
    print("\n✅ Data query complete!")
    print(f"📁 All files saved to: {output_dir.absolute()}")
    print(f"📋 Summary report: {report_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Query interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
