import json
from METAR_convert.upper_wind import UpperWind

# Load the raw bulletin from the parsed JSON file (should be the raw string, not already parsed)
with open('METAR_convert/weather_data/canada_group_01_parsed.json', 'r') as f:
    data = json.load(f)

# Try to find a bulletin string in the loaded data
# (Assume the structure is similar to the example in upper_wind.py docstring)
bulletins = []
if isinstance(data, dict):
    # Try to find a list of bulletins
    if 'weather_data' in data and 'Upper_Wind' in data['weather_data']:
        for entry in data['weather_data']['Upper_Wind']:
            if 'bulletin' in entry:
                bulletins.append(entry['bulletin'])
    elif 'bulletin' in data:
        bulletins.append(data['bulletin'])
    else:
        # Try to treat the whole dict as a bulletin
        bulletins.append(str(data))
elif isinstance(data, list):
    for entry in data:
        if isinstance(entry, dict) and 'bulletin' in entry:
            bulletins.append(entry['bulletin'])
        else:
            bulletins.append(str(entry))
else:
    bulletins.append(str(data))

for idx, bulletin in enumerate(bulletins, 1):
    print(f"\n=== Bulletin #{idx} ===\n{bulletin}\n")
    winds = UpperWind.parse_bulletin_all_stations(bulletin)
    for uw in winds:
        print(f"Station: {uw.station}")
        for p in uw.periods:
            print(f"  Period: {p.valid_time} {p.use_period}")
            for lvl in p.levels:
                print(f"    Alt: {lvl.altitude_ft} Dir: {lvl.direction_deg} Spd: {lvl.speed_kt} Temp: {lvl.temperature_c}")
    print()
