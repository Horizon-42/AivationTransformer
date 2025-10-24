#!/usr/bin/env python3
"""
Simple Interactive Route Builder Example
=======================================

Shows how to use the InteractiveRouteBuilder from the aviation_visualization package.
"""

from aviation_visualization import InteractiveRouteBuilder
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

def create_interactive_route_builder():
    """Create and save an interactive route builder map."""
    
    print("🛩️ Interactive Route Builder Example")
    print("=" * 38)
    
    # 1. Connect to weather database
    print("📊 Connecting to weather database...")
    repo = SQLiteWeatherRepository("weather_data/weather.db")
    
    # 2. Create interactive route builder
    print("🏗️ Creating interactive route builder...")
    builder = InteractiveRouteBuilder(repo)
    
    # 3. Generate interactive map
    print("🗺️ Generating interactive map...")
    map_file = builder.save_interactive_map("my_custom_route_builder.html")
    
    # 4. Clean up
    repo.close()
    
    print("✅ Interactive route builder created!")
    print(f"🌐 Open {map_file} in your browser")
    print()
    print("📖 How to use:")
    print("   • Click on any blue airplane marker (✈) to add stations to your route")
    print("   • Stations will be connected in the order you click them")
    print("   • Use the control panel on the right to manage your route")
    print("   • Remove individual stations with the ✕ button")
    print("   • Clear entire route with 'Clear Route' button")
    print("   • Export your route as JSON with 'Export Route' button")
    print()
    print("🎯 Perfect for flight planning and weather route analysis!")

if __name__ == "__main__":
    create_interactive_route_builder()