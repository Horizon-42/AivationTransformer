# natural_language_convert/schema_builder.py

def _clouds_compact(cloud_layers: list | None) -> str:
    if not cloud_layers:
        return ""
    parts = []
    for c in cloud_layers:
        cov = (c.get("coverage") or "").upper()
        alt = c.get("altitude_feet")
        if alt is None:
            alt = c.get("base_altitude_feet")
        # encode hundreds of feet as two digits (e.g., 2000 -> 20)
        if isinstance(alt, (int, float)):
            parts.append(f"{cov}{int(round(alt/100)):02d}")
        else:
            parts.append(f"{cov}")
    return "|".join(parts)

def build_metar_schema(m: dict) -> str:
    """
    Build a compact, deterministic text schema for a parsed METAR dict
    from test_group_0X_parsed.json.
    """
    wx = " ".join(m.get("present_weather") or [])
    clouds = _clouds_compact(m.get("cloud_layers"))

    return (
        "TASK=METAR\n"
        f"STATION={m.get('station_id')}\n"
        f"TIME={m.get('observation_time')}\n"
        f"WIND_DIR={m.get('wind_direction_degrees')}\n"
        f"WIND_SPD={m.get('wind_speed_knots')}\n"
        f"WIND_GUST={m.get('wind_gust_knots')}\n"
        f"WIND_VAR={m.get('wind_variable')}\n"
        f"VIS={m.get('visibility')}\n"
        f"WX={wx}\n"
        f"CLOUDS={clouds}\n"
        f"TEMP={m.get('temperature_celsius')}\n"
        f"DEW={m.get('dewpoint_celsius')}\n"
        f"ALT_HPA={m.get('altimeter_hpa')}\n"
        f"CAT={m.get('flight_category')}\n"
    )
