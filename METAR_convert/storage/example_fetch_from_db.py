"""Example script demonstrating how to retrieve weather objects from SQLite.

Run with:

    python -m METAR_convert.storage.example_fetch_from_db \
        --db weather_data/weather.db \
        --limit 2

It will print decoded METAR, TAF, Upper Wind, and SIGMET objects using the
same data models employed throughout the project.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union, Any

from .sqlite_repository import (
    SQLiteWeatherRepository,
    MetarObservation,
    TafBulletin,
    UpperWindPeriodRecord,
    SigmetReport,
)
from ..metar import CloudLayer, METAR
from ..taf import (
    IcingTurbulence,
    TAF,
    TAFCloudLayer,
    TAFForecastPeriod,
    TemperatureForecast,
)
from ..upper_wind import UpperWind, UpperWindLevel, UpperWindPeriod
from ..sigmet import SIGMET


def _station_defaults(station) -> Tuple[str, float, float, int]:
    """Return (name, lat, lon, elevation) with safe defaults."""

    if station is None:
        return "", 0.0, 0.0, 0

    name = station.name or station.id or ""
    latitude = station.latitude if station.latitude is not None else 0.0
    longitude = station.longitude if station.longitude is not None else 0.0
    elevation = station.elevation_meters if station.elevation_meters is not None else 0
    return name, latitude, longitude, elevation


def fetch_metars(session: Any, limit: Optional[int]) -> List[METAR]:
    query = session.query(MetarObservation).order_by(MetarObservation.observation_time.desc())
    if limit and limit > 0:
        query = query.limit(limit)

    metars: List[METAR] = []
    for record in query.all():
        name, lat, lon, elev = _station_defaults(record.station)
        metars.append(
            METAR(
                station_id=record.station_id,
                station_name=name or record.station_id,
                latitude=lat,
                longitude=lon,
                elevation_meters=elev,
                observation_time=record.observation_time,
                receipt_time=record.receipt_time,
                observation_timestamp=record.observation_timestamp,
                temperature_celsius=record.temperature_celsius,
                dewpoint_celsius=record.dewpoint_celsius,
                wind_direction_degrees=record.wind_direction_degrees,
                wind_speed_knots=record.wind_speed_knots,
                wind_gust_knots=record.wind_gust_knots,
                wind_variable=record.wind_variable,
                visibility=record.visibility,
                visibility_meters=record.visibility_meters,
                altimeter_hpa=record.altimeter_hpa,
                sea_level_pressure_hpa=record.sea_level_pressure_hpa,
                pressure_tendency_hpa=record.pressure_tendency_hpa,
                sky_coverage=record.sky_coverage,
                cloud_layers=[
                    CloudLayer(
                        coverage=layer.coverage,
                        altitude_feet=layer.altitude_feet,
                        cloud_type=layer.cloud_type,
                    )
                    for layer in record.cloud_layers
                ],
                flight_category=record.flight_category,
                max_temperature_celsius=record.max_temperature_celsius,
                min_temperature_celsius=record.min_temperature_celsius,
                present_weather=[phen.code for phen in record.weather],
                quality_control_field=record.quality_control_field,
                report_type=record.report_type,
                raw_observation=record.raw_observation,
            )
        )
    return metars


def _decode_wind_direction(value: Optional[str]) -> Optional[Union[int, str]]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def fetch_tafs(session: Any, limit: Optional[int]) -> List[TAF]:
    query = session.query(TafBulletin).order_by(TafBulletin.issue_time.desc())
    if limit and limit > 0:
        query = query.limit(limit)

    tafs: List[TAF] = []
    for bulletin in query.all():
        name, lat, lon, elev = _station_defaults(bulletin.station)
        forecast_periods: List[TAFForecastPeriod] = []
        for period in bulletin.forecast_periods:
            forecast_periods.append(
                TAFForecastPeriod(
                    valid_from=period.valid_from,
                    valid_to=period.valid_to,
                    valid_from_timestamp=period.valid_from_timestamp,
                    valid_to_timestamp=period.valid_to_timestamp,
                    becomes_time=period.becomes_time,
                    forecast_change_type=period.forecast_change_type,
                    probability_percent=period.probability_percent,
                    wind_direction_degrees=_decode_wind_direction(period.wind_direction_degrees),
                    wind_speed_knots=period.wind_speed_knots,
                    wind_gust_knots=period.wind_gust_knots,
                    wind_shear_height_feet=period.wind_shear_height_feet,
                    wind_shear_direction_degrees=period.wind_shear_direction_degrees,
                    wind_shear_speed_knots=period.wind_shear_speed_knots,
                    visibility=period.visibility,
                    vertical_visibility_feet=period.vertical_visibility_feet,
                    weather_phenomena=period.weather_phenomena,
                    altimeter_hpa=period.altimeter_hpa,
                    cloud_layers=[
                        TAFCloudLayer(
                            coverage=layer.coverage,
                            base_altitude_feet=layer.base_altitude_feet,
                            cloud_type=layer.cloud_type,
                        )
                        for layer in period.cloud_layers
                    ],
                    icing_turbulence=[
                        IcingTurbulence(
                            intensity=item.intensity,
                            type=item.type,
                            base_altitude_feet=item.base_altitude_feet,
                            top_altitude_feet=item.top_altitude_feet,
                        )
                        for item in period.icing_turbulence
                    ],
                    temperature_forecasts=[
                        TemperatureForecast(
                            temperature_celsius=temp.temperature_celsius,
                            time=temp.time,
                        )
                        for temp in period.temperature_forecasts
                    ],
                    not_decoded=period.not_decoded,
                )
            )

        tafs.append(
            TAF(
                station_id=bulletin.station_id,
                station_name=name or bulletin.station_id,
                latitude=lat,
                longitude=lon,
                elevation_meters=elev,
                bulletin_time=bulletin.bulletin_time,
                issue_time=bulletin.issue_time,
                database_time=bulletin.database_time,
                valid_from=bulletin.valid_from,
                valid_to=bulletin.valid_to,
                valid_from_timestamp=bulletin.valid_from_timestamp,
                valid_to_timestamp=bulletin.valid_to_timestamp,
                is_most_recent=bulletin.is_most_recent,
                is_prior_version=bulletin.is_prior_version,
                raw_taf=bulletin.raw_taf,
                remarks=bulletin.remarks,
                forecast_periods=forecast_periods,
            )
        )
    return tafs


def fetch_upper_winds(session: Any, limit: Optional[int]) -> List[UpperWind]:
    station_query = session.query(UpperWindPeriodRecord.station_id).distinct().order_by(UpperWindPeriodRecord.station_id)
    if limit and limit > 0:
        station_query = station_query.limit(limit)

    upper_winds: List[UpperWind] = []
    for (station_id,) in station_query.all():
        period_records = (
            session.query(UpperWindPeriodRecord)
            .filter_by(station_id=station_id)
            .order_by(UpperWindPeriodRecord.valid_time.desc(), UpperWindPeriodRecord.use_period.desc())
            .all()
        )
        periods: List[UpperWindPeriod] = []
        for record in period_records:
            levels = [
                UpperWindLevel(
                    altitude_ft=level.altitude_ft,
                    direction_deg=level.direction_deg,
                    speed_kt=level.speed_kt,
                    temperature_c=level.temperature_c,
                )
                for level in record.levels
            ]
            periods.append(UpperWindPeriod(record.valid_time, record.use_period, levels))

        upper_winds.append(UpperWind(station=station_id, periods=periods))
    return upper_winds


def fetch_sigmets(session: Any, limit: Optional[int]) -> List[SIGMET]:
    query = session.query(SigmetReport).order_by(SigmetReport.created_at.desc())
    if limit and limit > 0:
        query = query.limit(limit)

    sigmets: List[SIGMET] = []
    for record in query.all():
        sigmets.append(
            SIGMET(
                raw_text=record.raw_text,
                sigmet_id=record.sigmet_identifier,
                fir=record.fir,
                sequence=record.sequence,
                phenomenon=record.phenomenon,
                observation_type=record.observation_type,
                observation_time=record.observation_time,
                valid_from=record.valid_from,
                valid_to=record.valid_to,
                levels=record.levels,
                movement=record.movement,
                change=record.change,
                area_description=record.area_description,
                area_points=[
                    {"latitude": point.latitude, "longitude": point.longitude}
                    for point in record.area_points
                ],
            )
        )
    return sigmets


def _print_header(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def _summarise_metars(metars: Sequence[METAR]) -> None:
    if not metars:
        print("  (no METAR observations found)")
        return
    for metar in metars:
        time_str = metar.observation_time.strftime("%Y-%m-%d %H:%MZ")
        print(f"  {metar.station_id} at {time_str}: {metar.raw_observation}")


def _summarise_tafs(tafs: Sequence[TAF]) -> None:
    if not tafs:
        print("  (no TAF bulletins found)")
        return
    for taf in tafs:
        time_str = taf.issue_time.strftime("%Y-%m-%d %H:%MZ")
        print(f"  {taf.station_id} issued {time_str}: {len(taf.forecast_periods)} period(s)")


def _summarise_upper_winds(upper_winds: Sequence[UpperWind]) -> None:
    if not upper_winds:
        print("  (no Upper Wind data found)")
        return
    for uw in upper_winds:
        print(f"  {uw.station}: {len(uw.periods)} period(s)")
        for period in uw.periods[:2]:
            print(
                f"    VALID {period.valid_time} USE {period.use_period} with {len(period.levels)} level(s)"
            )


def _summarise_sigmets(sigmets: Sequence[SIGMET]) -> None:
    if not sigmets:
        print("  (no SIGMET advisories found)")
        return
    for sigmet in sigmets:
        print(f"  {sigmet.sigmet_id}: {sigmet.phenomenon} {sigmet.valid_from}/{sigmet.valid_to}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch decoded weather objects from the SQLite repository")
    parser.add_argument("--db", type=Path, default=Path("weather_data/weather.db"), help="Path to the SQLite database file")
    parser.add_argument("--limit", type=int, default=2, help="Maximum number of records to display per weather product")
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"Database file '{args.db}' was not found. Run data_query_canada_stations_v2.py first.")

    repository = SQLiteWeatherRepository(db_path=args.db)
    try:
        session_factory = repository._session_factory  # type: ignore[attr-defined]
        with session_factory() as session:  # type: ignore[call-arg]
            metars = fetch_metars(session, args.limit)
            tafs = fetch_tafs(session, args.limit)
            upper_winds = fetch_upper_winds(session, args.limit)
            sigmets = fetch_sigmets(session, args.limit)

        _print_header("METAR Observations")
        _summarise_metars(metars)

        _print_header("TAF Bulletins")
        _summarise_tafs(tafs)

        _print_header("Upper Wind Periods")
        _summarise_upper_winds(upper_winds)

        _print_header("SIGMET Advisories")
        _summarise_sigmets(sigmets)
    finally:
        repository.close()


if __name__ == "__main__":
    main()
