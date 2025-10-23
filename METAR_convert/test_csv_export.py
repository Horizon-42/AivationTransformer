"""
Test script for CSV export functionality

This script tests the CSV exporter using existing parsed JSON files
to validate attribute names and data structure handling.
"""

import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from station_lookup import enrich_weather_data
from csv_exporter import WeatherDataCSVExporter
from metar import METAR, CloudLayer
from taf import TAF, TAFCloudLayer, TAFForecastPeriod, IcingTurbulence, TemperatureForecast
from upper_wind import UpperWind, UpperWindPeriod, UpperWindLevel
from sigmet import parse_sigmet_text


def run_csv_export_from_json():
    """Run CSV export smoke-test using an existing parsed JSON file"""
    
    # Find an existing parsed JSON file
    weather_data_dir = Path("weather_data")
    json_files = list(weather_data_dir.glob("canada_group_*_parsed.json"))
    
    if not json_files:
        print("❌ No parsed JSON files found in weather_data/")
        print("   Please run the main query script first to generate test data.")
        return False
    
    # Use the first available file
    test_file = json_files[0]
    print(f"📂 Testing with: {test_file.name}")
    
    try:
        # Load the JSON file
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"   Loaded JSON with {len(data.get('metars', {}))} METAR stations")
        print(f"   Loaded JSON with {len(data.get('tafs', {}))} TAF stations")
        print(f"   Loaded JSON with {len(data.get('upper_winds', []))} Upper Wind objects")
        
        # Parse METARs
        metars_dict = {}
        for station_id, metar_list in data.get('metars', {}).items():
            metars_dict[station_id] = []
            for metar_data in metar_list:
                try:
                    # Reconstruct METAR object
                    metar = METAR(
                        station_id=metar_data['station_id'],
                        station_name=metar_data['station_name'],
                        latitude=metar_data['latitude'],
                        longitude=metar_data['longitude'],
                        elevation_meters=metar_data['elevation_meters'],
                        observation_time=datetime.fromisoformat(metar_data['observation_time']),
                        receipt_time=datetime.fromisoformat(metar_data['receipt_time']),
                        observation_timestamp=metar_data['observation_timestamp'],
                        temperature_celsius=metar_data['temperature_celsius'],
                        dewpoint_celsius=metar_data['dewpoint_celsius'],
                        wind_direction_degrees=metar_data.get('wind_direction_degrees'),
                        wind_speed_knots=metar_data.get('wind_speed_knots'),
                        wind_gust_knots=metar_data.get('wind_gust_knots'),
                        wind_variable=metar_data.get('wind_variable', False),
                        visibility=metar_data.get('visibility', '10+'),
                        visibility_meters=metar_data.get('visibility_meters'),
                        altimeter_hpa=metar_data.get('altimeter_hpa', 0.0),
                        sea_level_pressure_hpa=metar_data.get('sea_level_pressure_hpa'),
                        pressure_tendency_hpa=metar_data.get('pressure_tendency_hpa'),
                        sky_coverage=metar_data.get('sky_coverage', 'CLR'),
                        cloud_layers=[
                            CloudLayer(
                                coverage=layer['coverage'],
                                altitude_feet=layer.get('altitude_feet'),
                                cloud_type=layer.get('cloud_type')
                            )
                            for layer in metar_data.get('cloud_layers', [])
                        ],
                        flight_category=metar_data.get('flight_category', 'VFR'),
                        max_temperature_celsius=metar_data.get('max_temperature_celsius'),
                        min_temperature_celsius=metar_data.get('min_temperature_celsius'),
                        present_weather=metar_data.get('present_weather', []),
                        quality_control_field=metar_data.get('quality_control_field'),
                        report_type=metar_data.get('report_type', 'METAR'),
                        raw_observation=metar_data.get('raw_observation', '')
                    )
                    metars_dict[station_id].append(metar)
                except Exception as e:
                    print(f"   ⚠️  Error parsing METAR for {station_id}: {e}")
                    continue
        
        # Parse TAFs
        tafs_dict = {}
        for station_id, taf_list in data.get('tafs', {}).items():
            tafs_dict[station_id] = []
            for taf_data in taf_list:
                try:
                    # Parse forecast periods
                    forecast_periods = []
                    for period_data in taf_data.get('forecast_periods', []):
                        # Parse cloud layers for this period
                        cloud_layers = []
                        for layer_data in period_data.get('cloud_layers', []):
                            layer = TAFCloudLayer(
                                coverage=layer_data['coverage'],
                                base_altitude_feet=layer_data.get('base_altitude_feet'),
                                cloud_type=layer_data.get('cloud_type')
                            )
                            cloud_layers.append(layer)
                        
                        # Parse icing/turbulence
                        icing_turb = []
                        for it_data in period_data.get('icing_turbulence', []):
                            it = IcingTurbulence(
                                intensity=it_data.get('intensity'),
                                type=it_data.get('type'),
                                base_altitude_feet=it_data.get('base_altitude_feet'),
                                top_altitude_feet=it_data.get('top_altitude_feet')
                            )
                            icing_turb.append(it)
                        
                        # Parse temperature forecasts
                        temp_forecasts = []
                        for tf_data in period_data.get('temperature_forecasts', []):
                            tf = TemperatureForecast(
                                temperature_celsius=tf_data.get('temperature_celsius'),
                                time=datetime.fromisoformat(tf_data['time']) if tf_data.get('time') else None
                            )
                            temp_forecasts.append(tf)
                        
                        period = TAFForecastPeriod(
                            valid_from=datetime.fromisoformat(period_data['valid_from']),
                            valid_to=datetime.fromisoformat(period_data['valid_to']),
                            valid_from_timestamp=period_data['valid_from_timestamp'],
                            valid_to_timestamp=period_data['valid_to_timestamp'],
                            becomes_time=datetime.fromisoformat(period_data['becomes_time']) if period_data.get('becomes_time') else None,
                            forecast_change_type=period_data.get('forecast_change_type'),
                            probability_percent=period_data.get('probability_percent'),
                            wind_direction_degrees=period_data.get('wind_direction_degrees'),
                            wind_speed_knots=period_data.get('wind_speed_knots'),
                            wind_gust_knots=period_data.get('wind_gust_knots'),
                            wind_shear_height_feet=period_data.get('wind_shear_height_feet'),
                            wind_shear_direction_degrees=period_data.get('wind_shear_direction_degrees'),
                            wind_shear_speed_knots=period_data.get('wind_shear_speed_knots'),
                            visibility=period_data.get('visibility', '6+'),
                            vertical_visibility_feet=period_data.get('vertical_visibility_feet'),
                            weather_phenomena=period_data.get('weather_phenomena'),
                            altimeter_hpa=period_data.get('altimeter_hpa'),
                            cloud_layers=cloud_layers,
                            icing_turbulence=icing_turb,
                            temperature_forecasts=temp_forecasts,
                            not_decoded=period_data.get('not_decoded')
                        )
                        forecast_periods.append(period)
                    
                    # Create TAF object
                    taf = TAF(
                        station_id=taf_data['station_id'],
                        station_name=taf_data['station_name'],
                        latitude=taf_data['latitude'],
                        longitude=taf_data['longitude'],
                        elevation_meters=taf_data['elevation_meters'],
                        bulletin_time=datetime.fromisoformat(taf_data['bulletin_time']),
                        issue_time=datetime.fromisoformat(taf_data['issue_time']),
                        database_time=datetime.fromisoformat(taf_data['database_time']),
                        valid_from=datetime.fromisoformat(taf_data['valid_from']),
                        valid_to=datetime.fromisoformat(taf_data['valid_to']),
                        valid_from_timestamp=taf_data['valid_from_timestamp'],
                        valid_to_timestamp=taf_data['valid_to_timestamp'],
                        is_most_recent=taf_data.get('is_most_recent', True),
                        is_prior_version=taf_data.get('is_prior_version', False),
                        raw_taf=taf_data.get('raw_taf', ''),
                        remarks=taf_data.get('remarks', ''),
                        forecast_periods=forecast_periods
                    )
                    tafs_dict[station_id].append(taf)
                except Exception as e:
                    print(f"   ⚠️  Error parsing TAF for {station_id}: {e}")
                    continue
            
            if tafs_dict[station_id]:
                print(f"   TAF for {station_id}: {len(tafs_dict[station_id])} bulletins parsed successfully")
        
        # Parse Upper Winds
        upper_winds = []
        for uw_data in data.get('upper_winds', []):
            try:
                periods = []
                for period_data in uw_data.get('periods', []):
                    levels = []
                    for level_data in period_data.get('levels', []):
                        level = UpperWindLevel(
                            altitude_ft=level_data['altitude_ft'],
                            direction_deg=level_data.get('direction_deg'),
                            speed_kt=level_data.get('speed_kt'),
                            temperature_c=level_data.get('temperature_c')
                        )
                        levels.append(level)
                    
                    period = UpperWindPeriod(
                        valid_time=period_data['valid_time'],
                        use_period=period_data['use_period'],
                        levels=levels
                    )
                    periods.append(period)
                
                uw = UpperWind(
                    station=uw_data['station'],
                    periods=periods
                )
                upper_winds.append(uw)
            except Exception as e:
                print(f"   ⚠️  Error parsing Upper Wind: {e}")
                continue

        # Parse SIGMETs from history sample file (ensures consistent test data)
        sigmets = []
        sigmet_history_path = Path("weather_data/SIGMET_example.txt")
        if sigmet_history_path.exists():
            sigmet_text = sigmet_history_path.read_text(encoding='utf-8')
            sigmets = parse_sigmet_text(sigmet_text)

        # Enrich all weather data with station coordinates
        print("\n📍 Enriching weather data with station coordinates...")
        enrich_weather_data(metars_dict, tafs_dict, upper_winds)

        # Test CSV export
        print("\n🧪 Testing CSV Export...")
        test_output = Path("weather_data/test_csv_output")
        test_output.mkdir(exist_ok=True)
        
        exporter = WeatherDataCSVExporter(test_output)
        
        # Test METAR export
        if metars_dict:
            print("\n   Testing METAR CSV export...")
            try:
                metar_file = exporter.export_metars_to_csv(metars_dict, "test_metars.csv")
                print(f"   ✅ METAR CSV created: {metar_file}")
                
                # Check file size
                file_size = metar_file.stat().st_size
                print(f"      File size: {file_size:,} bytes")
                
                # Read first few lines
                with open(metar_file, 'r') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                print(f"      Header: {lines[0][:80]}...")
                if len(lines) > 1:
                    print(f"      Sample row: {lines[1][:80]}...")
                    
            except Exception as e:
                print(f"   ❌ METAR CSV export failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Test Upper Winds export
        if upper_winds:
            print("\n   Testing Upper Winds CSV export...")
            try:
                uw_file = exporter.export_upper_winds_to_csv(upper_winds, "test_upper_winds.csv")
                print(f"   ✅ Upper Winds CSV created: {uw_file}")
                
                file_size = uw_file.stat().st_size
                print(f"      File size: {file_size:,} bytes")
                
                with open(uw_file, 'r') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                print(f"      Header: {lines[0]}")
                if len(lines) > 1:
                    print(f"      Sample row: {lines[1]}")
                    
            except Exception as e:
                print(f"   ❌ Upper Winds CSV export failed: {e}")
                import traceback
                traceback.print_exc()
                return False

        if sigmets:
            print("\n   Testing SIGMET CSV export...")
            try:
                sigmet_file = exporter.export_sigmets_to_csv(
                    sigmets, "test_sigmets.csv")
                print(f"   ✅ SIGMET CSV created: {sigmet_file}")

                file_size = sigmet_file.stat().st_size
                print(f"      File size: {file_size:,} bytes")

                with open(sigmet_file, 'r') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                print(f"      Header: {lines[0]}")
                if len(lines) > 1:
                    print(f"      Sample row: {lines[1]}")

            except Exception as e:
                print(f"   ❌ SIGMET CSV export failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Test TAF export
        if tafs_dict:
            print("\n   Testing TAF CSV export...")
            try:
                taf_file = exporter.export_tafs_to_csv(tafs_dict, "test_tafs.csv")
                print(f"   ✅ TAF CSV created: {taf_file}")

                file_size = taf_file.stat().st_size
                print(f"      File size: {file_size:,} bytes")

                with open(taf_file, 'r') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                print(f"      Header: {lines[0][:80]}...")
                if len(lines) > 1:
                    print(f"      Sample row: {lines[1][:80]}...")

            except Exception as e:
                print(f"   ❌ TAF CSV export failed: {e}")
                import traceback
                traceback.print_exc()
                return False

        print("\n✅ CSV export test completed successfully!")
        print(f"   Test files saved to: {test_output}")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_export_from_json():
    assert run_csv_export_from_json() is True


if __name__ == "__main__":
    print("🧪 CSV Export Test Script")
    print("="*80)
    
    success = run_csv_export_from_json()
    
    if success:
        print("\n" + "="*80)
        print("✅ All tests passed!")
    else:
        print("\n" + "="*80)
        print("❌ Tests failed - check errors above")
