#!/usr/bin/env python3
"""
Interactive Route Builder for Aviation Weather
=============================================

Creates an interactive map where users can click on Canadian weather stations 
to build custom flight routes dynamically.
"""

import folium
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
    from aviation_visualization.weather_map import AviationWeatherMap
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the METAR_convert package and aviation_visualization are available")
    sys.exit(1)


class InteractiveRouteBuilder:
    """Interactive map for building custom flight routes by clicking stations."""
    
    def __init__(self, repository: SQLiteWeatherRepository):
        """
        Initialize the interactive route builder.
        
        Args:
            repository: SQLiteWeatherRepository instance for data access
        """
        self.repo = repository
        self.weather_map = AviationWeatherMap(repository)
        
        # Station data cache
        self.canadian_stations = {}
        self.selected_route = []
        
        # Load Canadian station coordinates
        self._load_canadian_stations()
    
    def _load_canadian_stations(self):
        """Load all Canadian weather stations with coordinates."""
        print("📡 Loading Canadian weather stations...")
        
        # Get weather data for Canadian stations (stations starting with 'CY')
        try:
            # Query recent data to get station coordinates
            weather_data = self.repo.query_weather_by_region(
                min_lat=41.0, max_lat=84.0,  # Canada latitude range
                min_lon=-141.0, max_lon=-52.0,  # Canada longitude range  
                hours_back=48
            )
            
            # Extract unique Canadian stations with coordinates
            for record in weather_data:
                if hasattr(record, 'station_code') and record.station_code.startswith('CY'):
                    if hasattr(record, 'latitude') and hasattr(record, 'longitude'):
                        if record.latitude and record.longitude:
                            self.canadian_stations[record.station_code] = {
                                'lat': float(record.latitude),
                                'lon': float(record.longitude),
                                'name': getattr(record, 'station_name', record.station_code)
                            }
            
            print(f"✅ Loaded {len(self.canadian_stations)} Canadian weather stations")
            
        except Exception as e:
            print(f"⚠️ Error loading stations: {e}")
            # Fallback to hardcoded major Canadian airports
            self._load_fallback_stations()
    
    def _load_fallback_stations(self):
        """Load fallback major Canadian airports if database query fails."""
        print("🔄 Using fallback major Canadian airports...")
        
        major_airports = {
            'CYYZ': {'lat': 43.6777, 'lon': -79.6248, 'name': 'Toronto Pearson'},
            'CYVR': {'lat': 49.1967, 'lon': -123.1815, 'name': 'Vancouver Intl'},
            'CYUL': {'lat': 45.4706, 'lon': -73.7378, 'name': 'Montreal Trudeau'},
            'CYYC': {'lat': 51.1315, 'lon': -114.0109, 'name': 'Calgary Intl'},
            'CYOW': {'lat': 45.3192, 'lon': -75.6692, 'name': 'Ottawa Macdonald-Cartier'},
            'CYWG': {'lat': 49.9100, 'lon': -97.2398, 'name': 'Winnipeg Richardson'},
            'CYEG': {'lat': 51.3089, 'lon': -113.5803, 'name': 'Edmonton Intl'},
            'CYHZ': {'lat': 44.8807, 'lon': -63.5086, 'name': 'Halifax Stanfield'},
            'CYQB': {'lat': 46.7911, 'lon': -71.3933, 'name': 'Quebec City Jean Lesage'},
            'CYXE': {'lat': 52.1708, 'lon': -106.7000, 'name': 'Saskatoon John G Diefenbaker'},
            'CYQR': {'lat': 50.4319, 'lon': -104.6657, 'name': 'Regina Intl'},
            'CYYJ': {'lat': 48.6469, 'lon': -123.4258, 'name': 'Victoria Intl'},
            'CYYT': {'lat': 47.6186, 'lon': -52.7518, 'name': "St John's Intl"},
            'CYFC': {'lat': 45.8681, 'lon': -66.5322, 'name': 'Fredericton Intl'},
            'CYZF': {'lat': 62.4628, 'lon': -114.4400, 'name': 'Yellowknife'},
            'CYFS': {'lat': 61.7602, 'lon': -121.2367, 'name': 'Fort Simpson'},
            'CYQA': {'lat': 53.3092, 'lon': -60.4256, 'name': 'Muskoka'},
        }
        
        self.canadian_stations = major_airports
        print(f"✅ Loaded {len(self.canadian_stations)} major Canadian airports")
    
    def create_interactive_route_map(self) -> folium.Map:
        """
        Create an interactive map with clickable stations for route building.
        
        Returns:
            Folium map with interactive route building capabilities
        """
        print("🗺️ Creating interactive route builder map...")
        
        # Create base map centered on Canada
        canada_center = [56.1304, -106.3468]
        route_map = folium.Map(
            location=canada_center,
            zoom_start=4,
            tiles='OpenStreetMap'
        )
        
        # Add custom JavaScript for route building
        self._add_route_builder_js(route_map)
        
        # Add all Canadian stations as clickable markers
        for station_code, station_info in self.canadian_stations.items():
            self._add_clickable_station(route_map, station_code, station_info)
        
        # Add control panel for route management
        self._add_control_panel(route_map)
        
        # Add legend
        self._add_interactive_legend(route_map)
        
        print(f"✅ Added {len(self.canadian_stations)} clickable weather stations")
        return route_map
    
    def _add_route_builder_js(self, map_obj: folium.Map):
        """Add JavaScript for interactive route building."""
        
        js_code = """
        <script>
        // Global variables for route building
        var selectedRoute = [];
        var routePolyline = null;
        var routeMarkers = [];
        
        // Function to add station to route
        function addToRoute(stationCode, lat, lon, name) {
            // Check if station already in route
            if (selectedRoute.some(s => s.code === stationCode)) {
                alert('Station ' + stationCode + ' is already in your route!');
                return;
            }
            
            // Add to route
            selectedRoute.push({
                code: stationCode,
                lat: lat,
                lon: lon,
                name: name,
                order: selectedRoute.length + 1
            });
            
            // Update route display
            updateRouteDisplay();
            updateRouteList();
            
            console.log('Added to route:', stationCode);
        }
        
        // Function to remove station from route  
        function removeFromRoute(stationCode) {
            selectedRoute = selectedRoute.filter(s => s.code !== stationCode);
            
            // Renumber remaining stations
            selectedRoute.forEach((station, index) => {
                station.order = index + 1;
            });
            
            updateRouteDisplay();
            updateRouteList();
        }
        
        // Function to clear entire route
        function clearRoute() {
            if (confirm('Clear entire route?')) {
                selectedRoute = [];
                updateRouteDisplay();
                updateRouteList();
            }
        }
        
        // Function to update route line on map
        function updateRouteDisplay() {
            // Remove existing route line
            if (routePolyline) {
                map.removeLayer(routePolyline);
                routePolyline = null;
            }
            
            // Remove existing route markers
            routeMarkers.forEach(marker => map.removeLayer(marker));
            routeMarkers = [];
            
            // Add new route line if we have 2+ stations
            if (selectedRoute.length >= 2) {
                var latlngs = selectedRoute.map(s => [s.lat, s.lon]);
                
                routePolyline = L.polyline(latlngs, {
                    color: '#ff6b35',
                    weight: 4,
                    opacity: 0.8
                }).addTo(map);
                
                // Add numbered waypoint markers
                selectedRoute.forEach((station, index) => {
                    var marker = L.circleMarker([station.lat, station.lon], {
                        radius: 12,
                        fillColor: '#ff6b35',
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.9
                    }).addTo(map);
                    
                    // Add number label
                    marker.bindTooltip((index + 1).toString(), {
                        permanent: true,
                        direction: 'center',
                        className: 'route-number-label'
                    });
                    
                    routeMarkers.push(marker);
                });
            }
        }
        
        // Function to update route list in control panel
        function updateRouteList() {
            var routeListEl = document.getElementById('route-list');
            if (!routeListEl) return;
            
            if (selectedRoute.length === 0) {
                routeListEl.innerHTML = '<em>Click stations to build route...</em>';
                return;
            }
            
            var html = '<h4>Current Route:</h4><ol>';
            selectedRoute.forEach((station, index) => {
                html += `<li>
                    <strong>${station.code}</strong> - ${station.name}
                    <button onclick="removeFromRoute('${station.code}')" style="margin-left:5px; font-size:12px;">✕</button>
                </li>`;
            });
            html += '</ol>';
            html += `<p><strong>Total Distance:</strong> ~${calculateRouteDistance()} km</p>`;
            html += '<button onclick="clearRoute()" style="background:#dc2626; color:white; padding:5px 10px; margin-top:10px;">Clear Route</button>';
            html += '<button onclick="exportRoute()" style="background:#059669; color:white; padding:5px 10px; margin-top:5px; margin-left:5px;">Export Route</button>';
            
            routeListEl.innerHTML = html;
        }
        
        // Function to calculate approximate route distance
        function calculateRouteDistance() {
            if (selectedRoute.length < 2) return 0;
            
            var totalDistance = 0;
            for (var i = 0; i < selectedRoute.length - 1; i++) {
                var from = selectedRoute[i];
                var to = selectedRoute[i + 1];
                totalDistance += calculateDistance(from.lat, from.lon, to.lat, to.lon);
            }
            return Math.round(totalDistance);
        }
        
        // Haversine distance formula
        function calculateDistance(lat1, lon1, lat2, lon2) {
            var R = 6371; // Earth's radius in km
            var dLat = (lat2 - lat1) * Math.PI / 180;
            var dLon = (lon2 - lon1) * Math.PI / 180;
            var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                    Math.sin(dLon/2) * Math.sin(dLon/2);
            var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }
        
        // Function to export route
        function exportRoute() {
            if (selectedRoute.length === 0) {
                alert('No route to export!');
                return;
            }
            
            var routeData = {
                route: selectedRoute.map(s => s.code),
                distance: calculateRouteDistance(),
                waypoints: selectedRoute
            };
            
            var dataStr = JSON.stringify(routeData, null, 2);
            var dataBlob = new Blob([dataStr], {type: 'application/json'});
            var url = URL.createObjectURL(dataBlob);
            
            var link = document.createElement('a');
            link.href = url;
            link.download = 'custom_flight_route_' + new Date().toISOString().slice(0,10) + '.json';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            alert('Route exported! Check your downloads folder.');
        }
        </script>
        
        <style>
        .route-control-panel {
            position: fixed;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 300px;
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        
        .route-number-label {
            background: transparent !important;
            border: none !important;
            font-weight: bold;
            color: white;
            font-size: 11px;
        }
        
        .clickable-marker {
            cursor: pointer;
        }
        
        .clickable-marker:hover {
            transform: scale(1.1);
        }
        </style>
        """
        
        map_obj.get_root().html.add_child(folium.Element(js_code))
    
    def _add_clickable_station(self, map_obj: folium.Map, station_code: str, station_info: Dict):
        """Add a clickable weather station marker."""
        
        # Create custom icon for weather stations
        icon_html = f"""
        <div style="
            background-color: #3b82f6;
            border: 2px solid white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        " 
        onclick="addToRoute('{station_code}', {station_info['lat']}, {station_info['lon']}, '{station_info['name']}')">
            ✈
        </div>
        """
        
        # Create marker with custom HTML
        marker = folium.Marker(
            location=[station_info['lat'], station_info['lon']],
            icon=folium.DivIcon(
                html=icon_html,
                icon_size=(20, 20),
                icon_anchor=(10, 10),
                class_name='clickable-marker'
            )
        )
        
        # Add informative popup
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #1f2937;">{station_code}</h4>
            <p style="margin: 5px 0;"><strong>Name:</strong> {station_info['name']}</p>
            <p style="margin: 5px 0;"><strong>Coordinates:</strong> {station_info['lat']:.4f}, {station_info['lon']:.4f}</p>
            <button onclick="addToRoute('{station_code}', {station_info['lat']}, {station_info['lon']}, '{station_info['name']}')" 
                    style="
                        background: #3b82f6;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                        margin-top: 10px;
                        width: 100%;
                    ">
                ➕ Add to Route
            </button>
        </div>
        """
        
        marker.add_child(folium.Popup(popup_html, max_width=250))
        marker.add_to(map_obj)
    
    def _add_control_panel(self, map_obj: folium.Map):
        """Add route management control panel."""
        
        control_html = """
        <div class="route-control-panel">
            <h3 style="margin-top: 0; color: #1f2937;">🛩️ Route Builder</h3>
            <p style="font-size: 12px; color: #6b7280;">
                Click on any weather station marker to add it to your custom route.
            </p>
            <div id="route-list">
                <em>Click stations to build route...</em>
            </div>
        </div>
        """
        
        map_obj.get_root().html.add_child(folium.Element(control_html))
    
    def _add_interactive_legend(self, map_obj: folium.Map):
        """Add legend for the interactive map."""
        
        legend_html = """
        <div style="
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 1000;
        ">
            <h4 style="margin-top: 0;">How to Use</h4>
            <p style="margin: 5px 0;"><span style="color: #3b82f6;">✈</span> Weather Station (click to add)</p>
            <p style="margin: 5px 0;"><span style="color: #ff6b35;">━</span> Your Custom Route</p>
            <p style="margin: 5px 0; font-size: 12px; color: #6b7280;">
                Build routes by clicking stations in order. Export when done!
            </p>
        </div>
        """
        
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def save_interactive_map(self, filename: str = "interactive_route_builder.html") -> str:
        """
        Save the interactive route builder map.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        # Create the interactive map
        interactive_map = self.create_interactive_route_map()
        
        # Save using the same directory structure as other maps
        package_dir = Path(__file__).parent
        maps_dir = package_dir / "maps"
        maps_dir.mkdir(exist_ok=True)
        
        filepath = maps_dir / filename
        interactive_map.save(str(filepath))
        
        print(f"💾 Interactive route builder saved to: {filepath.resolve()}")
        return str(filepath.resolve())


def create_route_builder_demo():
    """Demo function to create and save the interactive route builder."""
    
    print("🚀 Creating Interactive Route Builder Demo")
    print("=" * 45)
    
    try:
        # Initialize repository
        repo = SQLiteWeatherRepository("weather_data/weather.db")
        
        # Create route builder
        builder = InteractiveRouteBuilder(repo)
        
        # Create and save interactive map
        map_file = builder.save_interactive_map("canada_route_builder.html")
        
        # Cleanup
        repo.close()
        
        print(f"✅ Interactive route builder created!")
        print(f"🌐 Open {map_file} in your browser")
        print(f"🎯 Click on weather stations to build custom flight routes")
        print(f"📊 Export your routes as JSON files")
        
        return map_file
        
    except Exception as e:
        print(f"❌ Error creating route builder: {e}")
        return None


if __name__ == "__main__":
    create_route_builder_demo()