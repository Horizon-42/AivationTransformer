"""
Data Loader for Aviation Weather Transformer

Simple module to load METAR and TAF data from JSON files in the data directory.
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Add the parent directory to sys.path so we can import from METAR_convert
sys.path.insert(0, str(Path(__file__).parent.parent))

from METAR_convert.metar import METAR
from METAR_convert.taf import TAF


def load_metar_data() -> List[METAR]:
    """Load METAR data from metar_example_output.json"""
    data_dir = Path(__file__).parent.parent / "data"
    file_path = data_dir / "metar_example_output.json"
    
    with open(file_path, 'r') as f:
        raw_data = json.load(f)
    
    return [METAR.from_api_response(item) for item in raw_data]


def load_taf_data() -> List[TAF]:
    """Load TAF data from taf_example_output.json"""
    data_dir = Path(__file__).parent.parent / "data"
    file_path = data_dir / "taf_example_output.json"
    
    with open(file_path, 'r') as f:
        raw_data = json.load(f)
    
    return [TAF.from_api_response(item) for item in raw_data]


def load_all_data() -> Tuple[List[METAR], List[TAF]]:
    """Load both METAR and TAF data"""
    return load_metar_data(), load_taf_data()


# Example usage
if __name__ == "__main__":
    metars, tafs = load_all_data()
    print(f"Loaded {len(metars)} METAR and {len(tafs)} TAF records")
    
    if metars:
        print(f"First METAR: {metars[0].station_id} - {metars[0].temperature_celsius}°C")
    
    if tafs:
        print(f"First TAF: {tafs[0].station_id} - {len(tafs[0].forecast_periods)} periods")