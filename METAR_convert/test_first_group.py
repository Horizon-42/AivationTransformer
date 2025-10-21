"""
Quick test of data_query_canada_stations_v2.py with just the first group
to verify all fixes are working correctly.
"""

import sys
sys.path.insert(0, '/Users/liudongxu/Desktop/studys/aviation_transformer/METAR_convert')

from pathlib import Path
from navcanada_weather_server import NavCanadaWeatherServer
import time

# Import the functions from our script
REQUEST_DELAY = 3.0  # Shorter delay for testing

def test_batch_has_data(server, stations):
    """Test if a batch returns data - using correct NavCanadaWeatherResponse attributes"""
    try:
        result = server.get_weather(stations)
        
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_count = len(result.upper_winds)
        data_count = metar_count + taf_count + upper_count
        
        return (data_count > 0, data_count)
    except Exception as e:
        print(f"    Exception: {str(e)[:80]}", flush=True)
        return (False, 0)


def validate_single_station(server, station):
    """Test single station"""
    try:
        print(f"    Testing {station}...", end=" ", flush=True)
        result = server.get_weather([station])
        
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_count = len(result.upper_winds)
        data_count = metar_count + taf_count + upper_count
        
        if data_count > 0:
            print(f"✓ Valid ({data_count} reports)", flush=True)
            return True, data_count, None
        else:
            print(f"✗ Invalid (0 reports)", flush=True)
            return False, 0, "No data"
    except Exception as e:
        print(f"✗ Error: {str(e)[:80]}", flush=True)
        return False, 0, str(e)


def simple_binary_search(server, stations, delay=REQUEST_DELAY):
    """Simplified binary search for first group"""
    print(f"\n🔍 Binary search in group of {len(stations)}")
    print(f"   Stations: {', '.join(stations)}")
    
    invalid_stations = {}
    remaining = stations.copy()
    step = 0
    max_steps = len(stations) * 2
    
    while remaining and step < max_steps:
        step += 1
        
        if len(remaining) == 1:
            station = remaining[0]
            print(f"\n[Step {step}] Final station: {station}")
            time.sleep(delay)
            is_valid, count, error = validate_single_station(server, station)
            if not is_valid:
                invalid_stations[station] = error or "No data"
            break
        
        mid = len(remaining) // 2
        left = remaining[:mid]
        right = remaining[mid:]
        
        print(f"\n[Step {step}]")
        print(f"  Left:  {', '.join(left)}")
        print(f"  Right: {', '.join(right)}")
        
        time.sleep(delay)
        left_ok, left_count = test_batch_has_data(server, left)
        print(f"  Left result:  {'✓' if left_ok else '✗'} ({left_count} reports)")
        
        time.sleep(delay)
        right_ok, right_count = test_batch_has_data(server, right)
        print(f"  Right result: {'✓' if right_ok else '✗'} ({right_count} reports)")
        
        if not left_ok and not right_ok:
            print(f"  → Both failed - testing individually")
            for s in remaining:
                time.sleep(delay)
                is_valid, _, error = validate_single_station(server, s)
                if not is_valid:
                    invalid_stations[s] = error
            break
        elif not left_ok:
            print(f"  → Searching LEFT (0 reports)")
            remaining = left
        elif not right_ok:
            print(f"  → Searching RIGHT (0 reports)")
            remaining = right
        else:
            print(f"  → Both work (edge case) - testing individually")
            for s in remaining:
                time.sleep(delay)
                is_valid, _, error = validate_single_station(server, s)
                if not is_valid:
                    invalid_stations[s] = error
            break
    
    valid = [s for s in stations if s not in invalid_stations]
    
    print(f"\n✓ Binary search complete:")
    print(f"  Valid: {len(valid)} - {', '.join(valid) if valid else 'none'}")
    print(f"  Invalid: {len(invalid_stations)} - {', '.join(invalid_stations.keys()) if invalid_stations else 'none'}")
    
    return valid, invalid_stations


def main():
    print("="*80)
    print("TESTING FIRST GROUP WITH BINARY SEARCH")
    print("="*80)
    
    # First group with CYXD (invalid)
    first_group = ['CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU']
    
    print(f"\nFirst group: {', '.join(first_group)}")
    print(f"Known invalid: CYXD")
    
    server = NavCanadaWeatherServer(headless=True)
    
    # Test full batch first
    print("\n" + "-"*80)
    print("STEP 1: Test full batch")
    print("-"*80)
    has_data, count = test_batch_has_data(server, first_group)
    print(f"\nFull batch result: {'✓ Has data' if has_data else '✗ No data'} ({count} reports)")
    
    if count == 0:
        print("\n✓ Confirmed: 0 reports means invalid station present")
        print("   Now running binary search to find it...")
        
        time.sleep(REQUEST_DELAY)
        
        print("\n" + "-"*80)
        print("STEP 2: Binary search")
        print("-"*80)
        valid, invalid = simple_binary_search(server, first_group, REQUEST_DELAY)
        
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        
        if 'CYXD' in invalid:
            print("✅ SUCCESS: Found CYXD as invalid!")
        else:
            print("❌ FAILED: Did not identify CYXD as invalid")
        
        print(f"\nValid stations ({len(valid)}): {', '.join(valid)}")
        print(f"Invalid stations ({len(invalid)}): {', '.join(invalid.keys())}")
    else:
        print(f"\n⚠️  Unexpected: Full batch returned {count} reports")
        print("   (Expected 0 reports due to CYXD)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
