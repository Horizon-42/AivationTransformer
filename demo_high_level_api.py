#!/usr/bin/env python3
"""
Demo Script: SQLiteWeatherRepository High-Level API
===================================================

This demo script showcases the new high-level API methods added to SQLiteWeatherRepository:
1. query_weather_data() - Query by station IDs and time range
2. query_weather_by_region() - Query by geographic bounding box

The script demonstrates practical aviation weather use cases with real-world scenarios.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

def print_section_header(title: str, emoji: str = "🌤️"):
    """Print a formatted section header."""
    print(f"\n{emoji} {title}")
    print("=" * (len(title) + 4))

def print_subsection(title: str, emoji: str = "📍"):
    """Print a formatted subsection header."""
    print(f"\n{emoji} {title}")
    print("-" * (len(title) + 4))

def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M UTC")

def demo_query_weather_data():
    """Demonstrate the query_weather_data() method with various scenarios."""
    
    print_section_header("Query Weather Data by Station IDs", "🛩️")
    
    # Initialize repository
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    
    # Scenario 1: Major Canadian airports - current conditions
    print_subsection("Scenario 1: Current Conditions at Major Canadian Airports")
    
    major_airports = {
        "CYYZ": "Toronto Pearson",
        "CYVR": "Vancouver International", 
        "CYUL": "Montreal Trudeau",
        "CYYC": "Calgary International",
        "CYWG": "Winnipeg Richardson"
    }
    
    # Get data from the last 3 hours
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(hours=3)
    
    print(f"Querying: {', '.join(major_airports.keys())}")
    print(f"Time range: {format_datetime(recent_time)} to {format_datetime(now)}")
    
    try:
        weather_data = repo.query_weather_data(
            station_ids=list(major_airports.keys()),
            start_time=recent_time,
            end_time=now,
            limit=3
        )
        
        print(f"\n📊 Results: Found data for {len([k for k in weather_data.keys() if k != '_sigmets'])} stations")
        
        for station_id, data in weather_data.items():
            if station_id == '_sigmets':
                sigmets = data.get('sigmets', [])
                if sigmets:
                    print(f"\n⚠️  Active SIGMETs: {len(sigmets)} advisories")
                continue
            
            airport_name = major_airports.get(station_id, station_id)
            metars = data.get('metars', [])
            tafs = data.get('tafs', [])
            
            print(f"\n✈️  {station_id} ({airport_name})")
            print(f"    📋 METARs: {len(metars)} observations")
            print(f"    📈 TAFs: {len(tafs)} forecasts")
            
            # Show latest METAR details if available
            if metars:
                latest = metars[0]
                print(f"    🌡️  Latest: {format_datetime(latest.observation_time)}")
                print(f"         Temperature: {latest.temperature_celsius}°C")
                print(f"         Wind: {latest.wind_direction_degrees}°/{latest.wind_speed_knots}kt")
                print(f"         Visibility: {latest.visibility}")
                print(f"         Sky: {latest.sky_coverage}")
                
                # Show weather phenomena if any
                if latest.present_weather:
                    print(f"         Weather: {', '.join(latest.present_weather)}")
            
            # Show active TAF if available
            if tafs:
                latest_taf = tafs[0]
                valid_period = f"{format_datetime(latest_taf.valid_from)} to {format_datetime(latest_taf.valid_to)}"
                print(f"    📅 Current TAF: Valid {valid_period}")
                if latest_taf.forecast_periods:
                    print(f"         Forecast periods: {len(latest_taf.forecast_periods)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Scenario 2: Historical analysis
    print_subsection("Scenario 2: Historical Weather Analysis - Last 24 Hours", "📈")
    
    # Get 24 hours of data for Toronto
    past_24h = now - timedelta(hours=24)
    
    try:
        historical_data = repo.query_weather_data(
            station_ids=["CYYZ"],
            start_time=past_24h,
            end_time=now,
            limit=50  # More data for analysis
        )
        
        toronto_data = historical_data.get("CYYZ", {})
        metars = toronto_data.get('metars', [])
        
        if metars:
            print(f"📊 Retrieved {len(metars)} METAR observations for CYYZ")
            
            # Calculate temperature trends
            temperatures = [m.temperature_celsius for m in metars]
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            avg_temp = sum(temperatures) / len(temperatures)
            
            print(f"🌡️  Temperature Analysis:")
            print(f"    Minimum: {min_temp}°C")
            print(f"    Maximum: {max_temp}°C") 
            print(f"    Average: {avg_temp:.1f}°C")
            print(f"    Range: {max_temp - min_temp}°C")
            
            # Wind analysis
            wind_speeds = [m.wind_speed_knots for m in metars if m.wind_speed_knots is not None]
            if wind_speeds:
                avg_wind = sum(wind_speeds) / len(wind_speeds)
                max_wind = max(wind_speeds)
                print(f"💨 Wind Analysis:")
                print(f"    Average wind speed: {avg_wind:.1f}kt")
                print(f"    Maximum wind speed: {max_wind}kt")
        else:
            print("📊 No historical METAR data found for the specified period")
            
    except Exception as e:
        print(f"❌ Error in historical analysis: {e}")
    
    repo.close()

def demo_query_by_region():
    """Demonstrate the query_weather_by_region() method."""
    
    print_section_header("Query Weather Data by Geographic Region", "🗺️")
    
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(hours=6)
    
    # Scenario 1: Greater Toronto Area
    print_subsection("Scenario 1: Greater Toronto Area Weather Survey")
    
    # Define bounding box around Toronto
    # Toronto coordinates: ~43.6532°N, 79.3832°W
    toronto_box = {
        'min_latitude': 43.0,   # ~72km south
        'max_latitude': 44.3,   # ~72km north  
        'min_longitude': -80.0, # ~70km west
        'max_longitude': -78.7, # ~70km east
    }
    
    print(f"📍 Bounding box: {toronto_box['min_latitude']}°N to {toronto_box['max_latitude']}°N, "
          f"{toronto_box['min_longitude']}°W to {toronto_box['max_longitude']}°W")
    print(f"⏰ Time range: Last 6 hours")
    
    try:
        toronto_weather = repo.query_weather_by_region(
            **toronto_box,
            start_time=recent_time,
            end_time=now,
            limit=5
        )
        
        if toronto_weather is None:
            print("📊 No stations found in the Toronto region")
        else:
            stations_found = [sid for sid in toronto_weather.keys() if sid != '_sigmets']
            print(f"📊 Found {len(stations_found)} stations in the Toronto area")
            
            # Analyze regional weather patterns
            all_temperatures = []
            all_wind_speeds = []
            station_details = []
            
            for station_id, data in toronto_weather.items():
                if station_id == '_sigmets':
                    continue
                
                metars = data.get('metars', [])
                tafs = data.get('tafs', [])
                
                if metars:
                    latest_metar = metars[0]
                    all_temperatures.append(latest_metar.temperature_celsius)
                    if latest_metar.wind_speed_knots is not None:
                        all_wind_speeds.append(latest_metar.wind_speed_knots)
                    
                    station_details.append({
                        'id': station_id,
                        'temp': latest_metar.temperature_celsius,
                        'wind': latest_metar.wind_speed_knots or 0,
                        'visibility': latest_metar.visibility,
                        'sky': latest_metar.sky_coverage,
                        'metar_count': len(metars),
                        'taf_count': len(tafs)
                    })
            
            # Regional weather summary
            if all_temperatures:
                avg_temp = sum(all_temperatures) / len(all_temperatures)
                temp_range = max(all_temperatures) - min(all_temperatures)
                print(f"\n🌡️  Regional Temperature Summary:")
                print(f"    Average: {avg_temp:.1f}°C")
                print(f"    Range: {temp_range:.1f}°C (from {min(all_temperatures)}°C to {max(all_temperatures)}°C)")
            
            if all_wind_speeds:
                avg_wind = sum(all_wind_speeds) / len(all_wind_speeds)
                print(f"💨 Regional Wind Summary:")
                print(f"    Average wind speed: {avg_wind:.1f}kt")
            
            # Individual station details
            print(f"\n🏢 Individual Station Details:")
            for station in sorted(station_details, key=lambda x: x['id']):
                print(f"    {station['id']}: {station['temp']}°C, {station['wind']}kt, "
                      f"{station['visibility']}, {station['sky']} ({station['metar_count']} METARs)")
    
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Scenario 2: Coast-to-coast comparison
    print_subsection("Scenario 2: Coast-to-Coast Weather Comparison", "🌊")
    
    # Vancouver area
    vancouver_box = {
        'min_latitude': 49.0,
        'max_latitude': 49.5,
        'min_longitude': -123.5,
        'max_longitude': -122.5
    }
    
    # Halifax area  
    halifax_box = {
        'min_latitude': 44.5,
        'max_latitude': 45.0,
        'min_longitude': -64.0,
        'max_longitude': -63.0
    }
    
    regions = [
        ("Vancouver Area", vancouver_box),
        ("Halifax Area", halifax_box)
    ]
    
    for region_name, box in regions:
        try:
            regional_data = repo.query_weather_by_region(
                **box,
                start_time=recent_time,
                limit=3
            )
            
            if regional_data:
                stations = [sid for sid in regional_data.keys() if sid != '_sigmets']
                print(f"\n🏙️  {region_name}: {len(stations)} stations")
                
                # Get average temperature for the region
                temps = []
                for station_id, data in regional_data.items():
                    if station_id != '_sigmets' and data.get('metars'):
                        temps.append(data['metars'][0].temperature_celsius)
                
                if temps:
                    avg_temp = sum(temps) / len(temps)
                    print(f"     Average temperature: {avg_temp:.1f}°C")
                    print(f"     Stations: {', '.join(stations[:3])}{'...' if len(stations) > 3 else ''}")
            else:
                print(f"\n🏙️  {region_name}: No stations found")
                
        except Exception as e:
            print(f"❌ Error querying {region_name}: {e}")
    
    repo.close()

def demo_error_handling():
    """Demonstrate error handling and validation."""
    
    print_section_header("Error Handling and Validation", "⚠️")
    
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    
    # Test invalid bounding boxes
    invalid_boxes = [
        {
            'name': 'Inverted latitude bounds',
            'params': {'min_latitude': 45.0, 'max_latitude': 44.0, 'min_longitude': -80.0, 'max_longitude': -79.0}
        },
        {
            'name': 'Latitude out of range',
            'params': {'min_latitude': -100.0, 'max_latitude': 100.0, 'min_longitude': -80.0, 'max_longitude': -79.0}
        },
        {
            'name': 'Longitude out of range',
            'params': {'min_latitude': 43.0, 'max_latitude': 44.0, 'min_longitude': -200.0, 'max_longitude': 200.0}
        }
    ]
    
    for test_case in invalid_boxes:
        print(f"\n🧪 Testing: {test_case['name']}")
        try:
            result = repo.query_weather_by_region(**test_case['params'])
            print(f"❌ Unexpected success: {result is not None}")
        except ValueError as e:
            print(f"✅ Correctly caught validation error: {e}")
        except Exception as e:
            print(f"❓ Unexpected error type: {type(e).__name__}: {e}")
    
    repo.close()

def demo_practical_applications():
    """Show practical applications and use cases."""
    
    print_section_header("Practical Applications", "🛠️")
    
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    now = datetime.now(timezone.utc)
    
    # Application 1: Flight planning weather briefing
    print_subsection("Application 1: Flight Planning Weather Briefing", "✈️")
    
    flight_route = ["CYYZ", "CYOW", "CYUL"]  # Toronto -> Ottawa -> Montreal
    route_names = ["Toronto Pearson", "Ottawa MacDonald-Cartier", "Montreal Trudeau"]
    
    print("📋 Flight Route Weather Briefing")
    print(f"Route: {' → '.join([f'{code} ({name})' for code, name in zip(flight_route, route_names)])}")
    
    try:
        route_weather = repo.query_weather_data(
            station_ids=flight_route,
            start_time=now - timedelta(hours=1),
            limit=2
        )
        
        print(f"\n🌤️  Current Conditions Along Route:")
        for i, (station_id, airport_name) in enumerate(zip(flight_route, route_names)):
            data = route_weather.get(station_id, {})
            metars = data.get('metars', [])
            tafs = data.get('tafs', [])
            
            if metars:
                metar = metars[0]
                # Simple flight category determination
                vis_km = metar.visibility_meters / 1000 if metar.visibility_meters else 0
                if vis_km >= 8 and 'CLR' in metar.sky_coverage:
                    category = "VFR 🟢"
                elif vis_km >= 5:
                    category = "MVFR 🟡"
                elif vis_km >= 1.6:
                    category = "IFR 🔴"
                else:
                    category = "LIFR 🔴"
                
                print(f"   {i+1}. {station_id} ({airport_name}) - {category}")
                print(f"      Conditions: {metar.temperature_celsius}°C, {metar.wind_direction_degrees}°/{metar.wind_speed_knots}kt")
                print(f"      Visibility: {metar.visibility}, Sky: {metar.sky_coverage}")
                
                if tafs:
                    taf = tafs[0]
                    print(f"      Forecast: Valid until {format_datetime(taf.valid_to)}")
            else:
                print(f"   {i+1}. {station_id} ({airport_name}) - No current data")
    
    except Exception as e:
        print(f"❌ Error in flight briefing: {e}")
    
    # Application 2: Weather monitoring for a region
    print_subsection("Application 2: Regional Weather Monitoring System", "🌡️")
    
    # Monitor weather around major population centers
    monitoring_regions = [
        ("Southern Ontario", {'min_latitude': 42.0, 'max_latitude': 45.0, 'min_longitude': -83.0, 'max_longitude': -74.0}),
        ("Lower Mainland BC", {'min_latitude': 49.0, 'max_latitude': 49.6, 'min_longitude': -123.5, 'max_longitude': -122.0})
    ]
    
    print("🔍 Regional Weather Monitoring Dashboard")
    
    for region_name, bounds in monitoring_regions:
        try:
            regional_data = repo.query_weather_by_region(
                **bounds,
                start_time=now - timedelta(hours=2),
                limit=1
            )
            
            if regional_data:
                stations = [sid for sid in regional_data.keys() if sid != '_sigmets']
                
                # Collect current conditions
                temps, winds, conditions = [], [], []
                for station_id, data in regional_data.items():
                    if station_id != '_sigmets' and data.get('metars'):
                        metar = data['metars'][0]
                        temps.append(metar.temperature_celsius)
                        if metar.wind_speed_knots:
                            winds.append(metar.wind_speed_knots)
                        conditions.append(metar.sky_coverage)
                
                print(f"\n🏞️  {region_name} ({len(stations)} stations active)")
                if temps:
                    print(f"     Temperature: {min(temps)}°C to {max(temps)}°C (avg: {sum(temps)/len(temps):.1f}°C)")
                if winds:
                    print(f"     Wind speeds: {max(winds)}kt max (avg: {sum(winds)/len(winds):.1f}kt)")
                
                # Count sky conditions
                sky_counts = {}
                for condition in conditions:
                    sky_counts[condition] = sky_counts.get(condition, 0) + 1
                
                if sky_counts:
                    dominant_sky = max(sky_counts.items(), key=lambda x: x[1])
                    print(f"     Sky conditions: {dominant_sky[0]} (most common)")
            else:
                print(f"\n🏞️  {region_name}: No stations currently reporting")
                
        except Exception as e:
            print(f"❌ Error monitoring {region_name}: {e}")
    
    repo.close()

def main():
    """Main demo function."""
    
    print("🌤️" * 20)
    print("SQLiteWeatherRepository High-Level API Demo")
    print("🌤️" * 20)
    print("\nThis demo showcases the powerful new high-level API methods for querying aviation weather data.")
    print("The API provides unified access to METARs, TAFs, Upper Winds, and SIGMETs with geographic and temporal filtering.")
    
    try:
        # Run all demo sections
        demo_query_weather_data()
        demo_query_by_region()
        demo_error_handling()
        demo_practical_applications()
        
        print_section_header("Demo Completed Successfully! ", "🎉")
        print("\n📚 For more information, see:")
        print("   • docs/high_level_api.md - Complete API documentation")
        print("   • METAR_convert/storage/sqlite_repository.py - Source code")
        print("\n✨ The new high-level API makes aviation weather data analysis much more accessible!")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Demo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()