#!/usr/bin/env python3
"""
Advanced Streamlit Aviation Visualization
=======================================

A comprehensive Streamlit application for interactive aviation weather visualization
with 2D/3D maps, real-time weather data, and interactive route planning.
"""

import streamlit as st
import streamlit.components.v1 as components
import pydeck as pdk
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
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
        """Configure Streamlit page settings with modern styling"""
        st.set_page_config(
            page_title="🛩️ Aviation Weather Control Center",
            page_icon="✈️",
            layout="wide",
            initial_sidebar_state="collapsed"  # Start with collapsed sidebar for more map space
        )
        
        # Apply custom CSS for modern design
        st.markdown("""
        <style>
        /* Modern styling with reduced top padding */
        .main {
            padding-top: 0rem;
        }
        
        /* Remove default Streamlit margins */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        
        /* Ensure map displays properly */
        .stDeckGlJsonChart {
            min-height: 600px !important;
            height: 600px !important;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            padding-top: 1rem;
        }
        
        /* Clean map display */
        .stDeckGlJsonChart {
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Control panels */
        .control-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            border: none;
            background: linear-gradient(45deg, #3b82f6, #1d4ed8);
            color: white;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Responsive design */
        /* Minimize spacing around map */
        .element-container {
            margin-bottom: 0.5rem !important;
        }
        
            /* Compact header styling */
            .compact-header {
                text-align: center;
                padding: 8px 0 12px 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: -50px -20px 15px -20px;
                color: white;
                border-radius: 0 0 12px 12px;
            }
            
            .compact-header h2 {
                margin: 0;
                font-size: 1.8rem;
                font-weight: 600;
            }        @media (max-width: 768px) {
            .compact-header h2 {
                font-size: 1.4rem;
            }
            .map-container {
                height: calc(100vh - 120px);
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
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
                # Only show success in debug mode, not to users
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
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=48)
            weather_data = self.repo.query_weather_data(
                station_ids=None,
                start_time=start_time,
                end_time=end_time
            )
            
            if not weather_data:
                return pd.DataFrame()
            
            # Extract unique stations with coordinates
            stations_dict = {}
            for station_code, station_data in weather_data.items():
                # Skip special keys like '_sigmets'
                if station_code.startswith('_'):
                    continue

                metars = station_data.get('metars', [])
                if metars:
                    # Use most recent METAR for station info
                    record = metars[0]
                    lat = getattr(record, 'latitude', None)
                    lon = getattr(record, 'longitude', None)

                    if lat and lon and lat != 0.0 and lon != 0.0:
                        stations_dict[station_code] = {
                            'code': station_code,
                            'name': getattr(record, 'station_name', station_code),
                            'lat': float(lat),
                            'lon': float(lon),
                            'latest_obs': getattr(record, 'observation_time', None),
                            'has_weather': True
                        }
            
            df = pd.DataFrame(list(stations_dict.values()))
            # Only show debug info if needed, not to regular users
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
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=6)
            weather_data = self.repo.query_weather_data(
                station_ids=[station_code],
                start_time=start_time,
                end_time=end_time
            )
            if weather_data and station_code in weather_data:
                station_data = weather_data[station_code]
                metars = station_data.get('metars', [])
                if metars:
                    latest = metars[0]  # Most recent METAR
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
        
        # Flight category rules with enhanced visibility colors
        if vis_miles >= 5 and ceiling_hundreds >= 30:
            return 'VFR', '#00ff00'      # Bright Green
        elif vis_miles >= 3 and ceiling_hundreds >= 10:
            return 'MVFR', '#ffff00'     # Bright Yellow
        elif vis_miles >= 1 and ceiling_hundreds >= 5:
            return 'IFR', '#ff4500'      # Orange Red
        else:
            return 'LIFR', '#ff0000'     # Bright Red
    
    def get_map_styles(self) -> Dict[str, str]:
        """Get available map styles"""
        return {
            'satellite': None,  # Use default map
            'light': 'light',
            'dark': 'dark',
            'streets': 'road',
            'outdoors': None  # Use default map
        }

    def get_text_color_for_map_style(self) -> List[int]:
        """Get appropriate text color for current map style"""
        if st.session_state.map_style == 'dark':
            return [255, 255, 255, 255]  # White text for dark background
        elif st.session_state.map_style == 'light':
            return [0, 0, 0, 255]  # Black text for light background
        else:
            return [255, 255, 255, 255]  # White text for satellite/default

    def get_tooltip_style(self) -> Dict[str, str]:
        """Get tooltip style coordinated with map theme"""
        if st.session_state.map_style == 'dark':
            return {
                'backgroundColor': 'rgba(30, 30, 30, 0.95)',
                'color': 'white',
                'fontSize': '12px',
                'borderRadius': '8px',
                'border': '1px solid rgba(255, 255, 255, 0.2)',
                'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.5)'
            }
        elif st.session_state.map_style == 'light':
            return {
                'backgroundColor': 'rgba(255, 255, 255, 0.95)',
                'color': 'black',
                'fontSize': '12px',
                'borderRadius': '8px',
                'border': '1px solid rgba(0, 0, 0, 0.2)',
                'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.15)'
            }
        else:
            return {
                'backgroundColor': 'rgba(40, 40, 40, 0.95)',
                'color': 'white',
                'fontSize': '12px',
                'borderRadius': '8px',
                'border': '1px solid rgba(255, 255, 255, 0.3)',
                'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.6)'
            }
    
    def create_station_layers(self, stations_df: pd.DataFrame, show_stations: bool = True) -> List:
        """Create map layers for weather stations"""
        layers = []
        
        if not show_stations or stations_df.empty:
            return layers
        
        # Add weather information to stations - show stations even without weather data
        station_data = []
        for _, station in stations_df.iterrows():
            weather = self.get_latest_weather(station['code'])
            if weather:
                # Station with weather data
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
                    'category_color': color,  # Original hex color for tooltip
                    'color': color_rgb,
                    'elevation': weather.get('ceiling', 100),  # Use ceiling as elevation for 3D effect
                    'temperature': weather.get('temperature', 0),
                    'visibility': weather.get('visibility', 0),
                    'wind_speed': weather.get('wind_speed', 0),
                    'conditions': weather.get('conditions', 'Unknown')
                })
            else:
                # Station without weather data - show as gray/unknown
                station_data.append({
                    'code': station['code'],
                    'name': station['name'],
                    'lat': station['lat'],
                    'lon': station['lon'],
                    'category': 'UNKNOWN',
                    'category_color': '#808080',  # Gray color for unknown
                    'color': [128, 128, 128, 200],  # Gray RGB
                    'elevation': 100,  # Default elevation
                    'temperature': 0,
                    'visibility': 0,
                    'wind_speed': 0,
                    'conditions': 'No Data'
                })
        
        if not station_data:
            return layers
        
        station_df = pd.DataFrame(station_data)
        
        # Get text color based on map style
        text_color = self.get_text_color_for_map_style()

        if st.session_state.map_mode == '3D':
            # 3D Column layer for stations - bigger and more prominent
            layers.append(
                pdk.Layer(
                    'ColumnLayer',
                    data=station_df,
                    get_position=['lon', 'lat'],
                    get_elevation='elevation',
                    elevation_scale=30,
                    radius=8000,  # Bigger radius
                    get_fill_color='color',
                    get_line_color=[255, 255, 255, 100],  # White outline
                    line_width_min_pixels=1,
                    pickable=True,
                    auto_highlight=True,
                )
            )
        else:
            # 2D Scatterplot layer for stations - bigger with outline
            layers.append(
                pdk.Layer(
                    'ScatterplotLayer',
                    data=station_df,
                    get_position=['lon', 'lat'],
                    get_radius=12000,  # Much bigger radius
                    get_fill_color='color',
                    get_line_color=[255, 255, 255, 180],  # White outline
                    get_line_width=2,
                    line_width_min_pixels=2,
                    pickable=True,
                    auto_highlight=True,
                )
            )
        
        # Text labels for station codes - positioned above stations
        # Use larger text size if toggle is enabled, with better scaling
        text_size = 24 if st.session_state.get('large_station_names', False) else 16
        
        layers.append(
            pdk.Layer(
                'TextLayer',
                data=station_df,
                get_position=['lon', 'lat'],
                get_text='code',
                get_size=text_size,
                size_scale=1,  # Enable size scaling with zoom
                size_min_pixels=12,  # Minimum size in pixels
                size_max_pixels=48,  # Maximum size in pixels
                get_color=text_color,
                get_angle=0,
                get_text_anchor='"middle"',
                get_alignment_baseline='"bottom"',  # Position above the station
                billboard=True,  # Always face the camera
                font_family='"Arial", sans-serif',
                font_weight='bold',
                pickable=True
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
            waypoint_text_size = 16 if st.session_state.get('large_station_names', False) else 12
            
            layers.append(
                pdk.Layer(
                    'TextLayer',
                    data=waypoint_df,
                    get_position=['lon', 'lat'],
                    get_text='order',
                    get_size=waypoint_text_size,
                    get_color=[255, 255, 255, 255],
                    get_angle=0,
                    get_text_anchor='"middle"',
                    get_alignment_baseline='"center"',
                    font_weight='bold'
                )
            )
        
        return layers
    
    def create_map(self, stations_df: pd.DataFrame) -> pdk.Deck:
        """Create the main map visualization"""
        
        # Combine all layers
        layers = []
        
        # Add station layers - debug and fix
        show_stations = st.session_state.get('show_all_stations', True)
        
        # Add a clickable background layer for custom points (when route building is active)
        if st.session_state.get('show_quick_route_builder', False):
            # Create a grid of invisible points covering the map for clicking
            background_points = []
            for lat in range(-80, 81, 20):  # Every 20 degrees
                for lon in range(-180, 181, 20):
                    background_points.append({'lat': lat, 'lon': lon})
            
            if background_points:
                layers.append(
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=pd.DataFrame(background_points),
                        get_position=['lon', 'lat'],
                        get_radius=0,  # Invisible but clickable
                        get_fill_color=[0, 0, 0, 0],  # Completely transparent
                        pickable=True,
                        auto_highlight=False,
                    )
                )

        # Add station layers
        if show_stations and not stations_df.empty:
            station_layers = self.create_station_layers(stations_df, True)
            if station_layers:  # Only add if not empty
                layers.extend(station_layers)
        
        # Add route layers only if route exists
        route_layers = self.create_route_layer()
        if route_layers:  # Only add if not empty
            layers.extend(route_layers)
        
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
        map_style = map_styles.get(st.session_state.map_style, None)

        deck_kwargs = {
            'initial_view_state': view_state,
            'layers': layers,
        }

        # Only add map_style if it's not None
        if map_style is not None:
            deck_kwargs['map_style'] = map_style

        # Get tooltip style based on map theme
        tooltip_style = self.get_tooltip_style()
        
        deck_kwargs['tooltip'] = {
            'html': '''
            <div style="padding: 8px;">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 4px;">{code}</div>
                <div style="font-size: 14px; margin-bottom: 2px;"><strong>Name:</strong> {name}</div>
                <div style="font-size: 14px; margin-bottom: 2px;"><strong>Category:</strong> <span style="padding: 2px 6px; border-radius: 3px; background: {category_color}; color: white;">{category}</span></div>
                <div style="font-size: 14px; margin-bottom: 2px;"><strong>Temperature:</strong> {temperature}°C</div>
                <div style="font-size: 14px; margin-bottom: 2px;"><strong>Visibility:</strong> {visibility}m</div>
                <div style="font-size: 14px; margin-bottom: 2px;"><strong>Wind:</strong> {wind_speed} knots</div>
                <div style="font-size: 14px;"><strong>Conditions:</strong> {conditions}</div>
            </div>
            ''',
            'style': tooltip_style
        }

        return pdk.Deck(**deck_kwargs)
    
    def _add_quick_waypoint(self, lat: float, lon: float, name: str, waypoint_type: str = 'station'):
        """Quick method to add a waypoint"""
        if 'route_waypoints' not in st.session_state:
            st.session_state.route_waypoints = []
        
        waypoint = {
            'name': name,
            'lat': float(lat),
            'lon': float(lon),
            'type': waypoint_type
        }
        
        st.session_state.route_waypoints.append(waypoint)
        st.session_state.flight_route = st.session_state.route_waypoints.copy()
        
        st.success(f"✅ 已添加航点: {name} ({lat:.3f}, {lon:.3f})")
        st.rerun()

    def _process_map_click(self, click_info):
        """Process a map click event and add waypoint"""
        if not click_info:
            return
            
        # Extract coordinates - try different possible formats
        lat, lon = None, None
        
        if 'coordinate' in click_info:
            lat, lon = click_info['coordinate']
        elif 'lat' in click_info and 'lon' in click_info:
            lat, lon = click_info['lat'], click_info['lon']
        elif 'position' in click_info:
            lon, lat = click_info['position']  # Note: PyDeck uses [lon, lat] format
        
        if lat is not None and lon is not None:
            # Determine waypoint info
            if 'code' in click_info:
                # Clicked on a station
                waypoint_name = f"{click_info['code']} - {click_info.get('name', click_info['code'])}"
                waypoint_type = 'station'
            else:
                # Clicked on empty map area
                waypoint_name = f"Point_{len(st.session_state.get('route_waypoints', []))+1}"
                waypoint_type = 'custom'
            
            # Add to route
            if 'route_waypoints' not in st.session_state:
                st.session_state.route_waypoints = []
            
            waypoint = {
                'name': waypoint_name,
                'lat': float(lat),
                'lon': float(lon),
                'type': waypoint_type
            }
            
            st.session_state.route_waypoints.append(waypoint)
            st.session_state.flight_route = st.session_state.route_waypoints.copy()
            
            st.success(f"✅ 已添加航点: {waypoint_name} ({lat:.3f}, {lon:.3f})")
            st.rerun()

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
        """Render the main content area with modern design - SINGLE MAP ONLY"""
        
        # Initialize render control to prevent duplicates
        if 'main_content_rendered' not in st.session_state:
            st.session_state.main_content_rendered = True
        
        # Compact header
        st.markdown("""
        <div class="compact-header">
            <h2>🛩️ Aviation Weather Control Center</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Optimized control layout - Essential controls first
        main_col1, main_col2, main_col3 = st.columns([1, 1, 1])
        
        with main_col1:
            new_mode = st.radio("🗺️ View Mode", ['2D', '3D'], 
                              index=0 if st.session_state.map_mode == '2D' else 1,
                              horizontal=True,
                              key='quick_mode')
            if new_mode != st.session_state.map_mode:
                st.session_state.map_mode = new_mode
                st.rerun()
        
        with main_col2:
            styles = ['satellite', 'light', 'dark', 'streets', 'outdoors']
            new_style = st.selectbox("🎨 Map Style", styles,
                                   index=styles.index(st.session_state.map_style),
                                   key='quick_style')
            if new_style != st.session_state.map_style:
                st.session_state.map_style = new_style
                st.rerun()
        
        with main_col3:
            stations_status = "ON" if st.session_state.show_all_stations else "OFF"
            if st.button(f"📡 Stations [{stations_status}]", help="Toggle stations", use_container_width=True):
                st.session_state.show_all_stations = not st.session_state.show_all_stations
                st.rerun()
        
        # Secondary action buttons
        st.markdown("**⚙️ Quick Actions**")
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            # Station name size toggle with status
            if 'large_station_names' not in st.session_state:
                st.session_state.large_station_names = False
            
            name_size = "Large" if st.session_state.large_station_names else "Normal"
            if st.button(f"🔤 Names [{name_size}]", help="Toggle name size", use_container_width=True):
                st.session_state.large_station_names = not st.session_state.large_station_names
                st.rerun()
        
        with action_col2:
            if st.button(" Refresh", help="Update weather", use_container_width=True):
                st.session_state.weather_cache = {}
                st.rerun()
        
        with action_col3:
            route_count = len(st.session_state.flight_route)
            if route_count > 0:
                if st.button(f"🗑️ Clear Route ({route_count})", help="Clear route", use_container_width=True):
                    st.session_state.flight_route = []
                    st.rerun()
            else:
                st.button("🗑️ No Route", disabled=True, use_container_width=True)
        
        with action_col4:
            # Route builder toggle - always available
            current_builder_state = st.session_state.get('show_quick_route_builder', False)
            builder_text = "🔧 Route Builder" if not current_builder_state else "📊 Hide Builder"
            
            if st.button(builder_text, help="Toggle route building interface", use_container_width=True):
                st.session_state.show_quick_route_builder = not current_builder_state
                st.rerun()
                
            # Show route info as separate element if route exists
            if route_count > 0:
                distance = self.calculate_route_distance() if route_count > 1 else 0
                st.caption(f"✈️ {route_count} stops • {distance:.0f}km")
        
        # Main map area - maximized with proper display
        # Create and display the map with click interaction
        deck = self.create_map(stations_df)
        
        # Render PyDeck chart with click event handling
        clicked_data = st.pydeck_chart(
            deck, 
            use_container_width=True, 
            height=600,
            key="aviation_map"
        )
        
        # Handle map clicks for route building with improved detection
        if st.session_state.get('show_quick_route_builder', False):
            
            # Display map selection status
            if st.session_state.get('map_selection_mode', False):
                st.warning("🎯 **地图选点模式激活中** - 请在地图上点击您想添加航点的位置")
                
                # Check for PyDeck click events when in selection mode
                try:
                    if clicked_data and hasattr(clicked_data, 'last_object_clicked'):
                        click_obj = clicked_data.last_object_clicked
                        if click_obj:
                            self._process_map_click(click_obj)
                            st.session_state.map_selection_mode = False  # Turn off selection mode after click
                except:
                    pass
            
            # Quick add buttons for common coordinates
            st.markdown("#### 🎯 快速添加航点")
            quick_add_col1, quick_add_col2, quick_add_col3, quick_add_col4 = st.columns(4)
            
            with quick_add_col1:
                if st.button("📍 北京 (PEK)", use_container_width=True):
                    self._add_quick_waypoint(40.0801, 116.5846, "北京首都机场 (PEK)", "station")
            
            with quick_add_col2:
                if st.button("📍 上海 (PVG)", use_container_width=True):
                    self._add_quick_waypoint(31.1434, 121.8052, "上海浦东机场 (PVG)", "station")
            
            with quick_add_col3:
                if st.button("📍 广州 (CAN)", use_container_width=True):
                    self._add_quick_waypoint(23.3924, 113.2988, "广州白云机场 (CAN)", "station")
                    
            with quick_add_col4:
                if st.button("� 深圳 (SZX)", use_container_width=True):
                    self._add_quick_waypoint(22.6393, 113.8107, "深圳宝安机场 (SZX)", "station")
                    
            # Check for click events in PyDeck data
            try:
                # Method 1: Check for last_clicked_object attribute
                if hasattr(clicked_data, 'last_clicked_object') and clicked_data.last_clicked_object:
                    self._process_map_click(clicked_data.last_clicked_object)
                
                # Method 2: Check if clicked_data is a dict with click info
                elif isinstance(clicked_data, dict) and 'last_clicked_object' in clicked_data:
                    self._process_map_click(clicked_data['last_clicked_object'])
                
                # Method 3: Check for coordinate data directly
                elif isinstance(clicked_data, dict) and any(k in clicked_data for k in ['coordinate', 'lat', 'lon']):
                    self._process_map_click(clicked_data)
                    
            except Exception as e:
                # Silent handling - clicking might not always work immediately
                pass
        
        # Route builder interface
        if st.session_state.get('show_quick_route_builder', False):
            st.markdown("---")
            st.markdown("### 🛠️ Route Builder")
            
            # Click mode control
            click_mode_col1, click_mode_col2 = st.columns([3, 1])
            
            with click_mode_col1:
                st.info("🖱️ **地图交互模式** - 按住 Ctrl + 点击 或 使用下方按钮添加航点")
            
            with click_mode_col2:
                if st.button("🗺️ 地图选点", use_container_width=True):
                    st.session_state.map_selection_mode = not st.session_state.get('map_selection_mode', False)
                    if st.session_state.map_selection_mode:
                        st.success("🎯 地图选点模式已激活！请点击地图上的位置")
                    else:
                        st.info("地图选点模式已关闭")
                    st.rerun()
            
            # Add coordinate input for manual point addition
            st.markdown("#### 📍 手动添加航点坐标")
            
            # Coordinate input with suggested values
            coord_input_col1, coord_input_col2 = st.columns(2)
            
            with coord_input_col1:
                st.markdown("**常用机场坐标参考:**")
                st.caption("• 北京首都: 40.080, 116.585")
                st.caption("• 上海浦东: 31.143, 121.805") 
                st.caption("• 广州白云: 23.392, 113.299")
                st.caption("• 成都双流: 30.578, 103.947")
                
            with coord_input_col2:
                coord_col1, coord_col2, coord_col3 = st.columns([2, 2, 1])
                
                with coord_col1:
                    lat_input = st.number_input("纬度 (Latitude)", 
                                              value=st.session_state.get('last_lat', 39.0), 
                                              min_value=-90.0, 
                                              max_value=90.0, 
                                              step=0.001,
                                              format="%.3f",
                                              key="manual_lat")
                with coord_col2:
                    lon_input = st.number_input("经度 (Longitude)", 
                                              value=st.session_state.get('last_lon', 116.0), 
                                              min_value=-180.0, 
                                              max_value=180.0, 
                                              step=0.001,
                                              format="%.3f",
                                              key="manual_lon")
                with coord_col3:
                    if st.button("📍 添加点", use_container_width=True):
                        self._add_quick_waypoint(lat_input, lon_input, 
                                               f"Custom_{len(st.session_state.get('route_waypoints', []))+1}",
                                               'custom')
                        
                        # Remember last coordinates
                        st.session_state.last_lat = lat_input
                        st.session_state.last_lon = lon_input
        
        # Quick route builder (appears when user clicks Build Route button)
        if st.session_state.get('show_quick_route_builder', False) and not stations_df.empty:
            st.markdown("---")
            st.markdown("### 🚀 Quick Route Builder")
            st.info("💡 **添加航点方式:** ① 手动输入坐标添加任意点 ② 使用下拉菜单选择已知机场站点 ③ 查看地图选择合适位置")
            
            quick_col1, quick_col2, quick_col3 = st.columns([3, 1, 1])
            
            with quick_col1:
                # Quick station selection
                station_codes = stations_df['code'].tolist()
                selected_quick_station = st.selectbox(
                    "Select Airport Station",
                    options=[''] + station_codes,
                    key='quick_station_selector',
                    help="Choose an airport to add to your route"
                )
            
            with quick_col2:
                if st.button("➕ Add to Route", disabled=not selected_quick_station, use_container_width=True):
                    if selected_quick_station:
                        station_info = stations_df[stations_df['code'] == selected_quick_station].iloc[0]
                        self.add_waypoint_to_route(
                            lat=station_info['lat'],
                            lon=station_info['lon'],
                            name=f"{station_info['code']} - {station_info['name']}",
                            waypoint_type='station'
                        )
                        st.success(f"Added {selected_quick_station} to route!")
                        st.rerun()
            
            with quick_col3:
                if st.button("❌ Close", use_container_width=True):
                    st.session_state.show_quick_route_builder = False
                    st.rerun()
            
            st.info("💡 **提示:** 你也可以使用左侧边栏进行更详细的路线规划")
            st.markdown("---")
        
        # Route status at bottom (compact)
        if st.session_state.flight_route:
            with st.expander("✈️ Current Flight Route", expanded=False):
                route_col1, route_col2 = st.columns([3, 1])
                
                with route_col1:
                    # Route waypoints in compact format
                    waypoint_names = [w['name'] for w in st.session_state.flight_route]
                    route_text = " ➡️ ".join(waypoint_names)
                    st.markdown(f"**Route:** {route_text}")
                    
                    # Route validation
                    is_valid, message = self.validate_route()
                    if is_valid:
                        total_distance = self.calculate_route_distance()
                        st.success(f"✅ {message} • Distance: ~{total_distance:.0f} km")
                    else:
                        st.warning(f"⚠️ {message}")
                
                with route_col2:
                    if st.button("📊 Route Details", key="route_details"):
                        st.session_state.show_route_details = not st.session_state.get('show_route_details', False)
                
                # Show detailed route info if requested
                if st.session_state.get('show_route_details', False):
                    st.markdown("### Route Waypoints")
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
        else:
            # Show message when no route is selected
            st.info("💡 **Tip:** Use the sidebar to build a flight route and see weather conditions along your path.")
            
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