# natural_language_convert/run_group_upperwind.py
import json
from pathlib import Path
from .upperwind_rules import to_text as uw_to_text

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

def main():
    data = json.loads(GROUP_PATH.read_text())

    metars = data.get("metars", {}) or {}
    tafs   = data.get("tafs", {}) or {}

    # upper_winds is a list of period sets; use the first set if present
    uw_all = data.get("upper_winds", []) or []
    uw     = uw_all[0] if uw_all else None

    # Stations to print: METAR order first, then any TAF-only in their order
    stations = _ordered_union_keys(metars, tafs)

    if not stations:
        print("No stations found in this test group.")
        return

    for icao in stations:
        print("=" * 82)
        print(icao)

        if not uw:
            print(f"{icao}: no winds-aloft data available in this test group.")
            continue

        line = uw_to_text(uw, icao)
        if line:
            print(line)
        else:
            print(f"{icao}: no winds-aloft data available for this period.")

if __name__ == "__main__":
    main()
