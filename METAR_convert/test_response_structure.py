"""
Quick test to verify the NavCanadaWeatherResponse object handling is correct.
"""

import sys
sys.path.insert(0, '/Users/liudongxu/Desktop/studys/aviation_transformer/METAR_convert')

from navcanada_weather_server import NavCanadaWeatherServer

def test_response_structure():
    """Test that we're correctly accessing NavCanadaWeatherResponse attributes"""
    print("="*80)
    print("Testing NavCanadaWeatherResponse Object Access")
    print("="*80)
    
    server = NavCanadaWeatherServer(headless=True)
    
    # Test with a known valid station
    print("\n1. Testing valid station (CYYC)...")
    try:
        result = server.get_weather(['CYYC'])
        
        print(f"   Type: {type(result)}")
        print(f"   Has 'metars' attribute: {hasattr(result, 'metars')}")
        print(f"   Has 'tafs' attribute: {hasattr(result, 'tafs')}")
        print(f"   Has 'upper_winds' attribute: {hasattr(result, 'upper_winds')}")
        
        # Count data
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_count = len(result.upper_winds)
        total = metar_count + taf_count + upper_count
        
        print(f"\n   ✅ Data counts:")
        print(f"      METARs: {metar_count}")
        print(f"      TAFs: {taf_count}")
        print(f"      Upper Winds: {upper_count}")
        print(f"      Total: {total}")
        
        if total > 0:
            print(f"\n   ✅ SUCCESS: Got {total} reports for CYYC")
        else:
            print(f"\n   ⚠️  WARNING: 0 reports for CYYC (unexpected)")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with known invalid station
    print("\n2. Testing invalid station (CYXD)...")
    try:
        result = server.get_weather(['CYXD'])
        
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_count = len(result.upper_winds)
        total = metar_count + taf_count + upper_count
        
        print(f"   Data counts:")
        print(f"      METARs: {metar_count}")
        print(f"      TAFs: {taf_count}")
        print(f"      Upper Winds: {upper_count}")
        print(f"      Total: {total}")
        
        if total == 0:
            print(f"\n   ✅ SUCCESS: Got 0 reports for CYXD (expected)")
        else:
            print(f"\n   ⚠️  UNEXPECTED: Got {total} reports for CYXD")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test with mixed batch (valid + invalid)
    print("\n3. Testing mixed batch (CYYC + CYXD)...")
    try:
        result = server.get_weather(['CYYC', 'CYXD'])
        
        metar_count = sum(len(metars) for metars in result.metars.values())
        taf_count = sum(len(tafs) for tafs in result.tafs.values())
        upper_count = len(result.upper_winds)
        total = metar_count + taf_count + upper_count
        
        print(f"   Data counts:")
        print(f"      METARs: {metar_count}")
        print(f"      TAFs: {taf_count}")
        print(f"      Upper Winds: {upper_count}")
        print(f"      Total: {total}")
        
        if total == 0:
            print(f"\n   ✅ This confirms: Invalid station in batch causes 0 reports")
        else:
            print(f"\n   ⚠️  Got {total} reports with invalid station present")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "="*80)
    print("Test Complete")
    print("="*80)


if __name__ == "__main__":
    test_response_structure()
