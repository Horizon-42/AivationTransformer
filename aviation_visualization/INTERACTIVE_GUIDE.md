# Interactive Route Builder - User Guide

## 🎯 Overview

The Interactive Route Builder is an advanced feature that lets you create custom flight routes by clicking on Canadian weather stations directly on the map. Perfect for flight planning, weather analysis, and route optimization!

## 🚀 Getting Started

### Quick Start
```python
from aviation_visualization import InteractiveRouteBuilder
from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository

# Create interactive route builder
repo = SQLiteWeatherRepository("weather_data/weather.db") 
builder = InteractiveRouteBuilder(repo)
map_file = builder.save_interactive_map("my_route_builder.html")

# Open the HTML file in your browser!
```

### Run Demo
```bash
python3 interactive_route_example.py
```

## 🗺️ How to Use

### 1. **Add Stations to Route**
- Click on any blue airplane marker (✈) on the map
- Stations are added to your route in the order you click them
- Each station shows up in the route list with a number

### 2. **Manage Your Route**
- **View Route**: Check the route panel on the right side
- **Remove Station**: Click the ✕ button next to any station
- **Clear All**: Use the "Clear Route" button to start over
- **See Distance**: Automatic calculation of total route distance

### 3. **Export Your Route**
- Click "Export Route" to download a JSON file
- Contains station codes, coordinates, and route metadata
- Perfect for importing into flight planning software

## ✈️ Available Airports

The route builder includes 17 major Canadian airports:

| Code | Airport | Province |
|------|---------|----------|
| CYYZ | Toronto Pearson | ON |
| CYVR | Vancouver International | BC |
| CYUL | Montreal Trudeau | QC |
| CYYC | Calgary International | AB |
| CYOW | Ottawa Macdonald-Cartier | ON |
| CYWG | Winnipeg Richardson | MB |
| CYEG | Edmonton International | AB |
| CYHZ | Halifax Stanfield | NS |
| CYQB | Quebec City Jean Lesage | QC |
| CYXE | Saskatoon John G Diefenbaker | SK |
| CYQR | Regina International | SK |
| CYYJ | Victoria International | BC |
| CYYT | St. John's International | NL |
| CYFC | Fredericton International | NB |
| CYZF | Yellowknife | NT |
| CYFS | Fort Simpson | NT |
| CYQA | Muskoka | ON |

## 🎨 Map Features

### Visual Elements
- **Blue Airplane Icons (✈)**: Clickable weather stations
- **Orange Route Line**: Your custom flight path
- **Numbered Waypoints**: Show route order
- **Interactive Popups**: Click markers for station details

### Control Panel Features
- **Current Route List**: Shows all selected stations in order
- **Distance Calculation**: Real-time route distance in kilometers
- **Station Management**: Add/remove individual stations
- **Route Export**: Download route as JSON file

### Map Controls
- **Zoom**: Mouse wheel or map controls
- **Pan**: Click and drag to move around
- **Station Info**: Click any marker for airport details

## 📊 Example Routes

### Transcontinental Route
1. CYVR (Vancouver) → CYEG (Edmonton) → CYWG (Winnipeg) → CYYZ (Toronto)
2. Total Distance: ~2,847 km
3. Great for cross-country flight planning

### Maritime Tour  
1. CYHZ (Halifax) → CYFC (Fredericton) → CYYT (St. John's)
2. Total Distance: ~1,234 km
3. Perfect for East Coast flying

### Prairie Circuit
1. CYYC (Calgary) → CYXE (Saskatoon) → CYQR (Regina) → CYWG (Winnipeg)
2. Total Distance: ~1,456 km
3. Ideal for prairie province tours

## 💾 Exported Route Format

When you export a route, you get a JSON file like this:

```json
{
  "route": ["CYVR", "CYEG", "CYWG", "CYYZ"],
  "distance": 2847,
  "waypoints": [
    {
      "code": "CYVR",
      "lat": 49.1967,
      "lon": -123.1815,
      "name": "Vancouver Intl",
      "order": 1
    },
    // ... more waypoints
  ]
}
```

## 🔧 Technical Details

### Browser Compatibility
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- No plugins required - pure HTML/CSS/JavaScript
- Offline capable once loaded

### Performance
- Optimized for 17 major airports
- Real-time route updates
- Efficient distance calculations using Haversine formula
- Responsive design for desktop and tablet

### Integration
- Seamlessly integrates with aviation_visualization package
- Uses same weather data as other mapping tools
- Compatible with existing SQLite weather database

## 🎯 Use Cases

### Flight Planning
- Plan VFR routes between airports
- Check weather along your route
- Calculate approximate flight distances
- Export routes for GPS or flight planning apps

### Weather Analysis  
- Analyze weather patterns across regions
- Compare conditions at multiple airports
- Plan routes to avoid poor weather

### Training & Education
- Learn Canadian airport locations
- Practice flight planning skills
- Understand geographic relationships between airports

### Route Optimization
- Find efficient paths between airports
- Minimize flight time and fuel consumption
- Plan fuel stops for longer routes

---

**🎉 Happy Flight Planning!** Open any generated HTML file in your browser and start building custom routes with real-time Canadian weather data!