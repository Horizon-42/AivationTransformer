# Aviation Visualization Package 🛩️🗺️

Interactive map visualization package for Canadian aviation weather data using **Folium** and **Leaflet.js**.

## 📦 Package Structure

```
aviation_visualization/
├── __init__.py              # Package exports and metadata
├── weather_map.py           # Core AviationWeatherMap class
├── map_generator.py         # High-level MapGenerator utilities
├── demo.py                 # Usage examples and demos
├── requirements.txt        # Package dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### Basic Usage

```python
from aviation_visualization import MapGenerator
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

# Initialize
repo = SQLiteWeatherRepository("weather_data/weather.db")
generator = MapGenerator(repo)

# Generate a regional map
ontario_map = generator.create_regional_map('ontario')
ontario_map.save_map("ontario_weather.html")

# Generate all demo maps
generator.generate_all_demo_maps("output")

repo.close()
```

### Run Demo

```bash
cd aviation_visualization
python3 demo.py
```

## 🏗️ Architecture

### Two-Level API

1. **High-Level: `MapGenerator`** - Easy map creation with presets
2. **Low-Level: `AviationWeatherMap`** - Full control over map features

### Classes

#### `MapGenerator`
- **Purpose**: High-level map generation with predefined regions and routes
- **Best for**: Quick map creation, standard aviation scenarios
- **Methods**:
  - `create_regional_map()` - Ontario, Atlantic, Prairie, West Coast
  - `create_route_map()` - Predefined flight routes  
  - `create_custom_map()` - Custom stations and routes
  - `generate_all_demo_maps()` - Complete demo set

#### `AviationWeatherMap`
- **Purpose**: Core mapping functionality with full customization
- **Best for**: Advanced users, custom requirements
- **Methods**:
  - `create_base_map()` - Initialize map canvas
  - `add_weather_stations()` - Plot weather data
  - `add_flight_route()` - Draw routes between airports
  - `add_legend()` - Flight category legend
  - `save_map()` - Export to HTML

## 🗺️ Predefined Regions

| Region | Airports | Center | Description |
|--------|----------|--------|-------------|
| `ontario` | CYYZ, CYTZ, CYHM, etc. | Toronto | Greater Toronto Area |
| `atlantic` | CYHZ, CYSJ, CYQX, etc. | Halifax | Atlantic provinces |
| `prairie` | CYWG, CYQR, CYXE, etc. | Saskatoon | Prairie provinces |
| `west_coast` | CYVR, CYYJ, CYCD, etc. | Vancouver | BC coast |
| `major_canadian` | All major airports | Canada center | National overview |

## ✈️ Predefined Routes

| Route | Airports | Description |
|-------|----------|-------------|
| `transcontinental` | CYVR→CYYC→CYWG→CYYZ→CYUL | Coast to coast |
| `eastern_corridor` | CYYZ→CYOW→CYUL→CYQB→CYHZ | Eastern Canada |
| `prairie_circuit` | CYWG→CYQR→CYXE→CYEG→CYYC | Prairie loop |
| `atlantic_tour` | CYHZ→CYSJ→CYQX→CYYT | Maritime provinces |

## 🎨 Map Features

### Weather Station Markers
- **Color-coded by flight category**:
  - 🟢 **VFR** - Visibility ≥8km, ceiling ≥3000ft
  - 🟡 **MVFR** - Visibility 5-8km, ceiling 1000-3000ft
  - 🔴 **IFR** - Visibility 1.6-5km, ceiling 500-1000ft
  - 🔴 **LIFR** - Visibility <1.6km, ceiling <500ft
  - ⚪ **Unknown** - No recent data

- **Size by airport importance**:
  - Large: Major airports (CYYZ, CYVR, etc.)
  - Medium: Regional airports
  - Small: Minor weather stations

### Interactive Features
- **🔍 Zoom/Pan** - Mouse wheel, click-drag
- **💬 Popups** - Click stations for detailed weather
- **🗂️ Layer Control** - Switch map styles (light/dark)
- **📊 Legend** - Flight category explanation
- **📱 Mobile-friendly** - Works on all devices

### Flight Routes
- **Colored lines** connecting airports in sequence
- **Waypoint markers** with current weather info
- **Multiple routes** can be displayed simultaneously
- **Customizable** colors, weights, and names

## 📊 Usage Examples

### Example 1: Flight Planning

```python
# Plan a cross-country flight
generator = MapGenerator(repo)

