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
- `aviation_visualization/` - Advanced interactive mapping package
  - `streamlit_app.py` - 🆕 **Advanced Streamlit + PyDeck application**
  - `weather_map.py` - Core Folium mapping functionality (legacy)
  - `map_generator.py` - High-level map creation utilities
  - `interactive_route_builder.py` - HTML interactive route planning tool
  - `demo.py` - Usage examples

## 🗺️ Map Features

### 🆕 **Advanced Interactive Features**
- **2D/3D Map Views**: Real-time switching between 2D and 3D visualization modes
- **Multiple Map Styles**: Satellite, light, dark, streets, and outdoors themes
- **Real-time Weather Display**: All database weather stations with hover information
- **Smart Route Planning**: Click-to-add stations with validation (start/end must be stations)
- **Live Weather Data**: Mouse hover shows latest METAR data from database
- **Performance Optimization**: Smart caching and responsive design
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

### Pre-configured Flight Routes
- **Transcontinental**: Vancouver to Halifax
- **Central Canada**: Toronto to Winnipeg  
- **East Coast**: Montreal to St. John's

### Interactive Route Builder
- **Click-to-Build**: Click any weather station to add to your route
- **Dynamic Updates**: Route line updates in real-time as you add stations
- **Route Management**: Remove individual stations or clear entire route
- **Distance Calculation**: Automatic route distance calculation
- **Export Functionality**: Save custom routes as JSON files
- **17 Major Airports**: All major Canadian airports available for route building

## 🛠️ Usage Examples

### 🚀 **Launch the Advanced Visualization App**
```bash
# 🆕 New Advanced Streamlit Application (Recommended)
# Auto-launches in browser with full interactive features
python3 launch_aviation_app.py

# Or run directly with conda environment
/path/to/conda/envs/aviation/bin/python -m streamlit run aviation_visualization/streamlit_app.py

# Access at: http://localhost:8502
```

### 📊 **Legacy Demo Scripts** (Still Available)
```bash
# Folium-based demos (HTML output)
python3 aviation_visualization/demo.py
python3 example_usage.py  
python3 interactive_route_example.py
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