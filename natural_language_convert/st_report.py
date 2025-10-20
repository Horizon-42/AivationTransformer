# class StationReport:
#     def __init__(self, station_id, report_data, report_type, report_time, valid_period):
#         self.station_id = station_id
#         self.report_data = report_data
#         self.report_type = report_type  # 'METAR' or 'TAF'
#         self.report_time = report_time
#         self.valid_period = valid_period  # (start_time, end_time)

# a:StationReport = StationReport(
#     station_id="KJFK",
#     report_data="there will be light rain with a temperature of 75°F",
#     report_type="METAR",
#     report_time="2024-06-12T16:51:00Z",
#     valid_period=("2024-06-12T16:00:00Z", "2024-06-12T17:00:00Z"))

# print(a.station_id)  # Output: KJFK
# reports:list[StationReport] = [a]
# print(reports)  # Output: [<__main__.StationReport object at ...>]

# natural_language_convert/station_report.py
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Optional, Tuple, List
from datetime import datetime

from .metar_rules import to_text as metar_to_text
from .taf_rules import to_text as taf_to_text
from .upperwind_rules import to_text as uw_to_text


# ---------------------------------------------------------------------
# Dataclass definition
# ---------------------------------------------------------------------

@dataclass
class StationReport:
    station_id: str
    report_type: str = "Briefing"
    report_time: Optional[str] = None
    valid_period: Optional[Tuple[str, str]] = None
    report_data: str = ""


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _ordered_union_keys(d1: dict, d2: dict) -> list[str]:
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

def _latest_taf(tafs_for_station):
    if not tafs_for_station:
        return None
    recents = [t for t in tafs_for_station if t.get("is_most_recent")]
    return recents[0] if recents else tafs_for_station[0]

def _fmt_time_like(t: Optional[str]) -> Optional[str]:
    """Return 'DD/HHMMZ' for ISO-ish timestamps, else None or original if not parseable."""
    if not t:
        return None
    s = str(t).strip()
    if "." in s:
        s = s.split(".")[0]
    # strip trailing Z for parsing
    nz = s[:-1] if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(nz)
        return dt.strftime("%d/%H%MZ")
    except Exception:
        # if it already looks like DD/HHMMZ, keep it; else return original
        return s if ("/" in s and s.endswith("Z")) else s

# ---------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------

def build_reports_from_group(group_path: Path) -> List[StationReport]:
    """
    Reads a parsed group JSON and returns a list of StationReport objects.
    Keeps the station order from JSON.
    """
    data = json.loads(group_path.read_text())

    metars = data.get("metars", {}) or {}
    tafs   = data.get("tafs", {}) or {}
    uw_all = data.get("upper_winds", []) or []
    uw     = uw_all[0] if uw_all else None  # first period set

    stations = _ordered_union_keys(metars, tafs)
    reports: List[StationReport] = []

    for icao in stations:
        # ---------- METAR ----------
        m = _latest_metar(metars.get(icao) or [])
        if m:
            metar_text = f"{icao} METAR: {metar_to_text(m)}"
        else:
            metar_text = f"{icao} METAR: no METAR available in this test group."

        # ---------- TAF ----------
        t = _latest_taf(tafs.get(icao) or [])
        if t:
            taf_text = taf_to_text(t).replace(f"{icao} TAF valid", f"{icao} TAF valid")  # label already in text
        else:
            taf_text = f"{icao} TAF: no TAF available in this test group."

        # ---------- Upper-wind ----------
        if not uw:
            uw_text = f"{icao} Upperwinds: no winds-aloft data available in this test group."
        else:
            line = uw_to_text(uw, icao)
            uw_text = line if line else f"{icao} Upperwinds: no winds-aloft data available for this period."

        # ---------- Compose final labeled text ----------
        combined_text = f"{metar_text}\n\n{taf_text}\n\n{uw_text}"

        # ---------- Metadata ----------
        report_time = m.get("observation_time") if m else None
        valid_period = None
        if t:
            vf_raw, vt_raw = t.get("valid_from"), t.get("valid_to")
            vf = _fmt_time_like(vf_raw)
            vt = _fmt_time_like(vt_raw)
            if vf and vt:
                valid_period = (vf, vt)

        reports.append(
            StationReport(
                station_id=icao,
                report_time=report_time,
                valid_period=valid_period,
                report_data=combined_text.strip()
            )
        )

    return reports

# ---------------------------------------------------------------------
# Export helper
# ---------------------------------------------------------------------

def save_reports_as_json(reports: List[StationReport], out_path: Path) -> None:
    """
    Saves reports as a JSON array of dicts. Tuples become 2-element arrays in JSON.
    """
    serializable = []
    for r in reports:
        d = asdict(r)
        # ensure valid_period stays JSON-friendly (tuple -> list) handled by asdict already,
        # but make sure None stays None.
        serializable.append(d)
    out_path.write_text(json.dumps(serializable, indent=2))

# ---------------------------------------------------------------------
# CLI tester
# ---------------------------------------------------------------------

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    in_path  = root / "data" / "test_group_01_parsed.json"
    out_path = root / "data" / "station_reports.json"

    result = build_reports_from_group(in_path)
    save_reports_as_json(result, out_path)

    # pretty console preview
    print(f"Wrote {len(result)} StationReport objects to {out_path}")
    for r in result:
        print("=" * 82)
        print(f"{r.station_id} ({r.report_type})")
        print(f"time: {r.report_time}")
        if r.valid_period:
            print(f"valid: {r.valid_period[0]} – {r.valid_period[1]}")
        print()
        print(r.report_data)
        print()
