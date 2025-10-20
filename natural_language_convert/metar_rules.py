# natural_language_convert/metar_rules.py

CARDINALS = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
             "S","SSW","SW","WSW","W","WNW","NW","NNW"]

def _deg_to_cardinal(deg):
    if deg in (None, "VRB"): return "variable"
    try:
        i = int((int(deg) % 360) / 22.5 + 0.5) % 16
        return CARDINALS[i]
    except Exception:
        return "variable"

def _vis_to_words(v):
    if v is None: return "not reported"
    s = str(v).strip().upper()
    if s.endswith("+"):
        return "greater than " + s[:-1] + " miles"
    # Assume SM miles as in your dataset (e.g., "30", "6+", "3/4")
    if s == "3/4": return "three-quarters of a mile"
    if s == "1/2": return "one-half mile"
    if s.endswith("SM"):
        # sometimes the parser might already have SM
        return s.replace("SM", "miles").strip()
    # plain number means miles
    return f"{s} miles"

def _altimeter_inhg(hpa):
    if hpa is None: return None
    return f"{hpa * 0.02953:.2f}"

def _clouds_to_text(layers: list | None) -> str | None:
    if not layers: 
        return None
    parts=[]
    for c in layers:
        cov = (c.get("coverage") or "").upper()
        cov_word = {"SKC":"clear skies","CLR":"clear skies","FEW":"few clouds",
                    "SCT":"scattered clouds","BKN":"broken clouds","OVC":"overcast"}.get(cov, cov.lower())
        alt = c.get("altitude_feet")
        if alt is None: alt = c.get("base_altitude_feet")
        if isinstance(alt, (int,float)):
            parts.append(f"{cov_word} at {int(round(alt)):,} feet")
        else:
            parts.append(cov_word)
    # compress if first item is "clear skies" and nothing else meaningful
    if len(parts) == 1 and parts[0] == "clear skies":
        return "clear skies"
    # for METAR, mentioning the lowest significant layer is usually enough
    return ", ".join(parts[:2])  # keep it brief

def to_text(m: dict) -> str:
    # Wind
    spd = m.get("wind_speed_knots")
    gust = m.get("wind_gust_knots")
    if not spd or spd == 0:
        wind = "Winds calm"
    else:
        head = _deg_to_cardinal(m.get("wind_direction_degrees"))
        wind = f"Winds {head} at {int(spd)} knots" + (f" gusting {int(gust)}" if gust else "")

    # Visibility
    vis = _vis_to_words(m.get("visibility"))
    vis_txt = f"Visibility {vis}"

    # Weather phenomena
    wx_list = m.get("present_weather") or []
    wx_map = {"-RA":"light rain","+RA":"heavy rain","RA":"rain","BR":"mist","FG":"fog",
              "-SN":"light snow","+SN":"heavy snow","SN":"snow","DZ":"drizzle","HZ":"haze",
              "SHRA":"rain showers","TSRA":"thunderstorms with rain"}
    wx_words = [wx_map.get(code.replace("−","-"), code) for code in wx_list]
    wx_txt = (" with " + " and ".join(wx_words)) if wx_words else ""

    # Clouds
    clouds = _clouds_to_text(m.get("cloud_layers"))
    clouds_txt = (". " + clouds.capitalize()) if clouds else ""

    # Temps and altimeter
    t = m.get("temperature_celsius")
    d = m.get("dewpoint_celsius")
    td_txt = f". Temperature {round(t)}°C, dew point {round(d)}°C" if (t is not None and d is not None) else ""
    alt_inhg = _altimeter_inhg(m.get("altimeter_hpa"))
    alt_txt = f", altimeter {alt_inhg} inHg" if alt_inhg else ""

    # Flight category
    cat = m.get("flight_category")
    cat_txt = f". ({cat})" if cat else ""

    return f"{wind}. {vis_txt}{wx_txt}{clouds_txt}{td_txt}{alt_txt}{cat_txt}"
