#!/usr/bin/env python3
"""
Aviation Weather Visualization Demo
==================================

Demonstrates the aviation_visualization package capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aviation_visualization import AviationWeatherMap, MapGenerator
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

def demo_package_usage():
    """Demonstrate the organized aviation visualization package."""
    
    print("🌤️ Aviation Weather Visualization Package Demo")
    print("=" * 50)
    
    # Initialize repository
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    
    # Create map generator
    generator = MapGenerator(repo)
    
    print("\n📋 Available Features:")
    print(f"   Regions: {', '.join(generator.get_available_regions())}")
    print(f"   Routes: {', '.join(generator.get_available_routes())}")
    
    # Example 1: Quick regional map
    print("\n🗺️ Creating Ontario regional map...")
    ontario_map = generator.create_regional_map('ontario', time_hours=6)
    ontario_path = ontario_map.save_map("demo_ontario_map.html")
    
    # Example 2: Route-focused map
    print("\n✈️ Creating transcontinental route map...")
    route_map = generator.create_route_map('transcontinental', time_hours=3)
    route_path = route_map.save_map("demo_transcontinental_route.html")
    
    # Example 3: Custom map
    print("\n🛠️ Creating custom Atlantic provinces map...")
    atlantic_stations = ['CYHZ', 'CYSJ', 'CYQX', 'CYYT', 'CYAW']
    custom_routes = [
        {
            'stations': ['CYHZ', 'CYSJ', 'CYQX'],
            'name': 'Maritime Circuit',
            'color': '#059669',
            'weight': 4
        }
    ]
    
    custom_map = generator.create_custom_map(
        stations=atlantic_stations,
        routes=custom_routes,
        center=[45.0, -64.0],
        zoom=6
    )
    custom_path = custom_map.save_map("demo_custom_maritime.html")
    
    # Example 4: Generate all demo maps
    print("\n🎯 Generating complete set of demo maps...")
    all_maps = generator.generate_all_demo_maps("maps")
    
    # Clean up
    repo.close()
    
    print(f"\n✅ Demo Complete! Generated maps:")
    print(f"   🗺️ Ontario: {Path(ontario_path).name}")
    print(f"   ✈️ Route: {Path(route_path).name}")
    print(f"   🛠️ Custom: {Path(custom_path).name}")
    print(f"   📁 Full set: {len(all_maps)} maps in 'maps/' directory")
    
    print(f"\n🌐 Open any HTML file in your browser to view the interactive maps!")

def demo_low_level_api():
    """Demonstrate direct usage of AviationWeatherMap class."""
    
    print("\n🔧 Low-Level API Demo")
    print("-" * 30)
    
    # Initialize repository
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    
    # Create map directly
    weather_map = AviationWeatherMap(repo)
    
    # Build map step by step
    print("🗺️ Creating base map...")
    weather_map.create_base_map(center=[49.2, -123.1], zoom=7)  # Vancouver area
    
    print("📍 Adding Vancouver area airports...")
    vancouver_airports = ['CYVR', 'CYCD', 'CYQQ', 'CYBL']
    weather_map.add_weather_stations(time_hours=4, station_ids=vancouver_airports)
    
    print("✈️ Adding Vancouver island circuit...")
    weather_map.add_flight_route(
        ['CYVR', 'CYCD', 'CYQQ'], 
        'Vancouver Island Circuit',
        '#dc2626',
        5
    )
    
    print("📊 Adding legend...")
    weather_map.add_legend()
    
    print("💾 Saving map...")
    map_path = weather_map.save_map("demo_vancouver_detailed.html")
    
    repo.close()
    
    print(f"✅ Detailed Vancouver map: {Path(map_path).name}")

if __name__ == "__main__":
    demo_package_usage()
    demo_low_level_api()
    
    print(f"\n🎉 All demos complete!")
    print(f"📂 Check the generated HTML files and open them in your browser.")