# Get weather along route
route_stations = ['CYVR', 'CYYC', 'CYWG', 'CYYZ']
flight_map = generator.create_custom_map(
    stations=route_stations,
    routes=[{
        'stations': route_stations,
        'name': 'My Flight Plan',
        'color': '#ff6b6b',
        'weight': 4
    }],
    center=[52.0, -100.0],
    zoom=4
)
flight_map.save_map("flight_plan.html")
```

### Example 2: Regional Weather Analysis

```python
# Monitor weather in specific region
weather_map = AviationWeatherMap(repo)
weather_map.create_base_map(center=[43.6, -79.4], zoom=7)

# Add Toronto area airports
toronto_airports = ['CYYZ', 'CYTZ', 'CYHM', 'CYKZ']
weather_map.add_weather_stations(
    time_hours=2,  # Last 2 hours
    station_ids=toronto_airports
)

weather_map.add_legend()
weather_map.save_map("toronto_region.html")
```

### Example 3: Multiple Routes

```python
# Compare different route options
generator = MapGenerator(repo)
eastern_map = generator.create_regional_map('major_canadian')

# Add multiple route options
routes = [
    generator.flight_routes['transcontinental'],
    generator.flight_routes['eastern_corridor'],
    generator.flight_routes['prairie_circuit']
]

for route in routes:
    eastern_map.add_flight_route(
        route['stations'], 
        route['name'], 
        route['color']
    )

eastern_map.save_map("route_comparison.html")
```

## 🔧 Advanced Customization

### Custom Weather Station Classification

```python
class CustomWeatherMap(AviationWeatherMap):
    def classify_station(self, station_id: str) -> str:
        # Your custom logic here
        if station_id.startswith('CY'):
            return 'major'
        return 'minor'
```

### Custom Flight Categories

```python
weather_map = AviationWeatherMap(repo)

# Override default colors
weather_map.flight_category_colors = {
    'VFR': '#00ff00',     # Bright green
    'MVFR': '#ffff00',    # Yellow
    'IFR': '#ff8800',     # Orange
    'LIFR': '#ff0000',    # Red
    'UNKNOWN': '#808080'  # Gray
}
```

### Custom Map Styles

```python
import folium

weather_map = AviationWeatherMap(repo)
weather_map.create_base_map()

# Add custom tile layers
folium.TileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Satellite',
    overlay=False,
    control=True
).add_to(weather_map.map)
```

## 🛠️ Integration with Main Project

### With High-Level API

```python
from aviation_visualization import MapGenerator
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

# Use your existing repository
repo = SQLiteWeatherRepository("weather_data/weather.db")

# Get weather data using high-level API
weather_data = repo.query_weather_by_region(
    min_latitude=43.0,
    max_latitude=44.3,
    min_longitude=-80.0,
    max_longitude=-78.7
)

# Extract station IDs
station_ids = [sid for sid in weather_data.keys() if sid != '_sigmets']

# Create visualization
generator = MapGenerator(repo)
map_obj = generator.create_custom_map(
    stations=station_ids,
    center=[43.6, -79.4],
    zoom=7
)
map_obj.save_map("region_weather.html")
```

## Generated Maps

The maps are automatically saved in the `maps/` subdirectory within this package as standalone HTML files that can be opened in any web browser.

## Example Usage

## 🎯 Performance Tips

1. **Limit time range** - Use `time_hours` parameter to control data volume
2. **Specific stations** - Use `station_ids` to limit scope
3. **Batch generation** - Use `generate_all_demo_maps()` for multiple maps
4. **Map complexity** - Too many routes/stations can slow rendering

## 🔮 Future Enhancements

Potential additions to the package:

- **Weather overlays** - Precipitation radar, satellite imagery
- **Time animation** - Show weather changes over time
- **Export formats** - PNG, PDF, SVG output
- **Real-time updates** - Auto-refresh capabilities
- **Advanced filtering** - Filter by conditions, aircraft types
- **3D visualization** - Terrain and altitude awareness

## 📂 File Output

Generated maps are standalone HTML files that:
- ✅ Work offline (no internet required after loading)
- ✅ Include all JavaScript, CSS, and map data
- ✅ Are mobile-responsive
- ✅ Can be shared easily
- ✅ Load quickly (optimized file size)

---

**🎉 Ready to visualize Canadian aviation weather data!** 

Open any generated `.html` file in your browser to explore interactive weather maps.