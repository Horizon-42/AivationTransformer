#!/usr/bin/env python3
"""
Simple Example: Using the Aviation Visualization Package
=======================================================

This shows how to use the aviation_visualization package from your main project.
"""

from aviation_visualization import AviationWeatherMap, MapGenerator
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

def simple_example():
    """Simple example of creating a weather map."""
    
    print("🗺️ Simple Aviation Weather Map Example")
    print("=" * 40)
    
    # 1. Initialize your weather repository
    print("📊 Connecting to weather database...")
    repo = SQLiteWeatherRepository("weather_data/weather.db")
    
    # 2. Create map generator
    print("🏗️ Creating map generator...")
    generator = MapGenerator(repo)
    
    # 3. Generate a regional map (super easy!)
    print("🗺️ Generating Ontario regional map...")
    ontario_map = generator.create_regional_map('ontario', time_hours=6)
    
    # 4. Save the map
    print("💾 Saving map...")
    map_file = ontario_map.save_map("simple_ontario_map.html")
    
    # 5. Clean up
    repo.close()
    
    print(f"✅ Done! Open {map_file} in your browser.")
    print(f"🎯 The map shows weather stations around Toronto with current conditions.")
    print(f"📁 Maps are saved in aviation_visualization/maps/ directory.")
    
def custom_flight_route_example():
    """Example of creating a custom flight route map."""
    
    print("\n✈️ Custom Flight Route Example")
    print("=" * 35)
    
    # Initialize
    repo = SQLiteWeatherRepository("weather_data/weather.db") 
    generator = MapGenerator(repo)
    
    # Define your own flight route
    my_route = ["CYVR", "CYEG", "CYWG", "CYYZ"]  # Vancouver to Toronto
    
    print(f"📍 Planning route: {' → '.join(my_route)}")
    
    # Create custom map
    custom_map = generator.create_custom_map(
        stations=my_route,
        routes=[{
            'stations': my_route,
            'name': 'My Cross-Country Flight',
            'color': '#ff6b6b',  # Red color
            'weight': 4
        }],
        zoom=3  # Show all of Canada
    )
    
    # Save map
    map_file = custom_map.save_map("my_flight_route.html")
    repo.close()
    
    print(f"✅ Flight route map saved: {map_file}")
    print(f"🌤️ Shows weather conditions along your planned route.")
    print(f"📁 All maps are organized in aviation_visualization/maps/")

if __name__ == "__main__":
    simple_example()
    custom_flight_route_example()
    
    print(f"\n🎉 Examples complete!")
    print(f"📂 Open the HTML files in your browser to see the interactive maps.")
    print(f"🔍 Click on any airport marker to see detailed weather information.")