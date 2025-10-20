# natural_language_convert/run_group_taf.py
import json
from pathlib import Path
from .taf_rules import to_text as taf_to_text

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

def _latest_taf(tafs_for_station):
    if not tafs_for_station:
        return None
    recents = [t for t in tafs_for_station if t.get("is_most_recent")]
    return recents[0] if recents else tafs_for_station[0]

def main():
    data = json.loads(GROUP_PATH.read_text())
    metars = data.get("metars", {}) or {}
    tafs   = data.get("tafs", {}) or {}

    # Show stations in JSON order: TAF keys first, then METAR-only keys
    stations = _ordered_union_keys(tafs, metars)

    if not stations:
        print("No stations found in this test group.")
        return

    for icao in stations:
        print("=" * 82)
        print(icao)

        t = _latest_taf(tafs.get(icao) or [])
        if t:
            print(taf_to_text(t))
        else:
            print(f"{icao}: no TAF available in this test group.")

if __name__ == "__main__":
    main()
