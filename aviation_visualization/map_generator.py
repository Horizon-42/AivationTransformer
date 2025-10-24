#!/usr/bin/env python3
"""
Map Generator Module
==================

High-level utilities for generating different types of aviation weather maps.
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from .weather_map import AviationWeatherMap


class MapGenerator:
    """High-level map generation utilities."""
    
    def __init__(self, repository):
        """
        Initialize the map generator.
        
        Args:
            repository: SQLiteWeatherRepository instance
        """
        self.repo = repository
        
        # Predefined airport groups
        self.airport_groups = {
            'major_canadian': {
                'stations': ['CYYZ', 'CYVR', 'CYUL', 'CYYC', 'CYWG', 'CYOW', 'CYHZ'],
                'center': [56.1304, -106.3468],
                'zoom': 3
            },
            'ontario': {
                'stations': ['CYYZ', 'CYTZ', 'CYHM', 'CYKZ', 'CYOO', 'CYQG', 'CYXU', 'CYKF'],
                'center': [43.6532, -79.3832],
                'zoom': 6
            },
            'atlantic': {
                'stations': ['CYHZ', 'CYSJ', 'CYQX', 'CYYT', 'CYAW', 'CYZV'],
                'center': [45.0, -64.0],
                'zoom': 5
            },
            'prairie': {
                'stations': ['CYWG', 'CYQR', 'CYXE', 'CYEG', 'CYQF', 'CYQT'],
                'center': [52.0, -106.0],
                'zoom': 5
            },
            'west_coast': {
                'stations': ['CYVR', 'CYYJ', 'CYCD', 'CYQQ', 'CYBL'],
                'center': [49.2, -123.1],
                'zoom': 6
            }
        }
        
        # Predefined routes
        self.flight_routes = {
            'transcontinental': {
                'stations': ['CYVR', 'CYYC', 'CYWG', 'CYYZ', 'CYUL'],
                'name': 'Transcontinental Route',
                'color': '#dc2626'
            },
            'eastern_corridor': {
                'stations': ['CYYZ', 'CYOW', 'CYUL', 'CYQB', 'CYHZ'],
                'name': 'Eastern Corridor',
                'color': '#2563eb'
            },
            'prairie_circuit': {
                'stations': ['CYWG', 'CYQR', 'CYXE', 'CYEG', 'CYYC'],
                'name': 'Prairie Circuit',
                'color': '#16a34a'
            },
            'atlantic_tour': {
                'stations': ['CYHZ', 'CYSJ', 'CYQX', 'CYYT'],
                'name': 'Atlantic Tour',
                'color': '#ca8a04'
            }
        }

    def create_regional_map(self, region: str, time_hours: int = 6, 
                          include_routes: bool = True) -> AviationWeatherMap:
        """
        Create a regional weather map.
        
        Args:
            region: Region name ('ontario', 'atlantic', 'prairie', 'west_coast', 'major_canadian')
            time_hours: Hours of historical weather data to include
            include_routes: Whether to add flight routes
            
        Returns:
            Configured AviationWeatherMap instance
        """
        if region not in self.airport_groups:
            raise ValueError(f"Unknown region '{region}'. Available: {list(self.airport_groups.keys())}")
        
        region_config = self.airport_groups[region]
        
        # Create map
        weather_map = AviationWeatherMap(self.repo)
        weather_map.create_base_map(
            center=region_config['center'],
            zoom=region_config['zoom']
        )
        
        # Add weather stations
        weather_map.add_weather_stations(
            time_hours=time_hours,
            station_ids=region_config['stations']
        )
        
        # Add relevant flight routes
        if include_routes:
            if region == 'major_canadian':
                # Add multiple routes for full Canada view
                for route_key in ['transcontinental', 'eastern_corridor', 'prairie_circuit']:
                    route = self.flight_routes[route_key]
                    weather_map.add_flight_route(
                        route['stations'], 
                        route['name'], 
                        route['color'], 
                        4
                    )
            elif region == 'ontario':
                # Ontario route
                ontario_route = ['CYYZ', 'CYTZ', 'CYHM', 'CYKZ']
                weather_map.add_flight_route(ontario_route, 'Ontario Circuit', '#8b5cf6', 3)
            elif region == 'atlantic':
                route = self.flight_routes['atlantic_tour']
                weather_map.add_flight_route(route['stations'], route['name'], route['color'], 3)
            elif region == 'prairie':
                route = self.flight_routes['prairie_circuit']
                weather_map.add_flight_route(route['stations'], route['name'], route['color'], 3)
        
        # Add legend
        weather_map.add_legend()
        
        return weather_map

    def create_route_map(self, route_key: str, time_hours: int = 6) -> AviationWeatherMap:
        """
        Create a map focused on a specific flight route.
        
        Args:
            route_key: Route identifier ('transcontinental', 'eastern_corridor', etc.)
            time_hours: Hours of historical weather data to include
            
        Returns:
            Configured AviationWeatherMap instance
        """
        if route_key not in self.flight_routes:
            raise ValueError(f"Unknown route '{route_key}'. Available: {list(self.flight_routes.keys())}")
        
        route = self.flight_routes[route_key]
        
        # Create map centered on route
        weather_map = AviationWeatherMap(self.repo)
        weather_map.create_base_map(zoom=4)  # Auto-center on Canada
        
        # Add weather stations for route
        weather_map.add_weather_stations(
            time_hours=time_hours,
            station_ids=route['stations']
        )
        
        # Add the flight route
        weather_map.add_flight_route(
            route['stations'],
            route['name'],
            route['color'],
            4
        )
        
        # Add legend
        weather_map.add_legend()
        
        return weather_map

    def create_custom_map(self, stations: List[str], routes: Optional[List[Dict]] = None,
                         center: Optional[Tuple[float, float]] = None, 
                         zoom: int = 4, time_hours: int = 6) -> AviationWeatherMap:
        """
        Create a custom map with specified stations and routes.
        
        Args:
            stations: List of station IDs to include
            routes: List of route dictionaries with 'stations', 'name', 'color' keys
            center: Map center coordinates (lat, lon)
            zoom: Initial zoom level
            time_hours: Hours of historical weather data
            
        Returns:
            Configured AviationWeatherMap instance
        """
        # Create map
        weather_map = AviationWeatherMap(self.repo)
        weather_map.create_base_map(center=center, zoom=zoom)
        
        # Add weather stations
        weather_map.add_weather_stations(
            time_hours=time_hours,
            station_ids=stations
        )
        
        # Add custom routes
        if routes:
            for route in routes:
                weather_map.add_flight_route(
                    route.get('stations', []),
                    route.get('name', 'Custom Route'),
                    route.get('color', '#6b7280'),
                    route.get('weight', 3)
                )
        
        # Add legend
        weather_map.add_legend()
        
        return weather_map

    def generate_all_demo_maps(self, output_dir: str = ".") -> List[str]:
        """
        Generate all demo maps and save them.
        
        Args:
            output_dir: Directory to save maps in
            
        Returns:
            List of generated file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        generated_files = []
        
        print("🗺️ Generating aviation weather maps...")
        
        # 1. Ontario regional map
        print("📍 Creating Ontario regional map...")
        ontario_map = self.create_regional_map('ontario')
        ontario_file = output_path / "ontario_weather_map.html"
        ontario_map.save_map(str(ontario_file))
        generated_files.append(str(ontario_file))
        
        # 2. Eastern corridor route map
        print("✈️ Creating Eastern corridor route map...")
        eastern_map = self.create_route_map('eastern_corridor')
        eastern_file = output_path / "eastern_flight_route_map.html"
        eastern_map.save_map(str(eastern_file))
        generated_files.append(str(eastern_file))
        
        # 3. Regional comparison map
        print("🌎 Creating regional comparison map...")
        comparison_map = self.create_regional_map('major_canadian')
        comparison_file = output_path / "regional_comparison_map.html"
        comparison_map.save_map(str(comparison_file))
        generated_files.append(str(comparison_file))
        
        # 4. Full Canada map with all routes
        print("🇨🇦 Creating full Canada map...")
        canada_map = self.create_regional_map('major_canadian', include_routes=True)
        # Add additional routes for comprehensive view
        for route_key in ['atlantic_tour']:
            if route_key in self.flight_routes:
                route = self.flight_routes[route_key]
                canada_map.add_flight_route(route['stations'], route['name'], route['color'], 3)
        
        canada_file = output_path / "canadian_aviation_weather_map.html"
        canada_map.save_map(str(canada_file))
        generated_files.append(str(canada_file))
        
        print(f"🎉 Generated {len(generated_files)} maps in {output_path}")
        return generated_files

    def get_available_regions(self) -> List[str]:
        """Get list of available predefined regions."""
        return list(self.airport_groups.keys())

    def get_available_routes(self) -> List[str]:
        """Get list of available predefined routes."""
        return list(self.flight_routes.keys())

    def get_region_stations(self, region: str) -> List[str]:
        """Get stations for a specific region."""
        if region not in self.airport_groups:
            raise ValueError(f"Unknown region '{region}'")
        return self.airport_groups[region]['stations']

    def get_route_stations(self, route_key: str) -> List[str]:
        """Get stations for a specific route."""
        if route_key not in self.flight_routes:
            raise ValueError(f"Unknown route '{route_key}'")
        return self.flight_routes[route_key]['stations']