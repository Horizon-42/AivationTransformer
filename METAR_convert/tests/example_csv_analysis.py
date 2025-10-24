#!/usr/bin/env python3
"""
Example analysis scripts demonstrating the new CSV structures.

These examples show how the improved CSV formats make analysis easier
compared to the old normalized structures.
"""

import csv
import json
from pathlib import Path


def example_1_metar_weather_conditions():
    """Find all stations with specific weather conditions."""
    print("="*60)
    print("Example 1: Find stations with snow (SN) in present weather")
    print("="*60)
    
    with open('test_metars.csv') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Parse present_weather JSON (handle empty strings)
            weather_str = row['present_weather']
            if not weather_str or weather_str == '':
                continue
                
            weather = json.loads(weather_str)
            
            # Check for snow
            if any('SN' in w for w in weather):
                print(f"{row['station_id']}: {row['visibility']} visibility, "
                      f"temp {row['temperature_celsius']}°C, weather: {weather}")
    print()


def example_2_taf_quick_filtering():
    """Use TAF summary fields to quickly find interesting forecasts."""
    print("="*60)
    print("Example 2: Find complex TAFs with high winds")
    print("="*60)
    
    with open('test_tafs.csv') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Quick filtering using summary fields (no JSON parsing needed!)
            if (int(row['num_periods']) >= 5 and 
                row['has_prob'] == 'True' and
                row['max_wind_speed_kt'] and 
                int(row['max_wind_speed_kt']) > 10):
                
                print(f"\n{row['station_id']}:")
                print(f"  • {row['num_periods']} forecast periods")
                print(f"  • Max wind: {row['max_wind_speed_kt']}kt")
                print(f"  • Has TEMPO: {row['has_tempo']}")
                print(f"  • Has BECMG: {row['has_becmg']}")
                print(f"  • Has PROB: {row['has_prob']}")
                print(f"  • Has FM: {row['has_fm']}")
    print()


def example_3_taf_detailed_analysis():
    """Parse TAF JSON for detailed period analysis."""
    print("="*60)
    print("Example 3: Analyze visibility trends in first TAF")
    print("="*60)
    
    with open('test_tafs.csv') as f:
        reader = csv.DictReader(f)
        row = next(reader)  # Get first TAF
        
        periods = json.loads(row['forecast_periods_json'])
        
        print(f"\nTAF for {row['station_id']}")
        print(f"Valid: {row['valid_from']} to {row['valid_to']}")
        print(f"\nVisibility trend:")
        
        for period in periods:
            change_type = period['forecast_change_type'] or 'BASE'
            vis = period['visibility']
            weather = period['weather_phenomena'] or 'clear'
            print(f"  {change_type:8s}: {vis:6s} - {weather}")
    print()


def example_4_upper_winds_wind_shear():
    """Detect wind shear using the wide format."""
    print("="*60)
    print("Example 4: Detect significant wind shear (direction change > 90°)")
    print("="*60)
    
    with open('test_upper_winds.csv') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            station = row['station_id']
            period = row['use_period']
            
            # Easy access to specific altitude winds (no filtering/pivoting needed!)
            dir_3k = int(row['wind_3000ft_dir']) if row['wind_3000ft_dir'] else None
            dir_12k = int(row['wind_12000ft_dir']) if row['wind_12000ft_dir'] else None
            
            if dir_3k and dir_12k:
                # Calculate direction change
                shear = abs(dir_12k - dir_3k)
                if shear > 180:
                    shear = 360 - shear
                
                if shear > 90:
                    print(f"{station} {period}: Significant shear detected!")
                    print(f"  3,000ft: {dir_3k:3d}° at {row['wind_3000ft_speed_kt']:2s}kt")
                    print(f"  12,000ft: {dir_12k:3d}° at {row['wind_12000ft_speed_kt']:2s}kt")
                    print(f"  Direction change: {shear:.0f}°")
    print()


