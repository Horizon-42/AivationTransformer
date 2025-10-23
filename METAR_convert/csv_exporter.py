"""
CSV Export Module for Aviation Weather Data

This module provides functions to export METAR, TAF, and Upper Wind data
to well-structured CSV files suitable for data analysis.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .metar import METAR
from .sigmet import SIGMET
from .taf import TAF
from .upper_wind import UpperWind


class WeatherDataCSVExporter:
    """Exports aviation weather data to CSV files with appropriate schemas."""
    
    def __init__(self, output_dir: Path, verbose: bool = True):
        """
        Initialize the CSV exporter.
        
        Args:
            output_dir: Directory where CSV files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Emit messages when verbose mode is enabled."""
        if self.verbose:
            print(message)

    def export_metars_to_csv(self, metars_dict: Dict[str, List[METAR]],
                             filename: Optional[str] = None) -> Path:
        """
        Export METAR data to CSV format.
        
        Schema: One row per METAR observation
        Columns: Station info, timing, conditions, wind, visibility, pressure, clouds, weather
        Note: Raw observation text is excluded for cleaner analysis
        
        Args:
            metars_dict: Dictionary mapping station IDs to lists of METAR objects
            filename: Optional custom filename (default: metars_{timestamp}.csv)
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metars_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Define CSV columns (NO raw_observation for cleaner data)
        fieldnames = [
            # Station Information
            'station_id',
            'station_name',
            'latitude',
            'longitude',
            'elevation_meters',
            
            # Timing
            'observation_time',
            'observation_timestamp',
            
            # Report Info
            'report_type',
            'flight_category',
            
            # Temperature
            'temperature_celsius',
            'dewpoint_celsius',
            
            # Wind
            'wind_direction_degrees',
            'wind_speed_knots',
            'wind_gust_knots',
            'wind_variable',
            
            # Visibility
            'visibility',
            'visibility_meters',
            
            # Pressure
            'altimeter_hpa',
            'sea_level_pressure_hpa',
            
            # Sky Conditions
            'sky_coverage',
            'cloud_layers_json',  # JSON string of cloud layers
            
            # Weather
            'present_weather'  # Comma-separated list
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            rows_written = 0

            # Process each station's METARs
            for station_id, metars in metars_dict.items():
                for metar in metars:
                    # Prepare cloud layers as JSON string
                    cloud_layers_str = json.dumps([
                        {
                            'coverage': layer.coverage,
                            'base_feet': layer.altitude_feet,  # METAR uses altitude_feet
                            'cloud_type': layer.cloud_type
                        }
                        for layer in metar.cloud_layers
                    ]) if metar.cloud_layers else '[]'
                    
                    # Prepare present weather as comma-separated
                    present_weather_str = ','.join(metar.present_weather) if metar.present_weather else ''
                    
                    row = {
                        'station_id': metar.station_id,
                        'station_name': metar.station_name,
                        'latitude': metar.latitude,
                        'longitude': metar.longitude,
                        'elevation_meters': metar.elevation_meters,
                        
                        'observation_time': metar.observation_time.isoformat() if metar.observation_time else '',
                        'observation_timestamp': metar.observation_timestamp,
                        
                        'report_type': metar.report_type,
                        'flight_category': metar.flight_category,
                        
                        'temperature_celsius': metar.temperature_celsius,
                        'dewpoint_celsius': metar.dewpoint_celsius,
                        
                        'wind_direction_degrees': metar.wind_direction_degrees or '',
                        'wind_speed_knots': metar.wind_speed_knots or '',
                        'wind_gust_knots': metar.wind_gust_knots or '',
                        'wind_variable': metar.wind_variable,
                        
                        'visibility': metar.visibility,
                        'visibility_meters': metar.visibility_meters or '',
                        
                        'altimeter_hpa': metar.altimeter_hpa,
                        'sea_level_pressure_hpa': metar.sea_level_pressure_hpa or '',
                        
                        'sky_coverage': metar.sky_coverage,
                        'cloud_layers_json': cloud_layers_str,
                        
                        'present_weather': present_weather_str
                    }
                    
                    writer.writerow(row)
                    rows_written += 1
        
        self._log(f"   📊 Exported {rows_written} METARs to: {filepath.name}")
        return filepath
    
    def export_tafs_to_csv(self, tafs_dict: Dict[str, List[TAF]],
                           filename: Optional[str] = None) -> Path:
        """
        Export TAF data to CSV format.
        
        Schema: One row per forecast period (repeats bulletin info for each period).
        This structure avoids JSON in cells while keeping data easy to filter and analyze.
        
        Args:
            tafs_dict: Dictionary mapping station IDs to lists of TAF objects
            filename: Optional custom filename (default: tafs_{timestamp}.csv)
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tafs_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Define CSV columns - one row per forecast period
        fieldnames = [
            # Station Information
            'station_id',
            'station_name',
            'latitude',
            'longitude',
            'elevation_meters',
            
            # TAF Bulletin Info (repeated for each period)
            'bulletin_time',
            'issue_time',
            'bulletin_valid_from',
            'bulletin_valid_to',
            
            # Forecast Period Info
            'period_valid_from',
            'period_valid_to',
            'forecast_change_type',  # BASE, FM, BECMG, TEMPO, PROB
            'probability_percent',
            
            # Wind Forecast
            'wind_direction_deg',
            'wind_speed_kt',
            'wind_gust_kt',
            
            # Visibility Forecast
            'visibility',
            
            # Weather Forecast
            'weather_phenomena',
            
            # Sky Conditions (combined into one readable string)
            'sky_conditions',
            
            # Remarks
            'remarks'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            total_periods = 0
            
            # Process each station's TAFs
            for station_id, tafs in tafs_dict.items():
                for taf in tafs:
                    # Each TAF has multiple forecast periods
                    for period in taf.forecast_periods:
                        # Build sky conditions string from cloud layers
                        sky_conditions = []
                        if period.cloud_layers:
                            for layer in period.cloud_layers:
                                parts = [layer.coverage]
                                if layer.base_altitude_feet:
                                    parts.append(f"{layer.base_altitude_feet}ft")
                                if layer.cloud_type:
                                    parts.append(layer.cloud_type)
                                sky_conditions.append(' '.join(parts))
                        sky_str = '; '.join(sky_conditions) if sky_conditions else ''
                        
                        # Determine forecast type (BASE for first period without change type)
                        change_type = period.forecast_change_type or ''
                        if not change_type and period == taf.forecast_periods[0]:
                            change_type = 'BASE'
                        
                        row = {
                            'station_id': taf.station_id,
                            'station_name': taf.station_name,
                            'latitude': taf.latitude,
                            'longitude': taf.longitude,
                            'elevation_meters': taf.elevation_meters,
                            
                            'bulletin_time': taf.bulletin_time.isoformat() if taf.bulletin_time else '',
                            'issue_time': taf.issue_time.isoformat() if taf.issue_time else '',
                            'bulletin_valid_from': taf.valid_from.isoformat() if taf.valid_from else '',
                            'bulletin_valid_to': taf.valid_to.isoformat() if taf.valid_to else '',
                            
                            'period_valid_from': period.valid_from.isoformat() if period.valid_from else '',
                            'period_valid_to': period.valid_to.isoformat() if period.valid_to else '',
                            'forecast_change_type': change_type,
                            'probability_percent': period.probability_percent or '',
                            
                            'wind_direction_deg': period.wind_direction_degrees or '',
                            'wind_speed_kt': period.wind_speed_knots or '',
                            'wind_gust_kt': period.wind_gust_knots or '',
                            
                            'visibility': period.visibility or '',
                            'weather_phenomena': period.weather_phenomena or '',
                            
                            'sky_conditions': sky_str,
                            
                            'remarks': taf.remarks or ''
                        }
                        
                        writer.writerow(row)
                        total_periods += 1
        
        self._log(
            f"   📊 Exported {total_periods} TAF forecast periods to: {filepath.name}")
        return filepath
    
    def export_upper_winds_to_csv(self, upper_winds: List[UpperWind],
                                  filename: Optional[str] = None) -> Path:
        """
        Export Upper Wind data to CSV format.
        
        Schema: One row per period per station (wide format) with altitude levels as columns.
        Each altitude has ONE column containing: "dir/speed/temp" (e.g., "280/15/-28")
        
        Standard aviation altitude levels (feet): 3000, 6000, 9000, 12000, 18000, 24000, 30000, 34000, 39000
        
        Args:
            upper_winds: List of UpperWind objects
            filename: Optional custom filename (default: upper_winds_{timestamp}.csv)
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upper_winds_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Standard aviation altitude levels
        standard_altitudes = [3000, 6000, 9000, 12000, 18000, 24000, 30000, 34000, 39000]
        
        # Build fieldnames - one column per altitude
        fieldnames = [
            'station_id',
            'valid_time',       # e.g., "221200Z"
            'use_period'        # e.g., "1800-0000" or "00-12"
        ]
        
        # Add one column for each altitude (format: "dir/speed/temp")
        for alt in standard_altitudes:
            fieldnames.append(f'{alt}ft')
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            total_periods = 0
            
            # Process each UpperWind object (one per station)
            for upper_wind in upper_winds:
                station_id = upper_wind.station
                
                # Each station has multiple periods
                for period in upper_wind.periods:
                    # Build row with base info
                    row = {
                        'station_id': station_id,
                        'valid_time': period.valid_time,
                        'use_period': period.use_period
                    }
                    
                    # Create a lookup dict for altitude levels
                    level_data = {}
                    for level in period.levels:
                        level_data[level.altitude_ft] = {
                            'direction': level.direction_deg,
                            'speed': level.speed_kt,
                            'temperature': level.temperature_c
                        }
                    
                    # Fill in one column per altitude with "dir/speed/temp" format
                    for alt in standard_altitudes:
                        if alt in level_data:
                            data = level_data[alt]
                            dir_val = data['direction'] if data['direction'] is not None else ''
                            speed_val = data['speed'] if data['speed'] is not None else ''
                            temp_val = data['temperature'] if data['temperature'] is not None else ''
                            
                            # Combine into single cell: "dir/speed/temp"
                            row[f'{alt}ft'] = f"{dir_val}/{speed_val}/{temp_val}"
                        else:
                            # No data for this altitude
                            row[f'{alt}ft'] = ''
                    
                    writer.writerow(row)
                    total_periods += 1
        
        self._log(
            f"   📊 Exported {total_periods} upper wind periods to: {filepath.name}")
        return filepath
    
    def export_sigmets_to_csv(self, sigmets: List[SIGMET], filename: Optional[str] = None) -> Path:
        """Export SIGMET advisories to CSV format."""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sigmets_{timestamp}.csv"

        filepath = self.output_dir / filename

        fieldnames = [
            'sigmet_id',
            'fir',
            'sequence',
            'phenomenon',
            'observation_type',
            'observation_time_z',
            'valid_from',
            'valid_to',
            'levels',
            'movement',
            'change',
            'area_description',
            'area_polygon'
        ]

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            total_sigmet = 0
            for sigmet in sigmets:
                area_polygon = ''
                if getattr(sigmet, 'area_points', None):
                    area_polygon = ';'.join(
                        f"{point['latitude']},{point['longitude']}" for point in sigmet.area_points
                    )

                row = {
                    'sigmet_id': getattr(sigmet, 'sigmet_id', ''),
                    'fir': getattr(sigmet, 'fir', ''),
                    'sequence': getattr(sigmet, 'sequence', ''),
                    'phenomenon': getattr(sigmet, 'phenomenon', ''),
                    'observation_type': getattr(sigmet, 'observation_type', ''),
                    'observation_time_z': getattr(sigmet, 'observation_time', ''),
                    'valid_from': getattr(sigmet, 'valid_from', ''),
                    'valid_to': getattr(sigmet, 'valid_to', ''),
                    'levels': getattr(sigmet, 'levels', ''),
                    'movement': getattr(sigmet, 'movement', ''),
                    'change': getattr(sigmet, 'change', ''),
                    'area_description': getattr(sigmet, 'area_description', ''),
                    'area_polygon': area_polygon,
                }

                writer.writerow(row)
                total_sigmet += 1

        self._log(
            f"   📊 Exported {total_sigmet} SIGMET advisory(ies) to: {filepath.name}")
        return filepath

    def export_all(self, metars_dict: Dict[str, List[METAR]],
                   tafs_dict: Dict[str, List[TAF]],
                   upper_winds: List[UpperWind],
                   sigmets: Optional[List[SIGMET]] = None,
                   group_num: Optional[int] = None) -> Dict[str, Path]:
        """
        Export all weather data types to CSV files.
        
        Args:
            metars_dict: Dictionary of METAR data
            tafs_dict: Dictionary of TAF data
            upper_winds: List of UpperWind objects
            group_num: Optional group number for filename prefix
            
        Returns:
            Dictionary mapping data type to filepath
        """
        prefix = f"group_{group_num:02d}_" if group_num else ""
        
        files = {}
        
        if metars_dict:
            files['metars'] = self.export_metars_to_csv(
                metars_dict, 
                f"{prefix}metars.csv"
            )
        
        if tafs_dict:
            files['tafs'] = self.export_tafs_to_csv(
                tafs_dict, 
                f"{prefix}tafs.csv"
            )
        
        if upper_winds:
            files['upper_winds'] = self.export_upper_winds_to_csv(
                upper_winds, 
                f"{prefix}upper_winds.csv"
            )

        if sigmets:
            files['sigmets'] = self.export_sigmets_to_csv(
                sigmets,
                f"{prefix}sigmets.csv"
            )
        
        return files
