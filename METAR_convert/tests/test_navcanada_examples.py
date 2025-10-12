"""
Nav Canada Simple Client Examples

This script demonstrates the optimized structure:
- METAR/TAF/NOTAM grouped by station
- Upper Wind as a list
- Easy to parse and work with
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from navcanada_simple_client import NavCanadaSimpleClient
import json


def example_simple_extraction():
    """Example: Optimized structure extraction"""
    print("🌤️  Optimized Nav Canada Weather Extraction")
    print("=" * 50)
    print("Structure: METAR/TAF/NOTAM by station, Upper Wind as list")
    print("=" * 50)
    
    # Test with Vancouver
    stations = ['CYVR']
    
    with NavCanadaSimpleClient(headless=True) as client:
        # Get optimized data
        results = client.get_simple_weather_data(stations)
        
        if 'error' not in results:
            summary = results['extraction_summary']
            weather_data = results['weather_data']
            
            print(f"\n✅ Extraction complete!")
            print(f"  • Total entries: {summary['total_entries']}")
            print(f"  • METAR records: {summary.get('metar_records', 0)}")
            print(f"  • TAF records: {summary.get('taf_records', 0)}")
            print(f"  • NOTAM records: {summary.get('notam_records', 0)}")
            print(f"  • Upper Wind records: {summary.get('upper_wind_records', 0)}")
            print(f"  • Stations found: {', '.join(summary['stations_found'])}")
            
            # Show sample entries
            print(f"\n📋 Sample data structure:")
            if weather_data['METAR']:
                for station, entries in list(weather_data['METAR'].items())[:1]:
                    print(f"  METAR['{station}']: {len(entries)} entries")
                    if entries:
                        bulletin_preview = entries[0]['bulletin'][:100] + "..."
                        print(f"    Sample: {bulletin_preview}")
            
            if weather_data['Upper_Wind']:
                print(f"  Upper_Wind: {len(weather_data['Upper_Wind'])} entries")
                bulletin_preview = weather_data['Upper_Wind'][0]['bulletin'][:100] + "..."
                print(f"    Sample: {bulletin_preview}")
            
            # Save data
            filename = client.save_simple_data(results, "optimized_example.json")
            
            if filename:
                print(f"\n📄 Data saved to: {filename}")
        else:
            print(f"❌ Error: {results['error']}")


def example_multiple_stations():
    """Example: Multiple stations optimized extraction"""
    print("\n🌤️  Multiple Stations Optimized Extraction")
    print("=" * 50)
    
    # Test with multiple airports
    stations = ['CYVR', 'CYYC']  # Vancouver, Calgary
    
    with NavCanadaSimpleClient(headless=True) as client:
        results = client.get_simple_weather_data(stations)
        
        if 'error' not in results:
            summary = results['extraction_summary']
            weather_data = results['weather_data']
            
            print(f"\n✅ Multi-station extraction complete!")
            print(f"  • Total entries: {summary['total_entries']}")
            print(f"  • Stations found: {', '.join(summary['stations_found'])}")
            
            # Show breakdown by type
            print(f"\n📊 Data breakdown:")
            print(f"  • METAR: {summary.get('metar_records', 0)} records across {len(weather_data['METAR'])} stations")
            print(f"    Stations: {list(weather_data['METAR'].keys())}")
            print(f"  • TAF: {summary.get('taf_records', 0)} records across {len(weather_data['TAF'])} stations")
            print(f"    Stations: {list(weather_data['TAF'].keys())}")
            print(f"  • Upper Wind: {summary.get('upper_wind_records', 0)} records")
            print(f"  • NOTAM: {summary.get('notam_records', 0)} records across {len(weather_data['NOTAM'])} categories")
            print(f"    Categories: {list(weather_data['NOTAM'].keys())}")
            
            # Save data
            filename = client.save_simple_data(results, "multi_station_optimized.json")
            print(f"\n📄 Multi-station data saved to: {filename}")
        else:
            print(f"❌ Error: {results['error']}")


def example_data_analysis():
    """Example: Analyze the optimized extracted data"""
    print("\n🔍 Optimized Data Analysis Example")
    print("=" * 50)
    
    # Load the optimized data - use path relative to parent directory
    data_file = Path(__file__).parent.parent / "weather_data" / "optimized_example.json"
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        weather_data = data.get('weather_data', {})
        summary = data.get('extraction_summary', {})
        
        print(f"📋 Analyzing optimized data structure...")
        print(f"\n📊 Summary:")
        print(f"  • Total entries: {summary.get('total_entries', 0)}")
        print(f"  • METAR records: {summary.get('metar_records', 0)}")
        print(f"  • TAF records: {summary.get('taf_records', 0)}")
        print(f"  • NOTAM records: {summary.get('notam_records', 0)}")
        print(f"  • Upper Wind records: {summary.get('upper_wind_records', 0)}")
        
        # Show METAR stations
        metar_data = weather_data.get('METAR', {})
        if metar_data:
            print(f"\n🌤️  METAR Stations:")
            for station, entries in metar_data.items():
                print(f"  • {station}: {len(entries)} observation(s)")
                if entries:
                    print(f"    Sample: {entries[0]['bulletin'][:100]}...")
        
        # Show TAF stations
        taf_data = weather_data.get('TAF', {})
        if taf_data:
            print(f"\n📅 TAF Stations:")
            for station, entries in taf_data.items():
                print(f"  • {station}: {len(entries)} forecast(s)")
        
        # Show Upper Wind info
        upper_wind_data = weather_data.get('Upper_Wind', [])
        if upper_wind_data:
            print(f"\n🌬️  Upper Winds:")
            print(f"  • {len(upper_wind_data)} upper wind report(s)")
            print(f"  • Sample (first 200 chars): {upper_wind_data[0]['bulletin'][:200]}...")
        
        # Show NOTAM categories
        notam_data = weather_data.get('NOTAM', {})
        if notam_data:
            print(f"\n📢 NOTAM Categories:")
            for category, entries in notam_data.items():
                print(f"  • {category}: {len(entries)} NOTAM(s)")
        
    except FileNotFoundError:
        print(f"❌ No optimized_example.json found at {data_file}. Run example_simple_extraction() first.")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")


if __name__ == "__main__":
    # Run examples
    example_simple_extraction()
    example_multiple_stations()
    example_data_analysis()
