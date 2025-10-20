# natural_language_convert/upperwind_rules.py

PICKS = [3000, 6000, 9000, 30000, 34000]

def _nearest(levels, targets):
    out={}
    for tgt in targets:
        if not levels: continue
        best = min(levels, key=lambda L: abs((L.get("altitude_ft") or tgt) - tgt))
        out[tgt] = best
    return out

def to_text(upperwind: dict, icao: str) -> str | None:
    if not upperwind or not upperwind.get("periods"): return None
    ident = icao[-3:]
    for period in upperwind["periods"]:
        levels = period["stations"].get(ident) or period["stations"].get(icao)
        if not levels: 
            continue
        pick = _nearest(levels, PICKS)
        parts=[]
        jetmax=None
        for alt, L in pick.items():
            spd = L.get("speed_kt")
            if spd is None: continue
            deg = L.get("direction_deg")
            hdg = "VRB" if deg is None else f"{int(deg):03d}°"
            temp = L.get("temperature_c")
            tfrag = f", {temp}°C" if temp is not None else ""
            parts.append(f"{alt:,} ft – {hdg} at {int(spd)} kt{tfrag}")
            if alt >= 30000:
                jetmax = max(jetmax or 0, spd)
        line = f"{icao} winds aloft valid {period.get('use_period')}: " + "; ".join(parts) + "."
        if jetmax and jetmax >= 80:
            line += " Strong jet-level flow."
        return line
    return None
