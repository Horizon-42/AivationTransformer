# natural_language_convert/run_group_all.py
import json
from pathlib import Path

from .metar_rules import to_text as metar_to_text
from .taf_rules import to_text as taf_to_text
from .upperwind_rules import to_text as uw_to_text

GROUP_PATH = Path(__file__).resolve().parents[1] / "data" / "test_group_01_parsed.json"

def _ordered_union_keys(d1: dict, d2: dict) -> list[str]:
    """
    Preserve insertion order from JSON:
    - first all station keys from d1 (in their original order),
    - then any stations that appear only in d2 (in d2's order).
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
    # Prefer the newest by observation_timestamp if available
    if all("observation_timestamp" in m for m in metars_for_station):
        return max(metars_for_station, key=lambda m: m["observation_timestamp"])
    return metars_for_station[0]

def _latest_taf(tafs_for_station):
    if not tafs_for_station:
        return None
    recents = [t for t in tafs_for_station if t.get("is_most_recent")]
    return recents[0] if recents else tafs_for_station[0]

def main():
    data = json.loads(GROUP_PATH.read_text())
    metars = data.get("metars", {}) or {}
    tafs   = data.get("tafs", {}) or {}
    uw_all = data.get("upper_winds", []) or []
    uw     = uw_all[0] if uw_all else None  # one period set for this group

    # Station order = METAR order first, then any TAF-only stations in their order
    stations = _ordered_union_keys(metars, tafs)

    for icao in stations:
        print("=" * 82)
        print(icao)

        # -------- METAR (always first)
        m = _latest_metar(metars.get(icao) or [])
        if m:
            print(f"{icao}: {metar_to_text(m)}")
        else:
            print(f"{icao}: no METAR available in this test group.")

        # -------- TAF (second)
        t = _latest_taf(tafs.get(icao) or [])
        print()  # blank line between sections
        if t:
            print(taf_to_text(t))
        else:
            print(f"{icao}: no TAF available in this test group.")

        # -------- Upper-wind (third)
        print()  # blank line between sections
        if not uw:
            print(f"{icao}: no winds-aloft data available in this test group.")
        else:
            line = uw_to_text(uw, icao)
            if line:
                print(line)
            else:
                print(f"{icao}: no winds-aloft data available for this period.")

if __name__ == "__main__":
    main()
