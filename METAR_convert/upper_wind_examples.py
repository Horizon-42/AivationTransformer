"""
Examples for using the Upper Wind parser with optimized Nav Canada structure
"""

import json
from upper_wind import UpperWind


def example_parse_upper_winds():
    """Example: Parse upper wind data from optimized structure"""
    print("\n🌬️  Upper Wind Parsing Example")
    print("=" * 60)
    
    # Load optimized data
    with open("weather_data/optimized_example.json", "r") as f:
        data = json.load(f)
    
    # Access Upper_Wind list from optimized structure
    upper_wind_list = data["weather_data"].get("Upper_Wind", [])
    
    if not upper_wind_list:
        print("❌ No upper wind data found")
        return
    
    print(f"📊 Found {len(upper_wind_list)} upper wind report(s)\n")
    
    # Parse each upper wind bulletin
    for i, entry in enumerate(upper_wind_list, 1):
        print(f"{'='*60}")
        print(f"Upper Wind Report #{i}")
        print(f"Extracted at: {entry['extraction_time']}")
        print(f"Row index: {entry['row_index']}")
        print(f"{'='*60}\n")
        
        # Parse the bulletin
        upper_wind = UpperWind.from_bulletin(entry["bulletin"])
        
        # Display each period
        for period in upper_wind.periods:
            print(f"📅 VALID: {period.valid_time}")
            print(f"⏰ FOR USE: {period.use_period}")
            print(f"📍 Stations: {', '.join(period.stations.keys())}\n")
            
            for station, levels in period.stations.items():
                print(f"  Station: {station}")
                print(f"  {'Altitude':<10} {'Direction':<12} {'Speed':<10} {'Temperature':<12}")
                print(f"  {'-'*50}")
                
                for level in levels:
                    alt = f"{level.altitude_ft}ft"
                    dir_str = f"{level.direction_deg}°" if level.direction_deg is not None else "N/A"
                    spd_str = f"{level.speed_kt}kt" if level.speed_kt is not None else "N/A"
                    temp_str = f"{level.temperature_c}°C" if level.temperature_c is not None else "N/A"
                    
                    print(f"  {alt:<10} {dir_str:<12} {spd_str:<10} {temp_str:<12}")
                print()


def example_find_strong_winds():
    """Example: Find altitudes with strong winds (>50kt)"""
    print("\n💨 Finding Strong Winds (>50kt)")
    print("=" * 60)
    
    # Load optimized data
    with open("weather_data/optimized_example.json", "r") as f:
        data = json.load(f)
    
    upper_wind_list = data["weather_data"].get("Upper_Wind", [])
    
    if not upper_wind_list:
        print("❌ No upper wind data found")
        return
    
    # Parse and analyze
    for entry in upper_wind_list:
        upper_wind = UpperWind.from_bulletin(entry["bulletin"])
        
        for period in upper_wind.periods:
            print(f"\n📅 Period: VALID {period.valid_time} FOR USE {period.use_period}")
            
            strong_winds_found = False
            for station, levels in period.stations.items():
                for level in levels:
                    if level.speed_kt and level.speed_kt > 50:
                        if not strong_winds_found:
                            print(f"  🌪️  Strong winds for {station}:")
                            strong_winds_found = True
                        print(f"    {level.altitude_ft}ft: {level.direction_deg}° at {level.speed_kt}kt, {level.temperature_c}°C")
            
            if not strong_winds_found:
                print(f"  ✅ No strong winds (all <50kt)")


def example_get_wind_at_altitude():
    """Example: Get wind conditions at specific altitude"""
    print("\n🎯 Wind at Specific Altitude")
    print("=" * 60)
    
    target_altitude = 30000  # FL300
    
    # Load optimized data
    with open("weather_data/optimized_example.json", "r") as f:
        data = json.load(f)
    
    upper_wind_list = data["weather_data"].get("Upper_Wind", [])
    
    if not upper_wind_list:
        print("❌ No upper wind data found")
        return
    
    print(f"🔍 Looking for winds at {target_altitude}ft (FL{target_altitude//100})\n")
    
    # Parse and find
    for entry in upper_wind_list:
        upper_wind = UpperWind.from_bulletin(entry["bulletin"])
        
        for period in upper_wind.periods:
            print(f"📅 VALID {period.valid_time} FOR USE {period.use_period}")
            
            for station, levels in period.stations.items():
                for level in levels:
                    if level.altitude_ft == target_altitude:
                        if level.speed_kt is not None:
                            print(f"  {station}: {level.direction_deg}° at {level.speed_kt}kt, temp {level.temperature_c}°C")
                        else:
                            print(f"  {station}: No data available")
            print()


def example_export_to_dict():
    """Example: Export parsed data to dictionary format"""
    print("\n📦 Export to Dictionary Format")
    print("=" * 60)
    
    # Load optimized data
    with open("weather_data/optimized_example.json", "r") as f:
        data = json.load(f)
    
    upper_wind_list = data["weather_data"].get("Upper_Wind", [])
    
    if not upper_wind_list:
        print("❌ No upper wind data found")
        return
    
    # Convert to dictionary
    export_data = []
    
    for entry in upper_wind_list:
        upper_wind = UpperWind.from_bulletin(entry["bulletin"])
        
        for period in upper_wind.periods:
            period_data = {
                "valid_time": period.valid_time,
                "use_period": period.use_period,
                "stations": {}
            }
            
            for station, levels in period.stations.items():
                period_data["stations"][station] = [
                    {
                        "altitude_ft": level.altitude_ft,
                        "direction_deg": level.direction_deg,
                        "speed_kt": level.speed_kt,
                        "temperature_c": level.temperature_c
                    }
                    for level in levels
                ]
            
            export_data.append(period_data)
    
    # Save to JSON
    output_file = "weather_data/upper_winds_parsed.json"
    with open(output_file, "w") as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Exported {len(export_data)} period(s) to {output_file}")
    print(f"\nSample structure:")
    print(json.dumps(export_data[0] if export_data else {}, indent=2)[:500] + "...")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("🌬️  UPPER WIND PARSER EXAMPLES")
    print("="*60)
    
    example_parse_upper_winds()
    example_find_strong_winds()
    example_get_wind_at_altitude()
    example_export_to_dict()
    
    print("\n" + "="*60)
    print("✅ All examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