def example_5_upper_winds_vertical_profile():
    """Analyze complete vertical wind profile."""
    print("="*60)
    print("Example 5: Full vertical wind profile for first station/period")
    print("="*60)
    
    altitudes = [3000, 6000, 9000, 12000, 18000, 24000, 30000, 34000, 39000]
    
    with open('test_upper_winds.csv') as f:
        reader = csv.DictReader(f)
        row = next(reader)  # Get first period
        
        print(f"\nStation: {row['station_id']}")
        print(f"Valid: {row['valid_time']}, Use Period: {row['use_period']}")
        print(f"\nAltitude   Wind          Temperature")
        print(f"{'(ft)':>8s}   {'Dir':>3s} {'Speed':>5s}   {'(°C)':>7s}")
        print("-" * 40)
        
        for alt in altitudes:
            dir_col = f'wind_{alt}ft_dir'
            speed_col = f'wind_{alt}ft_speed_kt'
            temp_col = f'temp_{alt}ft_c'
            
            dir_val = row[dir_col] if row[dir_col] else 'N/A'
            speed_val = row[speed_col] if row[speed_col] else 'N/A'
            temp_val = row[temp_col] if row[temp_col] else 'N/A'
            
            print(f"{alt:8d}   {dir_val:>3s} {speed_val:>5s}kt  {temp_val:>7s}")
    print()


def example_6_upper_winds_temperature_lapse():
    """Calculate temperature lapse rate."""
    print("="*60)
    print("Example 6: Temperature lapse rates")
    print("="*60)
    
    with open('test_upper_winds.csv') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            temp_3k = float(row['temp_3000ft_c']) if row['temp_3000ft_c'] else None
            temp_9k = float(row['temp_9000ft_c']) if row['temp_9000ft_c'] else None
            
            if temp_3k is not None and temp_9k is not None:
                # Standard lapse rate is about 2°C per 1000ft
                # Calculate observed lapse rate
                delta_temp = temp_9k - temp_3k
                delta_alt = 6000  # feet
                lapse_rate = -delta_temp / (delta_alt / 1000)  # °C per 1000ft
                
                stability = "stable" if lapse_rate < 1.5 else "unstable" if lapse_rate > 3.0 else "neutral"
                
                print(f"{row['station_id']} {row['use_period']}: "
                      f"Lapse rate = {lapse_rate:.2f}°C/1000ft ({stability})")
    print()


def example_7_multi_dataset_correlation():
    """Correlate METAR observations with TAF forecasts."""
    print("="*60)
    print("Example 7: Compare METAR observations with TAF forecasts")
    print("="*60)
    
    # Load METARs
    metars = {}
    with open('test_metars.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metars[row['station_id']] = row
    
    # Load TAFs
    with open('test_tafs.csv') as f:
        reader = csv.DictReader(f)
        
        for taf_row in reader:
            station = taf_row['station_id']
            
            if station in metars:
                metar = metars[station]
                
                # Compare METAR with first TAF period (base forecast)
                periods = json.loads(taf_row['forecast_periods_json'])
                base_period = periods[0] if periods else None
                
                if base_period:
                    metar_wind = int(metar['wind_speed_knots']) if metar['wind_speed_knots'] else None
                    taf_wind = base_period['wind_speed_knots']
                    
                    if metar_wind and taf_wind:
                        diff = abs(metar_wind - taf_wind)
                        accuracy = "✓" if diff <= 5 else "⚠" if diff <= 10 else "✗"
                        
                        print(f"{station}: Wind forecast {accuracy}")
                        print(f"  METAR: {metar_wind}kt actual")
                        print(f"  TAF:   {taf_wind}kt forecast")
                        print(f"  Diff:  {diff}kt")
    print()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("CSV ANALYSIS EXAMPLES - New Structure Benefits")
    print("="*60 + "\n")
    
    # Change to test output directory
    import os
    os.chdir('weather_data/test_csv_output')
    
    example_1_metar_weather_conditions()
    example_2_taf_quick_filtering()
    example_3_taf_detailed_analysis()
    example_4_upper_winds_wind_shear()
    example_5_upper_winds_vertical_profile()
    example_6_upper_winds_temperature_lapse()
    example_7_multi_dataset_correlation()
    
    print("="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == '__main__':
    main()
