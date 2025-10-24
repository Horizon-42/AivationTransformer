# Aviation Transformer

A comprehensive system for processing and visualizing aviation weather data (METAR/TAF) with interactive mapping capabilities.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Activate your aviation conda environment
conda activate aviation

# Install visualization dependencies
conda install folium -c conda-forge
```

### 2. Simple Example
```python
from aviation_visualization import MapGenerator
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

# Connect to your weather database
repo = SQLiteWeatherRepository("weather_data/weather.db")
generator = MapGenerator(repo)

# Create a regional map with one line!
ontario_map = generator.create_regional_map('ontario')
ontario_map.save_map("my_weather_map.html")
```

### 3. View Your Maps
Maps are saved in `aviation_visualization/maps/` - open any HTML file in your browser (they work offline!)

## 📦 Package Structure

### Core Weather Processing
- `METAR_convert/` - Weather data parsing and storage
  - `metar.py` - METAR weather reports parsing
  - `taf.py` - TAF forecast parsing  
  - `weather_data_server.py` - Data server component
  - `storage/sqlite_repository.py` - Database operations with high-level API

### Interactive Visualization
- `aviation_visualization/` - Interactive mapping package
  - `weather_map.py` - Core mapping functionality
  - `map_generator.py` - High-level map creation utilities
  - `demo.py` - Usage examples

## 🗺️ Map Features

### Interactive Elements
- **Airport Markers**: Click for detailed weather information
- **Flight Routes**: Visualize planned flight paths
- **Flight Categories**: Color-coded by weather conditions
  - 🟢 VFR (Visual Flight Rules) - Good weather
  - 🟡 MVFR (Marginal VFR) - Moderate conditions  
  - 🔴 IFR (Instrument Flight Rules) - Poor weather
  - ⚫ LIFR (Low IFR) - Very poor conditions

### Pre-configured Regions
- **Ontario**: GTA and southern Ontario airports
- **Quebec**: Major Quebec airports including Montreal
- **Maritimes**: Atlantic Canada airports
- **Prairies**: Alberta, Saskatchewan, Manitoba
- **West Coast**: British Columbia airports

### Sample Flight Routes
- **Transcontinental**: Vancouver to Halifax
- **Central Canada**: Toronto to Winnipeg  
- **East Coast**: Montreal to St. John's

## 🛠️ Usage Examples

### Run Demo Scripts
```bash
# Package demos (creates multiple maps)
python3 aviation_visualization/demo.py

# Simple examples  
python3 example_usage.py
```

### High-Level API (Recommended)
```python
# Regional map
ontario_map = generator.create_regional_map('ontario', time_hours=6)

# Flight route map
route_map = generator.create_route_map('transcontinental')

# Custom map
custom_map = generator.create_custom_map(
    stations=['CYYZ', 'CYVR'], 
    routes=[{'stations': ['CYYZ', 'CYVR'], 'name': 'Toronto-Vancouver'}]
)
```

### Low-Level API (Advanced)
```python
# Direct control over map creation
weather_map = AviationWeatherMap()
weather_map.create_base_map(center_lat=43.6532, center_lon=-79.3832, zoom=6)
weather_map.add_weather_stations(repo, ['CYYZ', 'CYOW'])
weather_map.add_flight_route(['CYYZ', 'CYOW'], 'Toronto-Ottawa', '#blue')
```

## 📊 Database API

### Query Weather Data
```python
# Get recent weather for specific stations
weather_data = repo.query_weather_data(
    station_codes=['CYYZ', 'CYVR'],
    hours_back=6
)

# Get weather within geographic region  
regional_data = repo.query_weather_by_region(
    min_lat=43.0, max_lat=45.0,
    min_lon=-81.0, max_lon=-79.0,
    hours_back=3
)
```

## 🎯 Key Features

1. **Standardized Aviation Data**: Supports METAR, TAF formats per ICAO/WMO standards
2. **Interactive Maps**: Web-based maps using Leaflet.js (via Folium)
3. **Flight Planning**: Visualize routes with weather conditions
4. **Offline Capable**: Generated HTML maps work without internet
5. **Professional Package Structure**: Well-organized, reusable code
6. **High-Level API**: Easy-to-use functions for common tasks
7. **Extensible Design**: Add custom visualizations easily

## 📝 Documentation

See the `docs/` folder for aviation standards references:
- WMO Manual on Codes (weather format specifications)
- ICAO Annex 3 (meteorological standards)
- FAA Weather Handbook
- NASA aviation weather research

## 🛩️ Airport Codes Reference

Canadian airports use 4-letter ICAO codes:
- **CYYZ**: Toronto Pearson
- **CYVR**: Vancouver International  
- **CYUL**: Montreal Trudeau
- **CYYC**: Calgary International
- **CYOW**: Ottawa Macdonald-Cartier

## 📈 Next Steps

Generated maps include:
- Weather station markers with current conditions
- Flight route visualization
- Interactive popups with detailed weather data
- Automatic flight category color coding
- Professional cartography styling

All maps are organized in `aviation_visualization/maps/` - open any `.html` file in your browser to explore!

---

*Built for aviation professionals, weather enthusiasts, and flight planning applications.*