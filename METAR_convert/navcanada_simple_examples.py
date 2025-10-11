"""
Nav Canada Simple Client Examples

This script demonstrates the simple approach:
- Metadata column as keys
- Bulletin column as values
- No complex parsing or transformation
"""

from navcanada_simple_client import NavCanadaSimpleClient
import json


def example_simple_extraction():
    """Example: Simple metadata-bulletin extraction"""
    print("🌤️  Simple Nav Canada Weather Extraction")
    print("=" * 50)
    print("Approach: Metadata → Key, Bulletin → Value")
    print("=" * 50)
    
    # Test with Vancouver
    stations = ['CYVR']
    
    with NavCanadaSimpleClient(headless=True) as client:
        # Get simple data
        results = client.get_simple_weather_data(stations)
        
        if 'error' not in results:
            summary = results['extraction_summary']
            weather_data = results['weather_data']
            
            print(f"\n✅ Extraction complete!")
            print(f"  • Total entries: {summary['total_entries']}")
            print(f"  • Stations found: {', '.join(summary['stations_found'])}")
            
            # Show sample entries
            print(f"\n📋 Sample entries:")
            for i, (key, data) in enumerate(list(weather_data.items())[:5]):
                metadata = data['metadata']
                bulletin_preview = data['bulletin'][:100] + "..." if len(data['bulletin']) > 100 else data['bulletin']
                print(f"  {i+1}. {key}")
                print(f"     Metadata: {metadata}")
                print(f"     Bulletin: {bulletin_preview}")
                print()
            
            # Save data
            filename = client.save_simple_data(results, "simple_example.json")
            
            if filename:
                print(f"📄 Data saved to: {filename}")
        else:
            print(f"❌ Error: {results['error']}")


def example_multiple_stations():
    """Example: Multiple stations simple extraction"""
    print("\n🌤️  Multiple Stations Simple Extraction")
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
            
            # Count entries by type
            metar_count = len([k for k in weather_data.keys() if 'METAR' in k])
            taf_count = len([k for k in weather_data.keys() if 'TAF' in k])
            notam_count = len([k for k in weather_data.keys() if 'NOTAM' in k])
            upper_wind_count = len([k for k in weather_data.keys() if 'Upper_Wind' in k])
            
            print(f"\n📊 Data breakdown:")
            print(f"  • METAR observations: {metar_count}")
            print(f"  • TAF forecasts: {taf_count}")
            print(f"  • NOTAMs: {notam_count}")
            print(f"  • Upper winds: {upper_wind_count}")
            
            # Save data
            filename = client.save_simple_data(results, "multi_station_simple.json")
            print(f"\n📄 Multi-station data saved to: {filename}")
        else:
            print(f"❌ Error: {results['error']}")


def example_data_analysis():
    """Example: Analyze the simple extracted data"""
    print("\n🔍 Simple Data Analysis Example")
    print("=" * 50)
    
    # Load the simple data
    try:
        with open('weather_data/simple_example.json', 'r') as f:
            data = json.load(f)
        
        weather_data = data.get('weather_data', {})
        
        print(f"📋 Analyzing {len(weather_data)} entries...")
        
        # Find different data types
        data_types = {}
        for key, entry in weather_data.items():
            metadata = entry['metadata']
            # Extract data type from metadata
            if 'METAR' in metadata:
                data_type = 'METAR'
            elif 'TAF' in metadata:
                data_type = 'TAF'
            elif 'NOTAM' in metadata:
                data_type = 'NOTAM'
            elif 'Upper Wind' in metadata:
                data_type = 'Upper Wind'
            else:
                data_type = 'Other'
            
            if data_type not in data_types:
                data_types[data_type] = []
            data_types[data_type].append(key)
        
        print(f"\n📊 Data types found:")
        for data_type, entries in data_types.items():
            print(f"  • {data_type}: {len(entries)} entries")
        
        # Show upper winds if available
        if 'Upper Wind' in data_types:
            upper_wind_key = data_types['Upper Wind'][0]
            upper_wind_data = weather_data[upper_wind_key]
            print(f"\n🌬️  Upper winds preview:")
            print(f"  Metadata: {upper_wind_data['metadata']}")
            print(f"  Bulletin (first 200 chars): {upper_wind_data['bulletin'][:200]}...")
        
    except FileNotFoundError:
        print("❌ No simple_example.json found. Run example_simple_extraction() first.")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")


if __name__ == "__main__":
    # Run examples
    example_simple_extraction()
    example_multiple_stations()
    example_data_analysis()