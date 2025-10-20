"""
Nav Canada Weather Server Examples

This script demonstrates how to use the NavCanadaWeatherServer to:
- Query Nav Canada for weather data
- Get parsed METAR, TAF, and Upper Wind objects
- Save intermediate JSON files
- Export parsed data to JSON
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from navcanada_weather_server import NavCanadaWeatherServer


def example_get_all_weather():
    """Example: Get all weather data (METAR, TAF, Upper Winds) for a station"""
    print("\n" + "="*70)
    print("📋 Example 1: Get All Weather Data for CYVR")
    print("="*70)
    
    # Initialize server
    server = NavCanadaWeatherServer(headless=True, timeout=30)
    
    try:
        # Get all weather data
        response = server.get_weather(
            station_ids='CYVR',
            save_raw_data=True,
            raw_data_filename='test_cyvr_all_weather.json'
        )
        
        print("\n📊 Retrieved Data:")
        print(f"  • Raw data saved to: {response.raw_data_file}")
        
        # Display METAR data
        if response.metars:
            print(f"\n🌤️  METAR Data:")
            for station, metars in response.metars.items():
                print(f"\n  Station: {station}")
                for i, metar in enumerate(metars, 1):
                    print(f"    METAR #{i}:")
                    print(f"      Time: {metar.observation_time}")
                    print(f"      Temperature: {metar.temperature_celsius}°C ({metar.temperature_fahrenheit}°F)")
                    print(f"      Dewpoint: {metar.dewpoint_celsius}°C")
                    print(f"      Wind: {metar.wind_direction_degrees}° at {metar.wind_speed_knots}kt")
                    print(f"      Visibility: {metar.visibility}")
                    print(f"      Sky: {metar.sky_coverage}")
                    print(f"      Altimeter: {metar.altimeter_hpa:.1f} hPa")
                    print(f"      Flight Category: {metar.flight_category}")
        
        # Display TAF data
        if response.tafs:
            print(f"\n📅 TAF Data:")
            for station, tafs in response.tafs.items():
                print(f"\n  Station: {station}")
                for i, taf in enumerate(tafs, 1):
                    print(f"    TAF #{i}:")
                    print(f"      Issued: {taf.issue_time}")
                    print(f"      Valid: {taf.valid_time_from} to {taf.valid_time_to}")
                    print(f"      Forecast Periods: {len(taf.forecast_periods)}")
                    
                    # Show change periods
                    for period in taf.forecast_periods[:3]:  # Show first 3
                        print(f"        • {period.get('type', 'BASE')}: {period.get('time_from', 'N/A')} - {period.get('time_to', 'N/A')}")
        
        # Display Upper Wind data
        if response.upper_winds:
            print(f"\n🌬️  Upper Wind Data:")
            for i, wind in enumerate(response.upper_winds, 1):
                print(f"    Report #{i}:")
                print(f"      Valid: {wind.valid_time}")
                print(f"      Based on: {wind.data_based_on}")
                print(f"      Stations: {len(wind.station_data)}")
                
                # Show sample station data
                if wind.station_data:
                    sample_station = list(wind.station_data.keys())[0]
                    sample_data = wind.station_data[sample_station]
                    print(f"      Sample ({sample_station}):")
                    for alt, data in list(sample_data.items())[:2]:  # Show first 2 altitudes
                        print(f"        {alt}: {data}")

        # Display station-wise parsed Upper Wind mapping if available
        if getattr(response, 'parsed_upper_winds_by_station', None):
            keys = list(response.parsed_upper_winds_by_station.keys())
            print(
                f"\n📍 Upper Wind by Station (parsed): {len(keys)} station(s)")
            print(
                f"   Keys: {', '.join(keys[:10])}{' ...' if len(keys) > 10 else ''}")

        # Export to JSON
        print("\n💾 Exporting parsed data...")
        export_file = server.export_to_json(response, 'test_cyvr_parsed.json')
        print(f"  ✅ Exported to: {export_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def example_get_metar_only():
    """Example: Get only METAR data for multiple stations"""
    print("\n" + "="*70)
    print("📋 Example 2: Get METAR Only for Multiple Stations")
    print("="*70)
    
    server = NavCanadaWeatherServer(headless=True)
    
    try:
        # Get METAR data only
        metars = server.get_metar(
            station_ids=['CYVR', 'CYYC'],  # Vancouver and Calgary
            save_raw_data=True,
            raw_data_filename='test_multi_station_metar.json'
        )
        
        print(f"\n📊 Retrieved METARs for {len(metars)} stations:")
        
        for station, metar_list in metars.items():
            print(f"\n🌤️  {station}:")
            for metar in metar_list:
                print(f"  • Observation: {metar.observation_time}")
                print(f"    Temp: {metar.temperature_celsius}°C, Wind: {metar.wind_speed_knots}kt")
                print(f"    Visibility: {metar.visibility}, Sky: {metar.sky_coverage}")
                print(f"    Flight Category: {metar.flight_category}")
                
                # Check conditions
                if metar.is_vfr():
                    print(f"    ✅ VFR conditions")
                elif metar.is_ifr():
                    print(f"    ⚠️ IFR conditions")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def example_get_taf_only():
    """Example: Get only TAF data"""
    print("\n" + "="*70)
    print("📋 Example 3: Get TAF Only")
    print("="*70)
    
    server = NavCanadaWeatherServer(headless=True)
    
    try:
        # Get TAF data only
        tafs = server.get_taf(
            station_ids=['CYVR', 'CYYC'],
            save_raw_data=True,
            raw_data_filename='test_multi_station_taf.json'
        )
        
        print(f"\n📊 Retrieved TAFs for {len(tafs)} stations:")
        
        for station, taf_list in tafs.items():
            print(f"\n📅 {station}:")
            for taf in taf_list:
                print(f"  • Issued: {taf.issue_time}")
                print(f"    Valid: {taf.valid_time_from} to {taf.valid_time_to}")
                print(f"    Forecast contains {len(taf.forecast_periods)} period(s)")
                
                # Show change indicators
                change_types = [p.get('type', 'BASE') for p in taf.forecast_periods]
                if any(t in ['TEMPO', 'BECMG', 'PROB'] for t in change_types):
                    print(f"    Change types: {', '.join(set(change_types))}")
                
                # Check for adverse conditions
                raw_taf = taf.raw_taf_text or ""
                adverse = []
                if 'TS' in raw_taf:
                    adverse.append('Thunderstorms')
                if 'FG' in raw_taf or 'BR' in raw_taf:
                    adverse.append('Fog/Mist')
                if 'SN' in raw_taf:
                    adverse.append('Snow')
                
                if adverse:
                    print(f"    ⚠️ Adverse weather: {', '.join(adverse)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def example_get_upper_winds():
    """Example: Get upper wind data"""
    print("\n" + "="*70)
    print("📋 Example 4: Get Upper Winds")
    print("="*70)
    
    server = NavCanadaWeatherServer(headless=True)
    
    try:
        # Get upper wind data
        upper_winds = server.get_upper_winds(
            station_ids=['CYVR'],  # Upper winds typically cover a region
            save_raw_data=True,
            raw_data_filename='test_upper_winds.json'
        )
        
        print(f"\n📊 Retrieved {len(upper_winds)} upper wind report(s):")
        
        for i, wind in enumerate(upper_winds, 1):
            print(f"\n🌬️  Report #{i}:")
            print(f"  • Valid Time: {wind.valid_time}")
            print(f"  • Data Based On: {wind.data_based_on}")
            print(f"  • Covers {len(wind.station_data)} station(s)")
            
            # Show stations covered
            stations = list(wind.station_data.keys())
            print(f"  • Stations: {', '.join(stations[:5])}")  # Show first 5
            if len(stations) > 5:
                print(f"    ... and {len(stations) - 5} more")
            
            # Find strong winds (>50 knots)
            strong_winds = []
            for station, altitudes in wind.station_data.items():
                for altitude, data in altitudes.items():
                    if 'wind' in data:
                        try:
                            wind_speed = int(data['wind'].split('/')[1][:2])
                            if wind_speed > 50:
                                strong_winds.append((station, altitude, wind_speed))
                        except:
                            pass
            
            if strong_winds:
                print(f"\n  ⚠️ Strong Winds (>50kt) found:")
                for station, alt, speed in strong_winds[:5]:  # Show first 5
                    print(f"    • {station} at {alt}: {speed}kt")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def example_compare_stations():
    """Example: Compare weather between multiple stations"""
    print("\n" + "="*70)
    print("📋 Example 5: Compare Weather Between Stations")
    print("="*70)
    
    server = NavCanadaWeatherServer(headless=True)
    
    try:
        # Get weather for multiple stations
        response = server.get_weather(
            station_ids=['CYVR', 'CYYC', 'CYYZ'],  # Vancouver, Calgary, Toronto
            save_raw_data=True
        )
        
        print("\n📊 Weather Comparison:")
        print(f"\n{'Station':<10} {'Temp(°C)':<10} {'Wind(kt)':<10} {'Visibility':<12} {'Flight Cat':<12}")
        print("-" * 70)
        
        for station, metars in response.metars.items():
            if metars:
                metar = metars[0]  # Use most recent
                temp = f"{metar.temperature_celsius:.1f}" if metar.temperature_celsius is not None else "N/A"
                wind = f"{metar.wind_speed_knots}" if metar.wind_speed_knots is not None else "N/A"
                vis = metar.visibility or "N/A"
                cat = metar.flight_category or "N/A"
                
                print(f"{station:<10} {temp:<10} {wind:<10} {vis:<12} {cat:<12}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌤️  Nav Canada Weather Server - Test Examples")
    print("="*70)
    print("\nThese examples demonstrate querying Nav Canada and parsing weather objects")
    print("Note: Requires Selenium WebDriver and internet connection")
    print("="*70)
    
    # Run examples
    # Note: Comment out examples you don't want to run to save time
    
    example_get_all_weather()
    # example_get_metar_only()
    # example_get_taf_only()
    # example_get_upper_winds()
    # example_compare_stations()
    
    print("\n" + "="*70)
    print("✅ All examples complete!")
    print("="*70)
