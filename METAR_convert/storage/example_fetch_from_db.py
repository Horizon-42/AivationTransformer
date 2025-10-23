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
from typing import Sequence

from .sqlite_repository import SQLiteWeatherRepository
from ..metar import METAR
from ..taf import TAF
from ..upper_wind import UpperWind
from ..sigmet import SIGMET


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
    parser.add_argument(
        "--station",
        action="append",
        help="ICAO station identifier to filter by (repeatable or comma separated)",
    )
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"Database file '{args.db}' was not found. Run data_query_canada_stations_v2.py first.")

    station_filters = None
    if args.station:
        station_filters = [
            code.strip().upper()
            for value in args.station
            for code in value.split(",")
            if code and code.strip()
        ]
        if not station_filters:
            station_filters = None

    repository = SQLiteWeatherRepository(db_path=args.db)
    try:
        metars = repository.fetch_metars(
            station_ids=station_filters, limit=args.limit)
        tafs = repository.fetch_tafs(
            station_ids=station_filters, limit=args.limit)
        upper_winds = repository.fetch_upper_winds(
            station_ids=station_filters, limit=args.limit)
        sigmets = repository.fetch_sigmets(limit=args.limit)

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
