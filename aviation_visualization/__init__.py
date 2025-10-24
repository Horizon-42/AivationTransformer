"""
Aviation Weather Visualization Package
====================================

Interactive map visualization for Canadian aviation weather data.

This package provides tools for creating interactive maps showing:
- Weather stations with current conditions
- Flight routes between airports  
- Real-time METAR and TAF data
- Flight category classifications (VFR/IFR/etc)

Main Classes:
- AviationWeatherMap: Core mapping functionality
- MapGenerator: High-level map creation utilities

Example Usage:
    from aviation_visualization import AviationWeatherMap
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
    
    repo = SQLiteWeatherRepository("weather.db")
    weather_map = AviationWeatherMap(repo)
    weather_map.create_base_map()
    weather_map.add_weather_stations()
    weather_map.save_map("my_map.html")
"""

__version__ = "1.0.0"
__author__ = "Aviation Transformer Project"

# Import main classes for easy access
from .weather_map import AviationWeatherMap
from .map_generator import MapGenerator
from .interactive_route_builder import InteractiveRouteBuilder
from .streamlit_app import AdvancedAviationApp

__all__ = [
    "AviationWeatherMap",
    "MapGenerator",
    "InteractiveRouteBuilder",
    "AdvancedAviationApp"
]