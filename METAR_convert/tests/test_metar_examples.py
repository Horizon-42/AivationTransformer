"""
Examples for using the METAR parser with optimized Nav Canada structure
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from metar import METAR


def example_parse_from_optimized_json():
    """Example: Parse METAR data from optimized Nav Canada JSON"""
    print("\n🌤️  METAR Parsing from Optimized JSON")
    print("=" * 60)
    
    # Load optimized data
    data_path = Path(__file__).parent.parent / "weather_data" / "optimized_example.json"
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ No optimized_example.json found at {data_path}")
        print("Run navcanada_simple_examples.py first from the parent directory.")
        return
    
    metar_data = data["weather_data"].get("METAR", {})
    
    if not metar_data:
        print("❌ No METAR data found in optimized structure")
        return
    
    print(f"📊 Found METAR data for {len(metar_data)} station(s)\n")
    
    # Parse each station's METAR
    for station, entries in metar_data.items():
        print(f"{'='*60}")
        print(f"Station: {station}")
        print(f"{'='*60}")
        
        for i, entry in enumerate(entries, 1):
            print(f"\n📋 METAR Entry #{i}")
            print(f"Raw bulletin: {entry['bulletin'][:80]}...")
            print(f"Extracted at: {entry['extraction_time']}")
            print(f"Row index: {entry['row_index']}\n")
            
            # Parse the METAR
            metar = METAR.from_optimized_json(
                entry['bulletin'],
                station,
                entry['extraction_time']
            )
            
            # Display parsed data
            print(f"Parsed METAR:")
            print(f"  🏢 Station: {metar.station_id}")
            print(f"  📅 Observation Time: {metar.observation_time.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"  🌡️  Temperature: {metar.temperature_celsius}°C ({metar.temperature_fahrenheit():.1f}°F)")
            print(f"  💧 Dewpoint: {metar.dewpoint_celsius}°C ({metar.dewpoint_fahrenheit():.1f}°F)")
            
            if metar.wind_speed_knots:
                wind_dir = "Variable" if metar.wind_variable else f"{metar.wind_direction_degrees}°"
                wind_info = f"{wind_dir} at {metar.wind_speed_knots}kt"
                if metar.wind_gust_knots:
                    wind_info += f" gusting {metar.wind_gust_knots}kt"
                print(f"  🌬️  Wind: {wind_info}")
            else:
                print(f"  🌬️  Wind: Calm")
            
            print(f"  👁️  Visibility: {metar.visibility} SM")
            print(f"  ☁️  Sky: {metar.sky_coverage}")
            
            if metar.cloud_layers:
                print(f"  ☁️  Cloud Layers:")
                for layer in metar.cloud_layers:
                    alt_str = f"{layer.altitude_feet}ft" if layer.altitude_feet else "N/A"
                    type_str = f" {layer.cloud_type}" if layer.cloud_type else ""
                    print(f"      {layer.coverage} at {alt_str}{type_str}")
            
            print(f"  🛫 Flight Category: {metar.flight_category}")
            print(f"  📊 Altimeter: {metar.altimeter_hpa:.1f} hPa ({metar.altimeter_inches_hg():.2f}\")")
            
            # Show conditions
            print(f"\n  Conditions:")
            print(f"    VFR: {'✅ Yes' if metar.is_vfr() else '❌ No'}")
            print(f"    IFR: {'✅ Yes' if metar.is_ifr() else '❌ No'}")


def example_parse_multiple_stations():
    """Example: Parse and compare METAR from multiple stations"""
    print("\n📊 Compare METAR from Multiple Stations")
    print("=" * 60)
    
    # Load data with multiple stations
    data_path = Path(__file__).parent.parent / "weather_data" / "multi_station_optimized.json"
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ No multi_station_optimized.json found at {data_path}")
        print("Run navcanada_simple_examples.py first from the parent directory.")
        return
    
    metar_data = data["weather_data"].get("METAR", {})
    
    if not metar_data:
        print("❌ No METAR data found")
        return
    
    print(f"\n{'Station':<8} {'Temp(°C)':<10} {'Wind(kt)':<10} {'Vis':<8} {'Flight Cat':<12}")
    print("-" * 60)
    
    for station, entries in metar_data.items():
        if entries:
            metar = METAR.from_optimized_json(entries[0]['bulletin'], station)
            
            temp = f"{metar.temperature_celsius:.1f}"
            wind = f"{metar.wind_speed_knots or 0}" + (f"G{metar.wind_gust_knots}" if metar.wind_gust_knots else "")
            vis = metar.visibility
            flt_cat = metar.flight_category
            
            print(f"{station:<8} {temp:<10} {wind:<10} {vis:<8} {flt_cat:<12}")


def example_export_to_json():
    """Example: Parse METAR and export to structured JSON"""
    print("\n💾 Export Parsed METAR to JSON")
    print("=" * 60)
    
    # Load optimized data
    data_path = Path(__file__).parent.parent / "weather_data" / "optimized_example.json"
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ No optimized_example.json found at {data_path}")
        return
    
    metar_data = data["weather_data"].get("METAR", {})
    
    if not metar_data:
        print("❌ No METAR data found")
        return
    
    # Parse and export
    parsed_metars = {}
    
    for station, entries in metar_data.items():
        parsed_metars[station] = []
        
        for entry in entries:
            metar = METAR.from_optimized_json(entry['bulletin'], station, entry['extraction_time'])
            parsed_metars[station].append(metar.to_dict())
    
    # Save to file
    output_path = Path(__file__).parent.parent / "weather_data" / "metars_parsed.json"
    with open(output_path, "w") as f:
        json.dump(parsed_metars, f, indent=2, default=str)
    
    print(f"✅ Exported parsed METAR data to {output_path}")
    print(f"\nSample structure:")
    
    # Show sample
    for station, metars in list(parsed_metars.items())[:1]:
        print(f"\n{station}:")
        print(json.dumps(metars[0], indent=2, default=str)[:500] + "...")


def main():
    """Run all METAR examples"""
    print("\n" + "="*60)
    print("🌤️  METAR PARSER EXAMPLES")
    print("="*60)
    
    example_parse_from_optimized_json()
    example_parse_multiple_stations()
    example_export_to_json()
    
    print("\n" + "="*60)
    print("✅ All METAR examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
