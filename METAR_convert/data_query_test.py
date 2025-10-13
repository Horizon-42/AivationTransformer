"""
Test Data Query Script - Small Scale Test

This script queries weather data from a small set of Canadian stations for testing.
Tests the grouping and file saving functionality before running the full 100-station query.

Usage:
    python data_query_test.py
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from navcanada_weather_server import NavCanadaWeatherServer
import json


# Test with just 20 stations (2 groups of 10)
TEST_STATIONS = [
    # Group 1: Major airports
    'CYYZ', 'CYVR', 'CYUL', 'CYYC', 'CYEG', 'CYWG', 'CYOW', 'CYHZ', 'CYQB', 'CYVG',
    
    # Group 2: Regional airports
    'CYYJ', 'CYXE', 'CYLW', 'CYQM', 'CYSJ', 'CYFC', 'CYQR', 'CYQX', 'CYHM', 'CYTR'
]


def query_station_group(server: NavCanadaWeatherServer, 
                        stations: list, 
                        group_number: int,
                        output_dir: Path) -> dict:
    """Query weather data for a group of stations"""
    print(f"\n{'='*80}")
    print(f"📊 Processing Group {group_number}")
    print(f"📍 Stations ({len(stations)}): {', '.join(stations)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Query weather data
        response = server.get_weather(
            station_ids=stations,
            save_raw_data=True,
            raw_data_filename=f'test_group_{group_number:02d}_raw.json'
        )
        
        # Export parsed data
        parsed_filename = f'test_group_{group_number:02d}_parsed.json'
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
        
        return stats
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Failed: {str(e)}"
        print(f"\n❌ {error_msg}")
        
        return {
            'group_number': group_number,
            'stations_requested': stations,
            'success': False,
            'error': error_msg,
            'elapsed_time': elapsed_time
        }


def main():
    """Main test execution"""
    print("🌤️  Canadian Weather Stations - TEST QUERY")
    print("="*80)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Test stations: {len(TEST_STATIONS)}")
    print(f"📦 Groups: {(len(TEST_STATIONS) + 9) // 10}")
    print("="*80)
    
    # Initialize
    output_dir = Path("weather_data")
    output_dir.mkdir(exist_ok=True)
    
    server = NavCanadaWeatherServer(headless=True, timeout=60, data_dir=str(output_dir))
    
    # Split into groups of 10
    group_size = 10
    station_groups = [
        TEST_STATIONS[i:i + group_size] 
        for i in range(0, len(TEST_STATIONS), group_size)
    ]
    
    # Query each group
    all_stats = []
    
    for group_num, stations in enumerate(station_groups, start=1):
        stats = query_station_group(server, stations, group_num, output_dir)
        all_stats.append(stats)
        
        # Delay between groups
        if group_num < len(station_groups):
            delay = 3
            print(f"\n⏸️  Waiting {delay} seconds before next group...")
            time.sleep(delay)
    
    # Summary
    print(f"\n{'='*80}")
    print("📋 TEST SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for s in all_stats if s['success'])
    total_metars = sum(s.get('total_metars', 0) for s in all_stats if s['success'])
    total_tafs = sum(s.get('total_tafs', 0) for s in all_stats if s['success'])
    total_time = sum(s['elapsed_time'] for s in all_stats)
    
    print(f"\n✅ Results:")
    print(f"   • Groups processed: {len(all_stats)}")
    print(f"   • Successful: {successful}")
    print(f"   • Failed: {len(all_stats) - successful}")
    print(f"   • METARs collected: {total_metars}")
    print(f"   • TAFs collected: {total_tafs}")
    print(f"   • Total time: {total_time:.2f} seconds")
    print(f"   • Average per group: {total_time/len(all_stats):.2f} seconds")
    
    # Save test summary
    summary_file = output_dir / f'test_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'test_timestamp': datetime.now(timezone.utc).isoformat(),
            'groups': all_stats,
            'summary': {
                'total_groups': len(all_stats),
                'successful': successful,
                'total_metars': total_metars,
                'total_tafs': total_tafs,
                'total_time': total_time
            }
        }, f, indent=2)
    
    print(f"\n📄 Test summary saved to: {summary_file}")
    print(f"{'='*80}\n")
    print("✅ Test complete! If results look good, run data_query_canada_stations.py for full query")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
