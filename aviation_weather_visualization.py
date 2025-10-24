#!/usr/bin/env python3
"""
Aviation Weather Visualization Module
====================================

This module provides visualization capabilities for Canadian aviation weather stations
and flight routes using Folium (Leaflet.js) for interactive maps.

Features:
- Plot weather stations with current conditions
- Draw flight routes between airports
- Color-coded markers based on weather conditions
- Interactive popups with detailed weather information
- Export maps as HTML files

Dependencies:
    pip install folium
"""

import folium
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
    from METAR_convert.metar import METAR
    from METAR_convert.taf import TAF
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure folium is installed: pip install folium")
    sys.exit(1)


class AviationWeatherMap:
    """Interactive map visualization for aviation weather data."""
    
    def __init__(self, repository: SQLiteWeatherRepository):
        """
        Initialize the weather map.
        
        Args:
            repository: SQLiteWeatherRepository instance for data access
        """
        self.repo = repository
        self.map = None
        
        # Canada center coordinates for initial map view
        self.canada_center = [56.1304, -106.3468]
        
        # Flight category colors (based on visibility and ceiling)
        self.flight_category_colors = {
            'VFR': '#22c55e',    # Green
            'MVFR': '#eab308',   # Yellow  
            'IFR': '#ef4444',    # Red
            'LIFR': '#7c2d12',   # Dark Red
            'UNKNOWN': '#6b7280' # Gray
        }
        
        # Weather station types
        self.station_types = {
            'major': {'radius': 8, 'weight': 3},
            'regional': {'radius': 6, 'weight': 2}, 
            'minor': {'radius': 4, 'weight': 1}
        }

    def create_base_map(self, center: Optional[Tuple[float, float]] = None, zoom: int = 4) -> folium.Map:
        """
        Create the base map centered on Canada.
        
        Args:
            center: (latitude, longitude) for map center
            zoom: Initial zoom level
            
        Returns:
            Folium map object
        """
        if center is None:
            center = self.canada_center
            
        self.map = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap',
            prefer_canvas=True
        )
        
        # Add different tile layers for aviation
        folium.TileLayer('cartodbpositron', name='Light Map').add_to(self.map)
        folium.TileLayer('cartodbdark_matter', name='Dark Map').add_to(self.map)
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        return self.map

    def determine_flight_category(self, metar: METAR) -> str:
        """
        Determine flight category based on visibility and ceiling.
        
        Args:
            metar: METAR observation
            
        Returns:
            Flight category string (VFR, MVFR, IFR, LIFR, UNKNOWN)
        """
        try:
            # Get visibility in kilometers
            vis_km = metar.visibility_meters / 1000 if metar.visibility_meters else 0
            
            # Get ceiling from cloud layers
            ceiling_ft = None
            for layer in metar.cloud_layers:
                if layer.coverage in ['BKN', 'OVC'] and layer.altitude_feet:
                    if ceiling_ft is None or layer.altitude_feet < ceiling_ft:
                        ceiling_ft = layer.altitude_feet
            
            # Determine category based on US FAA criteria
            if vis_km >= 8.0 and (ceiling_ft is None or ceiling_ft >= 3000):
                return 'VFR'
            elif vis_km >= 5.0 and (ceiling_ft is None or ceiling_ft >= 1000):
                return 'MVFR'  
            elif vis_km >= 1.6 and (ceiling_ft is None or ceiling_ft >= 500):
                return 'IFR'
            elif vis_km < 1.6 or (ceiling_ft is not None and ceiling_ft < 500):
                return 'LIFR'
            else:
                return 'UNKNOWN'
                
        except Exception:
            return 'UNKNOWN'

    def classify_station(self, station_id: str) -> str:
        """
        Classify station type based on airport code.
        
        Args:
            station_id: Station identifier
            
        Returns:
            Station classification (major, regional, minor)
        """
        major_airports = {
            'CYYZ', 'CYVR', 'CYUL', 'CYYC', 'CYWG', 'CYOW', 'CYHZ', 
            'CYQX', 'CYSJ', 'CYQB', 'CYXU', 'CYYJ', 'CYEG'
        }
        
        regional_airports = {
            'CYQF', 'CYQR', 'CYQT', 'CYXE', 'CYXS', 'CYOD', 'CYQL',
            'CYZF', 'CYZV', 'CYAV', 'CYBL', 'CYBG'
        }
        
        if station_id in major_airports:
            return 'major'
        elif station_id in regional_airports:
            return 'regional'
        else:
            return 'minor'

    def create_weather_popup(self, station_id: str, metar: Optional[METAR], taf: Optional[TAF]) -> str:
        """
        Create HTML popup content for weather station.
        
        Args:
            station_id: Station identifier
            metar: Latest METAR observation
            taf: Latest TAF forecast
            
        Returns:
            HTML string for popup
        """
        html = f"<div style='width: 300px;'>"
        html += f"<h3>🛩️ {station_id}</h3>"
        
        if metar:
            html += f"<h4>📋 Current Conditions</h4>"
            html += f"<b>Time:</b> {metar.observation_time.strftime('%Y-%m-%d %H:%M UTC')}<br>"
            html += f"<b>Temperature:</b> {metar.temperature_celsius}°C<br>"
            
            if metar.wind_direction_degrees and metar.wind_speed_knots:
                html += f"<b>Wind:</b> {metar.wind_direction_degrees}°/{metar.wind_speed_knots}kt"
                if metar.wind_gust_knots:
                    html += f"G{metar.wind_gust_knots}kt"
                html += "<br>"
            
            html += f"<b>Visibility:</b> {metar.visibility}<br>"
            html += f"<b>Sky:</b> {metar.sky_coverage}<br>"
            
            if metar.present_weather:
                html += f"<b>Weather:</b> {', '.join(metar.present_weather)}<br>"
            
            html += f"<b>Altimeter:</b> {metar.altimeter_hpa:.1f} hPa<br>"
            
            # Flight category
            category = self.determine_flight_category(metar)
            color = self.flight_category_colors.get(category, '#6b7280')
            html += f"<b>Category:</b> <span style='color: {color}; font-weight: bold;'>{category}</span><br>"
        
        if taf:
            html += f"<h4>📈 Forecast (TAF)</h4>"
            html += f"<b>Valid:</b> {taf.valid_from.strftime('%m/%d %H:%M')} - {taf.valid_to.strftime('%m/%d %H:%M')} UTC<br>"
            html += f"<b>Periods:</b> {len(taf.forecast_periods)} forecast changes<br>"
        
        if not metar and not taf:
            html += "<p><i>No recent weather data available</i></p>"
        
        html += "</div>"
        return html

    def add_weather_stations(self, time_hours: int = 3, station_ids: Optional[List[str]] = None) -> None:
        """
        Add weather stations to the map with current conditions.
        
        Args:
            time_hours: Hours back to look for weather data
            station_ids: Specific stations to plot (None for all)
        """
        if not self.map:
            self.create_base_map()
        
        # Get recent weather data
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_hours)
        
        weather_data = self.repo.query_weather_data(
            station_ids=station_ids,
            start_time=start_time,
            end_time=end_time,
            limit=1
        )
        
        stations_added = 0
        
        for station_id, data in weather_data.items():
            if station_id == '_sigmets':
                continue
                
            metars = data.get('metars', [])
            tafs = data.get('tafs', [])
            
            latest_metar = metars[0] if metars else None
            latest_taf = tafs[0] if tafs else None
            
            # Skip stations without location data
            if not latest_metar or not latest_metar.latitude or not latest_metar.longitude:
                continue
            
            # Determine marker properties
            station_type = self.classify_station(station_id)
            station_props = self.station_types[station_type]
            
            # Determine marker color based on flight category
            if latest_metar:
                category = self.determine_flight_category(latest_metar)
                color = self.flight_category_colors.get(category, '#6b7280')
            else:
                color = self.flight_category_colors['UNKNOWN']
            
            # Create popup content
            popup_html = self.create_weather_popup(station_id, latest_metar, latest_taf)
            
            # Add marker to map
            folium.CircleMarker(
                location=[latest_metar.latitude, latest_metar.longitude],
                radius=station_props['radius'],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"{station_id}: {latest_metar.temperature_celsius}°C" if latest_metar else station_id,
                color='white',
                weight=station_props['weight'],
                fillColor=color,
                fillOpacity=0.8
            ).add_to(self.map)
            
            stations_added += 1
        
        print(f"📍 Added {stations_added} weather stations to map")

    def add_flight_route(self, route_stations: List[str], route_name: str = "Flight Route", 
                        color: str = '#2563eb', weight: int = 3) -> None:
        """
        Add a flight route connecting multiple stations.
        
        Args:
            route_stations: List of station IDs in route order
            route_name: Name for the route
            color: Line color (hex)
            weight: Line weight
        """
        if not self.map:
            self.create_base_map()
        
        # Get station coordinates
        weather_data = self.repo.query_weather_data(
            station_ids=route_stations,
            start_time=datetime.now(timezone.utc) - timedelta(hours=6),
            limit=1
        )
        
        route_coords = []
        route_info = []
        
        for station_id in route_stations:
            data = weather_data.get(station_id, {})
            metars = data.get('metars', [])
            
            if metars and metars[0].latitude and metars[0].longitude:
                metar = metars[0]
                route_coords.append([metar.latitude, metar.longitude])
                route_info.append({
                    'station': station_id,
                    'temp': metar.temperature_celsius,
                    'wind': f"{metar.wind_direction_degrees}°/{metar.wind_speed_knots}kt" if metar.wind_direction_degrees else "Calm"
                })
        
        if len(route_coords) >= 2:
            # Add route line
            folium.PolyLine(
                locations=route_coords,
                color=color,
                weight=weight,
                opacity=0.8,
                popup=f"Route: {route_name}"
            ).add_to(self.map)
            
            # Add route waypoint markers
            for i, (coord, info) in enumerate(zip(route_coords, route_info)):
                folium.Marker(
                    location=coord,
                    popup=f"<b>{info['station']}</b><br>Waypoint {i+1}<br>{info['temp']}°C, {info['wind']}",
                    tooltip=f"{info['station']} (Waypoint {i+1})",
                    icon=folium.Icon(color='blue', icon='plane')
                ).add_to(self.map)
            
            print(f"✈️ Added route '{route_name}' with {len(route_coords)} waypoints")
        else:
            print(f"⚠️ Could not create route '{route_name}' - insufficient waypoint data")

    def add_legend(self) -> None:
        """Add a legend explaining the flight categories."""
        if not self.map:
            return
        
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 150px; height: 140px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin-top:0">Flight Categories</h4>
        <p><i class="fa fa-circle" style="color:#22c55e"></i> VFR (>8km vis)</p>
        <p><i class="fa fa-circle" style="color:#eab308"></i> MVFR (5-8km vis)</p>
        <p><i class="fa fa-circle" style="color:#ef4444"></i> IFR (1.6-5km vis)</p>
        <p><i class="fa fa-circle" style="color:#7c2d12"></i> LIFR (<1.6km vis)</p>
        </div>
        '''
        self.map.get_root().html.add_child(folium.Element(legend_html))

    def save_map(self, filename: str = "aviation_weather_map.html") -> str:
        """
        Save the map to an HTML file.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        if not self.map:
            raise ValueError("No map created yet. Call create_base_map() first.")
        
        filepath = Path(filename)
        self.map.save(str(filepath))
        
        print(f"💾 Map saved to: {filepath.resolve()}")
        return str(filepath.resolve())


def create_canada_aviation_map(demo: bool = False) -> str:
    """
    Create a comprehensive aviation weather map for Canada.
    
    Args:
        demo: If True, create a demo with sample routes
        
    Returns:
        Path to saved HTML file
    """
    print("🗺️ Creating Canadian Aviation Weather Map...")
    
    # Initialize repository and map
    repo = SQLiteWeatherRepository("weather_data/weather.db", echo=False)
    weather_map = AviationWeatherMap(repo)
    
    # Create base map
    weather_map.create_base_map()
    
    # Add all Canadian weather stations
    print("📍 Adding weather stations...")
    weather_map.add_weather_stations(time_hours=6)  # Last 6 hours of data
    
    if demo:
        # Add some sample flight routes
        print("✈️ Adding sample flight routes...")
        
        # Transcontinental route
        transcontinental = ["CYVR", "CYYC", "CYWG", "CYYZ", "CYUL"]
        weather_map.add_flight_route(transcontinental, "Transcontinental Route", "#dc2626", 4)
        
        # Eastern corridor
        eastern_route = ["CYYZ", "CYOW", "CYUL", "CYQB", "CYHZ"]
        weather_map.add_flight_route(eastern_route, "Eastern Corridor", "#2563eb", 3)
        
        # Prairie circuit
        prairie_route = ["CYWG", "CYQR", "CYXE", "CYEG", "CYYC"]
        weather_map.add_flight_route(prairie_route, "Prairie Circuit", "#16a34a", 3)
    
    # Add legend
    weather_map.add_legend()
    
    # Save map
    filename = "canadian_aviation_weather_map.html"
    filepath = weather_map.save_map(filename)
    
    repo.close()
    
    print("🎉 Map creation complete!")
    print(f"📂 Open {filepath} in your web browser to view the interactive map")
    
    return filepath


if __name__ == "__main__":
    # Create the aviation weather map
    create_canada_aviation_map(demo=True)