# ✈️ Aviation Transformer

A modern system for processing and visualizing aviation weather data (METAR/TAF) with advanced 3D interactive mapping capabilities.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Activate your aviation conda environment
conda activate aviation

# Install modern visualization dependencies (already installed)
conda install streamlit pydeck -c conda-forge
```

### 2. Launch Interactive Application
```bash
# 🆕 Launch the Advanced Streamlit App (One Command!)
python3 launch_aviation_app.py

# Access at: http://localhost:8502
```

### 3. Instant Features
- **2D/3D Map Toggle**: Switch between views instantly
- **Real-time Weather**: Hover over stations for METAR data
- **Interactive Routes**: Click to build flight paths
- **5 Map Styles**: Satellite, Streets, Light, Dark, Outdoors

## 📦 Package Structure

### Core Weather Processing
- `METAR_convert/` - Weather data parsing and storage
  - `metar.py` - METAR weather reports parsing
  - `taf.py` - TAF forecast parsing  
  - `weather_data_server.py` - Data server component
  - `storage/sqlite_repository.py` - Database operations with high-level API

### 🆕 Modern Interactive Visualization
- `aviation_visualization/` - Advanced real-time mapping package
  - `streamlit_app.py` - **Complete Streamlit + PyDeck application**
  - `STREAMLIT_GUIDE.md` - Detailed user guide
  - `UPGRADE_COMPARISON.md` - Technical comparison with legacy approaches
- `launch_aviation_app.py` - One-click application launcher
- `old_demos/` - Legacy Folium-based approaches (archived)

## 🗺️ Advanced Map Features

### ⚡ **Real-time Interactive Experience**
- **🔄 2D/3D Views**: Instant switching between 2D and immersive 3D maps
- **🎨 5 Map Styles**: Satellite, Streets, Light, Dark, Outdoors themes
- **📡 Live Weather Stations**: All database stations with toggle control
- **✈️ Smart Route Planning**: Click stations to build validated flight paths
- **🌤️ Hover Weather Info**: Complete METAR data on mouse hover
- **⚡ Zero-latency Response**: True Python-native interactions
- **📏 Automatic Calculations**: Distance and flight time estimates

### 🌟 **Professional Flight Categories**
Weather stations color-coded by flight conditions:
- **🟢 VFR** (Visual Flight Rules) - Clear conditions, excellent visibility
- **🟡 MVFR** (Marginal VFR) - Moderate conditions, some restrictions
- **🔴 IFR** (Instrument Flight Rules) - Poor weather, instruments required
- **⚫ LIFR** (Low IFR) - Very poor conditions, minimal visibility

### 🎯 **Smart Route Validation**
- **Station Validation**: Start and end points must be weather stations
- **Mixed Routes**: Intermediate points can be any map location
- **Distance Calculations**: Accurate great-circle distance calculations
- **Flight Time Estimates**: Based on typical general aviation cruise speeds
- **Visual Feedback**: Real-time route updates and validation messages

## � Usage

### **One-Click Launch** (Recommended)
```bash
# Launch the complete interactive application
python3 launch_aviation_app.py

# Automatically opens browser at: http://localhost:8502
```

### **Python API Integration**
```python
# Use in your own Python applications
from aviation_visualization import AdvancedAviationApp
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

# Connect to weather database
repo = SQLiteWeatherRepository("weather_data/weather.db")

# Launch interactive app programmatically
app = AdvancedAviationApp()
app.run()
```

### **Access Real-time Data**
The application automatically connects to your weather database and provides:
- Live weather station data with METAR parsing
- Automatic flight category classification
- Smart caching for optimal performance
- Real-time route validation and distance calculation

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

1. **🌐 Real-time 3D Visualization**: Advanced WebGL-based maps with instant 2D/3D switching
2. **📊 Live Aviation Data**: Direct database integration with METAR/TAF parsing per ICAO standards
3. **✈️ Interactive Flight Planning**: Click-to-build routes with professional validation
4. **⚡ Zero-latency Performance**: Native Python interactions, no page refreshes needed
5. **🎨 Professional Interface**: Multiple themes, responsive design, aviation-grade UX
6. **📈 Smart Caching**: Multi-level performance optimization for real-time responsiveness
7. **🛠️ Modern Architecture**: Streamlit + PyDeck technology stack for maximum reliability

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

## 🎉 Ready to Fly!

Your aviation visualization system includes:

### 🛩️ **Complete Application**
- **Streamlit Interface**: Professional web application at `http://localhost:8502`
- **3D Weather Visualization**: Real-time interactive maps with aviation-specific features
- **Route Planning**: Professional flight path building with validation
- **Live Data Integration**: Direct connection to your weather database

### 📚 **Documentation & Support**
- `aviation_visualization/STREAMLIT_GUIDE.md` - Complete user guide
- `aviation_visualization/UPGRADE_COMPARISON.md` - Technical overview
- `docs/` - Aviation standards and specifications

### 🚀 **Next Steps**
1. **Launch**: `python3 launch_aviation_app.py`
2. **Explore**: Use the sidebar controls to customize your view
3. **Plan Routes**: Click weather stations to build flight paths
4. **Check Weather**: Hover over stations for real-time METAR data

---

**🎯 Built for aviation professionals, flight training, weather monitoring, and research applications.**

*Experience the future of aviation weather visualization with real-time 3D mapping!* ✈️🌤️