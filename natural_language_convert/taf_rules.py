# natural_language_convert/taf_rules.py

from datetime import datetime
import re

CARDINALS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
             "S","SSW","SW","WSW","W","WNW","NW","NNW"]

# ---------- small helpers ----------

def _deg_to_cardinal(deg):
    if deg in (None, "VRB"): 
        return "variable"
    try:
        i = int((int(deg) % 360) / 22.5 + 0.5) % 16
        return CARDINALS[i]
    except Exception:
        return "variable"

def _vis_to_words(v):
    if v is None: 
        return None
    s = str(v).upper().strip()
    # keep TAF convention in SM
    if s.endswith("+"):
        # Examples: "6+" -> "greater than 6 SM"
        return "greater than " + s[:-1] + " SM"
    if s in {"3/4", "1/2", "1 1/2", "1 1/4", "1 3/4"}:
        return f"{s} SM"
    if s.endswith("SM"):
        return s
    # plain number -> SM
    return f"{s} SM"

WX_MAP = {
    "-RA":"light rain","+RA":"heavy rain","RA":"rain","SHRA":"rain showers",
    "-SN":"light snow","+SN":"heavy snow","SN":"snow","PL":"ice pellets",
    "TSRA":"thunderstorms with rain","BR":"mist","FG":"fog","HZ":"haze","DZ":"drizzle"
}

def _wx_to_words(wx):
    if not wx: 
        return None
    if isinstance(wx, str): 
        wx = wx.split()
    words = [WX_MAP.get(code.replace("−","-"), code) for code in wx]
    return " and ".join(words) if words else None

def _fmt_time_like(t):
    """
    Input can be an ISO-like string (sometimes with microseconds) or already 'DD/HHMMZ'.
    Output: 'DD/HHMMZ' when parseable, otherwise a cleaned string without microseconds (adds Z if missing).
    """
    if not t:
        return ""
    s = str(t).strip()
    # strip microseconds if present
    if "." in s:
        s = s.split(".")[0]
    # Some sources already end with 'Z'
    z = s.endswith("Z")
    s_nz = s[:-1] if z else s
    # Try to parse as ISO (YYYY-MM-DDTHH:MM:SS)
    try:
        dt = datetime.fromisoformat(s_nz)
        return dt.strftime("%d/%H%MZ")
    except Exception:
        # Fallback: if it already looks like DD/HHMMZ, keep it; else ensure 'Z'
        return s if z or s.endswith("Z") or "/" in s else s + "Z"

def _clouds_to_words(layers):
    """
    Convert cloud layers to short wording; normalize 'clear skies' when appropriate.
    """
    if not layers: 
        return None
    parts=[]
    for c in layers:
        cov = (c.get("coverage") or "").upper()
        cov_word = {"FEW":"few","SCT":"scattered","BKN":"broken","OVC":"overcast",
                    "CLR":"clear skies","SKC":"clear skies"}.get(cov, cov.lower())
        alt = c.get("base_altitude_feet") or c.get("altitude_feet")
        if isinstance(alt,(int,float)):
            # If it's 'clear skies', altitude is not needed
            if cov_word == "clear skies":
                parts.append("clear skies")
            else:
                parts.append(f"{cov_word} at {int(alt):,} ft")
        else:
            parts.append(cov_word)
    # De-duplicate identical phrases and keep it brief
    parts = list(dict.fromkeys(parts))
    # Prefer just one "clear skies" if present
    if "clear skies" in parts and len(parts) > 1:
        parts = ["clear skies"]
    return ", ".join(parts[:2])

def _wind_piece(p):
    spd = p.get("wind_speed_knots")
    if spd is None:
        return None
    head = _deg_to_cardinal(p.get("wind_direction_degrees"))
    gust = p.get("wind_gust_knots")
    return f"winds {head} {int(spd)} kt" + (f" gust {int(gust)}" if gust else "")

def _period_header(p):
    t0 = _fmt_time_like(p.get("valid_from"))
    t1 = _fmt_time_like(p.get("valid_to"))
    tag = (p.get("forecast_change_type") or "FM").upper()

    if tag.startswith("PROB"):
        m = re.match(r"PROB(\d{2})", tag)
        perc = m.group(1) if m else ""
        # e.g., "30 percent probability 13/2000Z–13/0000Z"
        return f"{int(perc)} percent probability {t0}–{t1}" if perc else f"Probability {t0}–{t1}"

    if tag == "TEMPO":
        return f"Temporarily {t0}–{t1}"
    if tag == "BECMG":
        return f"Becoming {t0}–{t1}"
    if tag == "FM":
        return f"From {t0}"
    # Unknown / BASE
    return f"From {t0}"

def _period_body(p):
    bits=[]
    w = _wind_piece(p)
    if w: bits.append(w)

    v = _vis_to_words(p.get("visibility"))
    if v: bits.append(f"vis {v}")

    wx = _wx_to_words(p.get("weather_phenomena"))
    if wx: bits.append(wx)

    cl = _clouds_to_words(p.get("cloud_layers"))
    if cl: bits.append(cl)

    return ", ".join(bits) if bits else "no significant change"

# ---------- main API ----------

def to_text(t: dict) -> str:
    valid_from = _fmt_time_like(t.get("valid_from"))
    valid_to   = _fmt_time_like(t.get("valid_to"))
    header = f"{t.get('station_id','')} TAF valid {valid_from}–{valid_to}:"

    # Sort periods by start time (robust to strings with microseconds/ISO)
    def _parse_for_sort(x):
        raw = str(x or "").strip()
        raw = raw.split(".")[0]  # drop microseconds if any
        try:
            # remove trailing Z for parsing
            if raw.endswith("Z"): raw = raw[:-1]
            return datetime.fromisoformat(raw)
        except Exception:
            return raw  # string fallback

    periods = list(t.get("forecast_periods", []))
    periods.sort(key=lambda p: _parse_for_sort(p.get("valid_from")))

    lines = [header]
    for p in periods:
        head = _period_header(p)
        body = _period_body(p)
        lines.append(f"{head}, {body}.")

    return "\n".join(lines)