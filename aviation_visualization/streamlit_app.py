#!/usr/bin/env python3
"""
Advanced Streamlit Aviation Visualization
=======================================

A comprehensive Streamlit application for interactive aviation weather visualization
with 2D/3D maps, real-time weather data, and interactive route planning.
"""

import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
    from METAR_convert.metar import METAR
    from METAR_convert.taf import TAF
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.error("Make sure the METAR_convert package is available")
    st.stop()


class AdvancedAviationApp:
    """Advanced Streamlit aviation visualization application"""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
        self.load_weather_repository()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="🛩️ Aviation Weather Control Center",
            page_icon="✈️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        # Map settings
        if 'map_mode' not in st.session_state:
            st.session_state.map_mode = '3D'  # '2D' or '3D'
        if 'map_style' not in st.session_state:
            st.session_state.map_style = 'satellite'
        if 'show_all_stations' not in st.session_state:
            st.session_state.show_all_stations = True
        
        # Route building
        if 'flight_route' not in st.session_state:
            st.session_state.flight_route = []
        if 'waypoint_counter' not in st.session_state:
            st.session_state.waypoint_counter = 0
        
        # Weather data cache
        if 'weather_cache' not in st.session_state:
            st.session_state.weather_cache = {}
        if 'last_weather_update' not in st.session_state:
            st.session_state.last_weather_update = None
        
        # Map interaction
        if 'selected_station' not in st.session_state:
            st.session_state.selected_station = None
        if 'hover_weather' not in st.session_state:
            st.session_state.hover_weather = None
    
    def load_weather_repository(self):
        """Load weather database repository"""
        try:
            db_path = Path(__file__).parent.parent / "weather_data" / "weather.db"
            if db_path.exists():
                self.repo = SQLiteWeatherRepository(str(db_path))
                st.success("✅ Connected to weather database")
            else:
                st.warning(f"⚠️ Database not found at {db_path}")
                self.repo = None
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            self.repo = None
    
    def get_all_stations_from_db(self) -> pd.DataFrame:
        """Load all weather stations from database"""
        if not self.repo:
            return pd.DataFrame()
        
        try:
            # Get weather data from last 48 hours to find active stations
            weather_data = self.repo.query_weather_data([], hours_back=48)
            
            if not weather_data:
                return pd.DataFrame()
            
            # Extract unique stations with coordinates
            stations_dict = {}
            for record in weather_data:
                code = getattr(record, 'station_code', None)
                lat = getattr(record, 'latitude', None)
                lon = getattr(record, 'longitude', None)
                
                if code and lat and lon:
                    if code not in stations_dict:
                        stations_dict[code] = {
                            'code': code,
                            'name': getattr(record, 'station_name', code),
                            'lat': float(lat),
                            'lon': float(lon),
                            'latest_obs': getattr(record, 'observation_time', None),
                            'has_weather': True
                        }
            
            df = pd.DataFrame(list(stations_dict.values()))
            st.info(f"📡 Loaded {len(df)} weather stations from database")
            return df
            
        except Exception as e:
            st.error(f"❌ Error loading stations: {e}")
            return pd.DataFrame()
    
    def get_latest_weather(self, station_code: str) -> Optional[Dict]:
        """Get latest weather data for a station"""
        if not self.repo:
            return None
        
        # Check cache first
        cache_key = f"{station_code}_{datetime.now().strftime('%Y%m%d_%H')}"
        if cache_key in st.session_state.weather_cache:
            return st.session_state.weather_cache[cache_key]
        
        try:
            weather_data = self.repo.query_weather_data([station_code], hours_back=6)
            if weather_data:
                latest = weather_data[0]
                weather_info = {
                    'station': station_code,
                    'observation_time': getattr(latest, 'observation_time', None),
                    'temperature': getattr(latest, 'temperature_celsius', None),
                    'visibility': getattr(latest, 'visibility_meters', None),
                    'wind_speed': getattr(latest, 'wind_speed_knots', None),
                    'wind_direction': getattr(latest, 'wind_direction_degrees', None),
                    'conditions': getattr(latest, 'weather_phenomena', 'Unknown'),
                    'ceiling': getattr(latest, 'cloud_ceiling_feet', None),
                    'raw_metar': getattr(latest, 'raw_text', '')
                }
                
                # Cache the result
                st.session_state.weather_cache[cache_key] = weather_info
                return weather_info
                
        except Exception as e:
            st.error(f"Error getting weather for {station_code}: {e}")
        
        return None
    
    def get_flight_category(self, visibility: Optional[float], ceiling: Optional[float]) -> Tuple[str, str]:
        """Determine flight category from visibility and ceiling"""
        if visibility is None or ceiling is None:
            return 'UNKNOWN', '#6b7280'
        
        # Convert visibility from meters to statute miles
        vis_miles = visibility * 0.000621371 if visibility else 0
        # Convert ceiling from feet to hundreds of feet
        ceiling_hundreds = ceiling / 100 if ceiling else 0
        
        # Flight category rules
        if vis_miles >= 5 and ceiling_hundreds >= 30:
            return 'VFR', '#22c55e'      # Green
        elif vis_miles >= 3 and ceiling_hundreds >= 10:
            return 'MVFR', '#eab308'     # Yellow  
        elif vis_miles >= 1 and ceiling_hundreds >= 5:
            return 'IFR', '#ef4444'      # Red
        else:
            return 'LIFR', '#7c2d12'     # Dark Red
    
    def get_map_styles(self) -> Dict[str, str]:
        """Get available map styles"""
        return {
            'satellite': 'mapbox://styles/mapbox/satellite-streets-v11',
            'light': 'mapbox://styles/mapbox/light-v10',
            'dark': 'mapbox://styles/mapbox/dark-v10',
            'streets': 'mapbox://styles/mapbox/streets-v11',
            'outdoors': 'mapbox://styles/mapbox/outdoors-v11'
        }
    
    def create_station_layers(self, stations_df: pd.DataFrame, show_stations: bool = True) -> List:
        """Create map layers for weather stations"""
        layers = []
        
        if not show_stations or stations_df.empty:
            return layers
        
        # Add weather information to stations
        station_data = []
        for _, station in stations_df.iterrows():
            weather = self.get_latest_weather(station['code'])
            if weather:
                category, color = self.get_flight_category(
                    weather.get('visibility'), 
                    weather.get('ceiling')
                )
                
                # Convert color hex to RGB
                color_rgb = [int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), 200]
                
                station_data.append({
                    'code': station['code'],
                    'name': station['name'],
                    'lat': station['lat'],
                    'lon': station['lon'],
                    'category': category,
                    'color': color_rgb,
                    'elevation': weather.get('ceiling', 100),  # Use ceiling as elevation for 3D effect
                    'temperature': weather.get('temperature', 0),
                    'visibility': weather.get('visibility', 0),
                    'wind_speed': weather.get('wind_speed', 0),
                    'conditions': weather.get('conditions', 'Unknown')
                })
        
        if not station_data:
            return layers
        
        station_df = pd.DataFrame(station_data)
        
        if st.session_state.map_mode == '3D':
            # 3D Column layer for stations
            layers.append(
                pdk.Layer(
                    'ColumnLayer',
                    data=station_df,
                    get_position=['lon', 'lat'],
                    get_elevation='elevation',
                    elevation_scale=20,
                    radius=5000,
                    get_fill_color='color',
                    pickable=True,
                    auto_highlight=True,
                )
            )
        else:
            # 2D Scatterplot layer for stations
            layers.append(
                pdk.Layer(
                    'ScatterplotLayer',
                    data=station_df,
                    get_position=['lon', 'lat'],
                    get_radius=8000,
                    get_fill_color='color',
                    pickable=True,
                    auto_highlight=True,
                )
            )
        
        # Text labels for station codes
        layers.append(
            pdk.Layer(
                'TextLayer',
                data=station_df,
                get_position=['lon', 'lat'],
                get_text='code',
                get_size=12,
                get_color=[255, 255, 255, 255],
                get_angle=0,
                get_text_anchor='"middle"',
                get_alignment_baseline='"center"'
            )
        )
        
        return layers
    
    def create_route_layer(self) -> List:
        """Create route visualization layer"""
        layers = []
        
        if len(st.session_state.flight_route) < 2:
            return layers
        
        # Create path data
        path_coordinates = []
        for waypoint in st.session_state.flight_route:
            path_coordinates.append([waypoint['lon'], waypoint['lat']])
        
        # Route path layer
        layers.append(
            pdk.Layer(
                'PathLayer',
                data=[{'path': path_coordinates}],
                get_path='path',
                get_width=5,
                get_color=[255, 107, 53, 200],
                width_scale=1000,
                pickable=True
            )
        )
        
        # Waypoint markers
        waypoint_data = []
        for i, waypoint in enumerate(st.session_state.flight_route):
            waypoint_data.append({
                'lat': waypoint['lat'],
                'lon': waypoint['lon'],
                'name': waypoint.get('name', f"Waypoint {i+1}"),
                'type': waypoint.get('type', 'waypoint'),
                'order': i + 1
            })
        
        if waypoint_data:
            waypoint_df = pd.DataFrame(waypoint_data)
            
            # Waypoint markers
            layers.append(
                pdk.Layer(
                    'ScatterplotLayer',
                    data=waypoint_df,
                    get_position=['lon', 'lat'],
                    get_radius=6000,
                    get_fill_color=[255, 107, 53, 255],
                    get_line_color=[255, 255, 255, 255],
                    line_width_min_pixels=2,
                    pickable=True,
                    auto_highlight=True,
                )
            )
            
            # Waypoint numbers
            layers.append(
                pdk.Layer(
                    'TextLayer',
                    data=waypoint_df,
                    get_position=['lon', 'lat'],
                    get_text='order',
                    get_size=14,
                    get_color=[255, 255, 255, 255],
                    get_angle=0,
                    get_text_anchor='"middle"',
                    get_alignment_baseline='"center"'
                )
            )
        
        return layers
    
    def create_map(self, stations_df: pd.DataFrame) -> pdk.Deck:
        """Create the main map visualization"""
        
        # Combine all layers
        layers = []
        
        # Add station layers
        if st.session_state.show_all_stations:
            layers.extend(self.create_station_layers(stations_df, True))
        
        # Add route layers
        layers.extend(self.create_route_layer())
        
        # Set initial view state
        if st.session_state.flight_route:
            # Center on route
            route_lats = [w['lat'] for w in st.session_state.flight_route]
            route_lons = [w['lon'] for w in st.session_state.flight_route]
            center_lat = sum(route_lats) / len(route_lats)
            center_lon = sum(route_lons) / len(route_lons)
            zoom = 6
        else:
            # Default to Canada center
            center_lat, center_lon = 56.1304, -106.3468
            zoom = 4
        
        # Adjust pitch based on map mode
        pitch = 50 if st.session_state.map_mode == '3D' else 0
        
        view_state = pdk.ViewState(
            longitude=center_lon,
            latitude=center_lat,
            zoom=zoom,
            pitch=pitch,
            bearing=0
        )
        
        # Get map style
        map_styles = self.get_map_styles()
        map_style = map_styles.get(st.session_state.map_style, map_styles['satellite'])
        
        return pdk.Deck(
            map_style=map_style,
            initial_view_state=view_state,
            layers=layers,
            tooltip={
                'html': '''
                <b>{code}</b><br/>
                <b>Name:</b> {name}<br/>
                <b>Category:</b> {category}<br/>
                <b>Temperature:</b> {temperature}°C<br/>
                <b>Visibility:</b> {visibility}m<br/>
                <b>Wind:</b> {wind_speed} knots<br/>
                <b>Conditions:</b> {conditions}
                ''',
                'style': {
                    'backgroundColor': 'steelblue',
                    'color': 'white',
                    'fontSize': '12px',
                    'padding': '10px'
                }
            }
        )
    
    def add_waypoint_to_route(self, lat: float, lon: float, name: str = None, waypoint_type: str = 'waypoint'):
        """Add a waypoint to the current route"""
        waypoint = {
            'lat': lat,
            'lon': lon,
            'name': name or f"Waypoint {len(st.session_state.flight_route) + 1}",
            'type': waypoint_type,  # 'station' or 'waypoint'
            'order': len(st.session_state.flight_route) + 1
        }
        
        st.session_state.flight_route.append(waypoint)
        st.success(f"✅ Added {waypoint['name']} to route")
    
    def validate_route(self) -> Tuple[bool, str]:
        """Validate that route starts and ends with stations"""
        if len(st.session_state.flight_route) < 2:
            return False, "Route must have at least 2 waypoints"
        
        first = st.session_state.flight_route[0]
        last = st.session_state.flight_route[-1]
        
        if first.get('type') != 'station':
            return False, "Route must start with a weather station"
        
        if last.get('type') != 'station':
            return False, "Route must end with a weather station"
        
        return True, "Route is valid"
    
    def render_sidebar_controls(self, stations_df: pd.DataFrame):
        """Render the sidebar control panel"""
        
        with st.sidebar:
            st.header("🎛️ Aviation Control Center")
            
            # Map Settings
            st.subheader("🗺️ Map Settings")
            
            # 2D/3D Toggle
            map_mode = st.radio(
                "Map Mode",
                options=['2D', '3D'],
                index=0 if st.session_state.map_mode == '2D' else 1,
                horizontal=True
            )
            if map_mode != st.session_state.map_mode:
                st.session_state.map_mode = map_mode
                st.rerun()
            
            # Map Style
            map_styles = self.get_map_styles()
            style_names = list(map_styles.keys())
            style_index = style_names.index(st.session_state.map_style) if st.session_state.map_style in style_names else 0
            
            new_style = st.selectbox(
                "Map Style",
                options=style_names,
                index=style_index,
                format_func=str.title
            )
            if new_style != st.session_state.map_style:
                st.session_state.map_style = new_style
                st.rerun()
            
            # Station Display Toggle
            st.subheader("📡 Weather Stations")
            show_stations = st.checkbox(
                "Show All Database Stations",
                value=st.session_state.show_all_stations,
                help="Toggle display of all weather stations from database"
            )
            if show_stations != st.session_state.show_all_stations:
                st.session_state.show_all_stations = show_stations
                st.rerun()
            
            if not stations_df.empty:
                st.info(f"📊 {len(stations_df)} stations available")
            
            # Route Planning
            st.subheader("✈️ Route Planning")
            
            # Station selection for route building
            if not stations_df.empty:
                station_codes = stations_df['code'].tolist()
                selected_station = st.selectbox(
                    "Select Station to Add to Route",
                    options=[''] + station_codes,
                    key='station_selector'
                )
                
                if st.button("➕ Add Station to Route", disabled=not selected_station):
                    if selected_station:
                        station_info = stations_df[stations_df['code'] == selected_station].iloc[0]
                        self.add_waypoint_to_route(
                            lat=station_info['lat'],
                            lon=station_info['lon'],
                            name=f"{station_info['code']} - {station_info['name']}",
                            waypoint_type='station'
                        )
                        st.rerun()
            
            # Current Route Display
            if st.session_state.flight_route:
                st.write("**Current Route:**")
                for i, waypoint in enumerate(st.session_state.flight_route):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        icon = "📍" if waypoint['type'] == 'station' else "📌"
                        st.write(f"{i+1}. {icon} {waypoint['name']}")
                    with col2:
                        if st.button("❌", key=f"remove_{i}", help="Remove waypoint"):
                            st.session_state.flight_route.pop(i)
                            st.rerun()
                
                # Route validation
                is_valid, message = self.validate_route()
                if is_valid:
                    st.success(f"✅ {message}")
                else:
                    st.warning(f"⚠️ {message}")
                
                # Route actions
                if st.button("🗑️ Clear Route"):
                    st.session_state.flight_route = []
                    st.rerun()
                
                if is_valid:
                    if st.button("📊 Calculate Route Stats"):
                        total_distance = self.calculate_route_distance()
                        st.info(f"📏 Total Distance: ~{total_distance:.0f} km")
            
            else:
                st.info("Click stations on the map or use the selector above to build a route")
            
            # Weather Updates
            st.subheader("🌤️ Weather Data")
            if st.button("🔄 Refresh Weather Cache"):
                st.session_state.weather_cache = {}
                st.session_state.last_weather_update = datetime.now()
                st.success("Weather cache cleared")
                st.rerun()
            
            if st.session_state.last_weather_update:
                st.caption(f"Last updated: {st.session_state.last_weather_update.strftime('%H:%M:%S')}")
    
    def calculate_route_distance(self) -> float:
        """Calculate total route distance using Haversine formula"""
        if len(st.session_state.flight_route) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(st.session_state.flight_route) - 1):
            lat1 = st.session_state.flight_route[i]['lat']
            lon1 = st.session_state.flight_route[i]['lon']
            lat2 = st.session_state.flight_route[i + 1]['lat']
            lon2 = st.session_state.flight_route[i + 1]['lon']
            
            # Haversine formula
            from math import radians, cos, sin, asin, sqrt
            
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Earth's radius in kilometers
            
            total_distance += c * r
        
        return total_distance
    
    def render_main_content(self, stations_df: pd.DataFrame):
        """Render the main content area"""
        
        st.title("🛩️ Advanced Aviation Weather Control Center")
        st.markdown("**Interactive 2D/3D visualization with real-time weather data and route planning**")
        
        # Map display
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"🗺️ {st.session_state.map_mode} Aviation Map ({st.session_state.map_style.title()})")
            
            # Create and display map
            deck = self.create_map(stations_df)
            
            # Handle map interactions
            map_data = st.pydeck_chart(deck, use_container_width=True)
            
            # Map click instructions
            st.info("💡 **Instructions:** Toggle station display, change map styles, and build routes using the sidebar. Click stations to add them to your route!")
        
        with col2:
            st.subheader("📊 Flight Status")
            
            # Route information
            if st.session_state.flight_route:
                st.write(f"**Waypoints:** {len(st.session_state.flight_route)}")
                
                # Show route summary
                for i, waypoint in enumerate(st.session_state.flight_route):
                    if waypoint['type'] == 'station':
                        weather = self.get_latest_weather(waypoint['name'].split(' - ')[0])
                        if weather:
                            category, _ = self.get_flight_category(
                                weather.get('visibility'), 
                                weather.get('ceiling')
                            )
                            st.write(f"{i+1}. **{waypoint['name']}** - {category}")
                        else:
                            st.write(f"{i+1}. **{waypoint['name']}**")
                    else:
                        st.write(f"{i+1}. {waypoint['name']}")
                
                # Route statistics
                if len(st.session_state.flight_route) >= 2:
                    distance = self.calculate_route_distance()
                    st.metric("Total Distance", f"{distance:.0f} km")
                    
                    # Estimated flight time (assuming 500 km/h average speed)
                    flight_time = distance / 500
                    hours = int(flight_time)
                    minutes = int((flight_time - hours) * 60)
                    st.metric("Est. Flight Time", f"{hours}h {minutes}m")
            
            else:
                st.info("No route selected")
                st.write("Use the sidebar to build a flight route")
            
            # Weather summary
            st.subheader("🌤️ Weather Summary")
            
            if not stations_df.empty and st.session_state.show_all_stations:
                # Get weather categories distribution
                categories = {'VFR': 0, 'MVFR': 0, 'IFR': 0, 'LIFR': 0, 'UNKNOWN': 0}
                
                for _, station in stations_df.head(10).iterrows():  # Sample first 10 for performance
                    weather = self.get_latest_weather(station['code'])
                    if weather:
                        category, _ = self.get_flight_category(
                            weather.get('visibility'), 
                            weather.get('ceiling')
                        )
                        categories[category] += 1
                
                # Display weather categories
                for category, count in categories.items():
                    if count > 0:
                        color_map = {
                            'VFR': '🟢', 'MVFR': '🟡', 
                            'IFR': '🔴', 'LIFR': '⚫', 'UNKNOWN': '⚪'
                        }
                        st.write(f"{color_map[category]} {category}: {count} stations")
            
            else:
                st.write("Enable 'Show All Database Stations' to see weather summary")
    
    def run(self):
        """Run the Streamlit application"""
        
        # Load stations data
        stations_df = self.get_all_stations_from_db()
        
        # Render sidebar
        self.render_sidebar_controls(stations_df)
        
        # Render main content
        self.render_main_content(stations_df)
        
        # Footer
        st.markdown("---")
        st.markdown("**🎯 Aviation Weather Control Center** - Advanced visualization with real-time weather data")


def main():
    """Main function to run the application"""
    app = AdvancedAviationApp()
    app.run()


if __name__ == "__main__":
    main()