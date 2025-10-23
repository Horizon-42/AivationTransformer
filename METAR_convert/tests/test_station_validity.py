"""
Test script to validate Canadian station IDs

Tests each station individually to identify which ones are valid/invalid
"""
from navcanada_weather_server import NavCanadaWeatherServer
import time

# First 10 stations to test
TEST_STATIONS = ['CYYC', 'CYBW', 'CYOD', 'CYEG', 'CYXD', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU']


def validate_station(server, station_id):
    """Helper that validates a single station and returns tuple(status, station_id)."""
    print(f"\n🔍 Testing {station_id}...", end=" ")
    try:
        response = server.get_weather(
            station_ids=[station_id],
            save_raw_data=False
        )
        
        # Check if we got any data
        total_data = (sum(len(v) for v in response.metars.values()) +
                     sum(len(v) for v in response.tafs.values()) +
                     len(response.upper_winds))
        
        if total_data > 0:
            print(f"✅ VALID (got {total_data} records)")
            return True, station_id
        else:
            print(f"⚠️  NO DATA (might be invalid or no current data)")
            return False, station_id
            
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['invalid', 'not found', 'error']):
            print(f"❌ INVALID - {e}")
            return False, station_id
        else:
            print(f"⚠️  ERROR - {e}")
            return False, station_id


def test_single_station(server, station_id):
    is_valid, station = validate_station(server, station_id)
    assert station == station_id
    assert is_valid, f"Expected station {station_id} to return weather data"

def main():
    print("🧪 Canadian Station Validator")
    print("=" * 70)
    print(f"Testing {len(TEST_STATIONS)} stations individually...")
    print("=" * 70)
    
    server = NavCanadaWeatherServer(headless=True, timeout=30)
    
    valid_stations = []
    invalid_stations = []
    
    for station in TEST_STATIONS:
        is_valid, station_id = validate_station(server, station)
        if is_valid:
            valid_stations.append(station_id)
        else:
            invalid_stations.append(station_id)
        
        # Small delay between requests
        time.sleep(1)
    
    print(f"\n{'='*70}")
    print("📊 RESULTS")
    print(f"{'='*70}")
    print(f"\n✅ Valid stations ({len(valid_stations)}):")
    for station in valid_stations:
        print(f"   • {station}")
    
    print(f"\n❌ Invalid/No Data stations ({len(invalid_stations)}):")
    for station in invalid_stations:
        print(f"   • {station}")
    
    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()
