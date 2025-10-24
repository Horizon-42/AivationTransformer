#!/usr/bin/env python3
"""
Simple Aviation Weather Map Demo
===============================

Quick demo script to generate aviation weather maps with different configurations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from aviation_weather_visualization import AviationWeatherMap, create_canada_aviation_map
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

def demo_simple_map():
    """Create a simple map with just weather stations."""
    print("🗺️ Creating Simple Weather Station Map...")
    
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    weather_map = AviationWeatherMap(repo)
    
    # Create base map centered on Toronto
    weather_map.create_base_map(center=[43.6532, -79.3832], zoom=6)
    
    # Add weather stations around Toronto/Ontario
    ontario_stations = ["CYYZ", "CYTZ", "CYHM", "CYKZ", "CYOO", "CYQG", "CYXU", "CYKF"]
    weather_map.add_weather_stations(time_hours=3, station_ids=ontario_stations)
    
    # Add legend
    weather_map.add_legend()
    
    # Save map
    filepath = weather_map.save_map("ontario_weather_map.html")
    repo.close()
    
    print(f"✅ Simple map created: {filepath}")
    return filepath

def demo_flight_route_map():
    """Create a map focused on a specific flight route."""
    print("✈️ Creating Flight Route Weather Map...")
    
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    weather_map = AviationWeatherMap(repo)
    
    # Create base map
    weather_map.create_base_map(center=[45.5, -75.0], zoom=5)
    
    # Define a flight route: Toronto -> Ottawa -> Montreal -> Quebec City
    flight_route = ["CYYZ", "CYOW", "CYUL", "CYQB"]
    
    # Add weather stations for these airports
    weather_map.add_weather_stations(time_hours=6, station_ids=flight_route)
    
    # Add the flight route
    weather_map.add_flight_route(flight_route, "Eastern Canada Route", "#dc2626", 4)
    
    # Add legend
    weather_map.add_legend()
    
    # Save map
    filepath = weather_map.save_map("eastern_flight_route_map.html")
    repo.close()
    
    print(f"✅ Flight route map created: {filepath}")
    return filepath

def demo_regional_comparison():
    """Create a map comparing different regions."""
    print("🌎 Creating Regional Comparison Map...")
    
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    weather_map = AviationWeatherMap(repo)
    
    # Create base map of Canada
    weather_map.create_base_map(zoom=4)
    
    # Define regions with representative airports
    regions = {
        "Atlantic": ["CYHZ", "CYSJ", "CYQX", "CYYT"],
        "Central": ["CYYZ", "CYUL", "CYOW", "CYQB"],  
        "Prairie": ["CYWG", "CYQR", "CYXE", "CYEG"],
        "West Coast": ["CYVR", "CYYJ", "CYCD", "CYQQ"]
    }
    
    # Add all stations
    all_stations = []
    for region_stations in regions.values():
        all_stations.extend(region_stations)
    
    weather_map.add_weather_stations(time_hours=6, station_ids=all_stations)
    
    # Add regional routes
    colors = ["#dc2626", "#2563eb", "#16a34a", "#ca8a04"]
    for i, (region_name, stations) in enumerate(regions.items()):
        if len(stations) >= 2:
            weather_map.add_flight_route(stations, f"{region_name} Circuit", colors[i], 3)
    
    # Add legend
    weather_map.add_legend()
    
    # Save map
    filepath = weather_map.save_map("regional_comparison_map.html")
    repo.close()
    
    print(f"✅ Regional comparison map created: {filepath}")
    return filepath

def main():
    """Run all demo map types."""
    print("🌤️ Aviation Weather Map Demos")
    print("="*40)
    
    try:
        # Create different map types
        maps_created = []
        
        print("\n1️⃣ Creating maps...")
        maps_created.append(demo_simple_map())
        maps_created.append(demo_flight_route_map())
        maps_created.append(demo_regional_comparison())
        
        # Also create the full Canada map
        print("\n🇨🇦 Creating Full Canada Map...")
        full_map = create_canada_aviation_map(demo=True)
        maps_created.append(full_map)
        
        print(f"\n🎉 Demo Complete! Created {len(maps_created)} interactive maps:")
        for i, map_path in enumerate(maps_created, 1):
            print(f"   {i}. {Path(map_path).name}")
        
        print(f"\n📂 Open any of these HTML files in your web browser to explore the maps!")
        print(f"🌐 The maps are interactive - you can zoom, pan, and click on stations for details.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()