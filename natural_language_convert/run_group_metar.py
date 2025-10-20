# natural_language_convert/run_group_metar.py
import json
from pathlib import Path
from .metar_rules import to_text as metar_to_text

GROUP_PATH = Path(__file__).resolve().parents[1] / "data" / "test_group_01_parsed.json"

def _ordered_union_keys(d1: dict, d2: dict) -> list[str]:
    """
    Preserve insertion order from JSON:
    - first all keys from d1 (in their original order),
    - then any keys that appear only in d2 (in d2's order).
    """
    out = []
    for k in (d1 or {}).keys():
        out.append(k)
    for k in (d2 or {}).keys():
        if k not in out:
            out.append(k)
    return out

def _latest_metar(metars_for_station):
    if not metars_for_station:
        return None
    if all("observation_timestamp" in m for m in metars_for_station):
        return max(metars_for_station, key=lambda m: m["observation_timestamp"])
    return metars_for_station[0]

def main():
    data = json.loads(GROUP_PATH.read_text())
    metars = data.get("metars", {}) or {}
    tafs   = data.get("tafs", {}) or {}

    # Show stations in JSON order: METAR keys first, then TAF-only keys
    stations = _ordered_union_keys(metars, tafs)

    if not stations:
        print("No stations found in this test group.")
        return

    for icao in stations:
        print("=" * 82)
        print(icao)

        m = _latest_metar(metars.get(icao) or [])
        if m:
            print(f"{icao}: {metar_to_text(m)}")
        else:
            print(f"{icao}: no METAR available in this test group.")

if __name__ == "__main__":
    main()
