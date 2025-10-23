"""
Examples for using the TAF parser with optimized Nav Canada structure
"""

from METAR_convert.taf import TAF
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



def example_parse_from_optimized_json():
    """Example: Parse TAF data from optimized Nav Canada JSON"""
    print("\n📅 TAF Parsing from Optimized JSON")
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
    
    taf_data = data["weather_data"].get("TAF", {})
    
    if not taf_data:
        print("❌ No TAF data found in optimized structure")
        return
    
    print(f"📊 Found TAF data for {len(taf_data)} station(s)\n")
    
    # Parse each station's TAF
    for station, entries in taf_data.items():
        print(f"{'='*60}")
        print(f"Station: {station}")
        print(f"{'='*60}")
        
        for i, entry in enumerate(entries, 1):
            print(f"\n📋 TAF Entry #{i}")
            print(f"Extracted at: {entry['extraction_time']}")
            print(f"Row index: {entry['row_index']}")
            print(f"\nRaw bulletin:")
            print(entry['bulletin'])
            print()
            
            # Parse the TAF
            taf = TAF.from_optimized_json(
                entry['bulletin'],
                station,
                entry['extraction_time']
            )
            
            # Display parsed data
            print(f"Parsed TAF:")
            print(f"  🏢 Station: {taf.station_id}")
            print(f"  📅 Issued: {taf.issue_time.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"  ⏰ Valid: {taf.valid_from.strftime('%d/%H:%M')} to {taf.valid_to.strftime('%d/%H:%M UTC')}")
            print(f"  ⏱️  Validity: {taf.validity_hours():.1f} hours")
            print(f"  📊 Forecast Periods: {len(taf.forecast_periods)}")
            
            # Show each forecast period
            if taf.forecast_periods:
                print(f"\n  Forecast Periods:")
                for j, period in enumerate(taf.forecast_periods, 1):
                    change = period.forecast_change_type or "BASE"
                    prob = f" PROB{period.probability_percent}" if period.probability_percent else ""
                    print(f"\n    Period {j}: {change}{prob}")
                    print(f"      Time: {period.valid_from.strftime('%d/%H:%M')}-{period.valid_to.strftime('%d/%H:%M')}")
                    
                    if period.wind_speed_knots:
                        wind_dir = period.wind_direction_degrees if period.wind_direction_degrees != 'VRB' else 'Variable'
                        wind_info = f"{wind_dir}° at {period.wind_speed_knots}kt"
                        if period.wind_gust_knots:
                            wind_info += f" gusting {period.wind_gust_knots}kt"
                        print(f"      Wind: {wind_info}")
                    
                    print(f"      Visibility: {period.visibility} SM")
                    
                    if period.weather_phenomena:
                        print(f"      Weather: {period.weather_phenomena}")
                    
                    if period.cloud_layers:
                        print(f"      Clouds:")
                        for layer in period.cloud_layers:
                            alt = f"{layer.base_altitude_feet}ft" if layer.base_altitude_feet else "N/A"
                            print(f"        {layer.coverage} at {alt}")
                    
                    if period.is_significant_weather():
                        print(f"      ⚠️  SIGNIFICANT WEATHER")
            
            # Show utility methods
            print(f"\n  Analysis:")
            print(f"    Lowest visibility: {taf.get_lowest_visibility()} SM")
            highest_wind = taf.get_highest_wind_speed()
            if highest_wind:
                print(f"    Highest wind speed: {highest_wind}kt")
            
            sig_periods = taf.get_periods_with_weather()
            if sig_periods:
                print(f"    Periods with significant weather: {len(sig_periods)}")


def example_compare_stations():
    """Example: Compare TAF forecasts between stations"""
    print("\n📊 Compare TAF Forecasts")
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
    
    taf_data = data["weather_data"].get("TAF", {})
    
    if not taf_data:
        print("❌ No TAF data found")
        return
    
    print(f"\n{'Station':<8} {'Valid Hours':<12} {'Periods':<10} {'Highest Wind':<15} {'Lowest Vis':<12}")
    print("-" * 70)
    
    for station, entries in taf_data.items():
        if entries:
            taf = TAF.from_optimized_json(entries[0]['bulletin'], station)
            
            valid_hrs = f"{taf.validity_hours():.1f}h"
            periods = len(taf.forecast_periods)
            highest_wind = f"{taf.get_highest_wind_speed()}kt" if taf.get_highest_wind_speed() else "N/A"
            lowest_vis = f"{taf.get_lowest_visibility()} SM"
            
            print(f"{station:<8} {valid_hrs:<12} {periods:<10} {highest_wind:<15} {lowest_vis:<12}")


def example_export_to_json():
    """Example: Parse TAF and export to structured JSON"""
    print("\n💾 Export Parsed TAF to JSON")
    print("=" * 60)
    
    # Load optimized data
    data_path = Path(__file__).parent.parent / "weather_data" / "optimized_example.json"
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ No optimized_example.json found at {data_path}")
        return
    
    taf_data = data["weather_data"].get("TAF", {})
    
    if not taf_data:
        print("❌ No TAF data found")
        return
    
    # Parse and export
    parsed_tafs = {}
    
    for station, entries in taf_data.items():
        parsed_tafs[station] = []
        
        for entry in entries:
            taf = TAF.from_optimized_json(entry['bulletin'], station, entry['extraction_time'])
            parsed_tafs[station].append(taf.to_dict())
    
    # Save to file
    output_path = Path(__file__).parent.parent / "weather_data" / "tafs_parsed.json"
    with open(output_path, "w") as f:
        json.dump(parsed_tafs, f, indent=2, default=str)
    
    print(f"✅ Exported parsed TAF data to {output_path}")
    print(f"\nSample structure (first 800 chars):")
    
    # Show sample
    for station, tafs in list(parsed_tafs.items())[:1]:
        print(f"\n{station}:")
        print(json.dumps(tafs[0], indent=2, default=str)[:800] + "...")


def example_find_bad_weather():
    """Example: Find stations with adverse weather in TAF"""
    print("\n⚠️  Find Adverse Weather Conditions")
    print("=" * 60)
    
    # Load data
    data_path = Path(__file__).parent.parent / "weather_data" / "multi_station_optimized.json"
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ No multi_station_optimized.json found at {data_path}")
        return
    
    taf_data = data["weather_data"].get("TAF", {})
    
    if not taf_data:
        print("❌ No TAF data found")
        return
    
    print("\nScanning TAF forecasts for adverse conditions...\n")
    
    for station, entries in taf_data.items():
        if entries:
            taf = TAF.from_optimized_json(entries[0]['bulletin'], station)
            
            issues = []
            
            # Check for significant weather
            sig_weather_periods = taf.get_periods_with_weather()
            if sig_weather_periods:
                issues.append(f"Significant weather in {len(sig_weather_periods)} period(s)")
            
            # Check for low visibility
            lowest_vis = taf.get_lowest_visibility()
            try:
                if lowest_vis != "6+" and float(lowest_vis.replace('+', '')) < 3:
                    issues.append(f"Low visibility: {lowest_vis} SM")
            except ValueError:
                pass
            
            # Check for high winds
            highest_wind = taf.get_highest_wind_speed()
            if highest_wind and highest_wind > 20:
                issues.append(f"High winds: {highest_wind}kt")
            
            # Display findings
            if issues:
                print(f"⚠️  {station}:")
                for issue in issues:
                    print(f"    • {issue}")
            else:
                print(f"✅ {station}: Good conditions forecast")


def main():
    """Run all TAF examples"""
    print("\n" + "="*60)
    print("📅 TAF PARSER EXAMPLES")
    print("="*60)
    
    example_parse_from_optimized_json()
    example_compare_stations()
    example_export_to_json()
    example_find_bad_weather()
    
    print("\n" + "="*60)
    print("✅ All TAF examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
