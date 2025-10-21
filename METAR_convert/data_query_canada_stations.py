"""
Data Query Script for Canadian Aviation Weather Stations

This script queries weather data from 100 Canadian stations using the Nav Canada Weather Server.
Stations are processed in groups of 10, with each group saved to a separate file.

Usage:
    python data_query_canada_stations.py
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from navcanada_weather_server import NavCanadaWeatherServer


# Top 100 Canadian airport stations (ICAO codes)
CANADIAN_STATIONS = [
    # Major International Airports (Top 20)
    'CYYZ', 'CYVR', 'CYUL', 'CYYC', 'CYEG', 'CYWG', 'CYOW', 'CYHZ', 
    'CYQB', 'CYVG', 'CYYJ', 'CYXE', 'CYLW', 'CYQM', 'CYSJ', 'CYFC',
    'CYQR', 'CYQX', 'CYHM', 'CYTR',
    
    # Regional Airports (20-40)
    'CYKA', 'CYCD', 'CYPQ', 'CYZF', 'CYXY', 'CYQT', 'CYYG', 'CYQI',
    'CYZR', 'CYPR', 'CYXJ', 'CYOD', 'CYXC', 'CYBL', 'CYXS', 'CYZV',
    'CYGR', 'CYTH', 'CYXU', 'CYZT',
    
    # Northern and Remote Airports (40-60)
    'CYLT', 'CYZP', 'CYFB', 'CYVM', 'CYEV', 'CYFS', 'CYVP', 'CYXT',
    'CYZW', 'CYYR', 'CYXH', 'CYOC', 'CYLJ', 'CYYF', 'CYZH', 'CYGH',
    'CYOW', 'CYPX', 'CYAX', 'CYBG',
    
    # Smaller Regional (60-80)
    'CYQV', 'CYXL', 'CYXN', 'CYXP', 'CYXR', 'CYXZ', 'CYYA', 'CYYB',
    'CYYE', 'CYYH', 'CYYN', 'CYYT', 'CYYY', 'CYZD', 'CYZE', 'CYZG',
    'CYZM', 'CYZO', 'CYZS', 'CYZX',
    
    # Additional Stations (80-100)
    'CYAB', 'CYAC', 'CYAD', 'CYAH', 'CYAL', 'CYAM', 'CYAQ', 'CYAT',
    'CYAW', 'CYAY', 'CYAZ', 'CYBA', 'CYBB', 'CYBC', 'CYBK', 'CYBN',
    'CYBO', 'CYBQ', 'CYBR', 'CYBT'
]


def query_station_group(server: NavCanadaWeatherServer, 
                        stations: list, 
                        group_number: int,
                        output_dir: Path) -> dict:
    """
    Query weather data for a group of stations
    
    Args:
        server: NavCanadaWeatherServer instance
        stations: List of station codes to query
        group_number: Group number for identification
        output_dir: Directory to save output files
        
    Returns:
        Dictionary with query results and statistics
    """
    print(f"\n{'='*80}")
    print(f"📊 Processing Group {group_number}")
    print(f"📍 Stations: {', '.join(stations)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Query weather data
        response = server.get_weather(
            station_ids=stations,
            save_raw_data=True,
            raw_data_filename=f'canada_group_{group_number:02d}_raw.json'
        )
        
        # Export parsed data
        parsed_filename = f'canada_group_{group_number:02d}_parsed.json'
        parsed_file = server.export_to_json(response, parsed_filename)
        
        elapsed_time = time.time() - start_time
        
        # Collect statistics
        stats = {
            'group_number': group_number,
            'stations_requested': stations,
            'stations_with_metar': list(response.metars.keys()),
            'stations_with_taf': list(response.tafs.keys()),
            'total_metars': sum(len(v) for v in response.metars.values()),
            'total_tafs': sum(len(v) for v in response.tafs.values()),
            'total_upper_winds': len(response.upper_winds),
            'raw_data_file': response.raw_data_file,
            'parsed_data_file': parsed_file,
            'elapsed_time': elapsed_time,
            'success': True,
            'error': None
        }
        
        print(f"\n✅ Group {group_number} Complete!")
        print(f"   • METARs: {stats['total_metars']} from {len(stats['stations_with_metar'])} stations")
        print(f"   • TAFs: {stats['total_tafs']} from {len(stats['stations_with_taf'])} stations")
        print(f"   • Upper Winds: {stats['total_upper_winds']} reports")
        print(f"   • Time elapsed: {elapsed_time:.2f} seconds")
        print(f"   • Files saved:")
        print(f"     - {response.raw_data_file}")
        print(f"     - {parsed_file}")
        
        return stats
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Failed to query group {group_number}: {str(e)}"
        print(f"\n❌ {error_msg}")
        
        stats = {
            'group_number': group_number,
            'stations_requested': stations,
            'stations_with_metar': [],
            'stations_with_taf': [],
            'total_metars': 0,
            'total_tafs': 0,
            'total_upper_winds': 0,
            'raw_data_file': None,
            'parsed_data_file': None,
            'elapsed_time': elapsed_time,
            'success': False,
            'error': error_msg
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
    total_stats = {
        'query_timestamp': datetime.now(timezone.utc).isoformat(),
        'total_groups': len(all_stats),
        'successful_groups': sum(1 for s in all_stats if s['success']),
        'failed_groups': sum(1 for s in all_stats if not s['success']),
        'total_stations_requested': sum(len(s['stations_requested']) for s in all_stats),
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
    
    for group_num, stations in enumerate(station_groups, start=1):
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
