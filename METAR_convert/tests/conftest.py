"""Shared pytest fixtures for the METAR_convert test suite."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Iterable, List

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from navcanada_weather_server import NavCanadaWeatherServer


class StaticNavCanadaWeatherServer(NavCanadaWeatherServer):
    """NavCanadaWeatherServer that replays canned optimized JSON payloads."""

    def __init__(self, sample_path: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._sample_path = sample_path

    def _extract_raw_data(self, station_ids: Iterable[str]):  # type: ignore[override]
        raw = json.loads(self._sample_path.read_text(encoding="utf-8"))
        requested = {station_id.upper() for station_id in station_ids}
        data = deepcopy(raw.get("weather_data", {}))

        # Filter METAR/TAF dictionaries down to the requested stations.
        for key in ("METAR", "TAF"):
            section = data.get(key)
            if isinstance(section, dict):
                data[key] = {
                    station: entries
                    for station, entries in section.items()
                    if station in requested
                }

        raw["weather_data"] = data
        raw.setdefault("session_info", {})["stations_requested"] = list(requested)
        return raw


@pytest.fixture(scope="session")
def sample_data_path() -> Path:
    return Path(__file__).parent / "weather_data" / "multi_station_optimized.json"


@pytest.fixture(scope="session")
def server(sample_data_path: Path) -> StaticNavCanadaWeatherServer:
    return StaticNavCanadaWeatherServer(
        sample_path=sample_data_path,
        headless=True,
        timeout=5,
        verbose=False,
        repository=None,
    )


@pytest.fixture(scope="session")
def stations() -> List[str]:
    return ["CYVR", "CYYC"]


@pytest.fixture(params=["CYVR", "CYYC"])
def station_id(request: pytest.FixtureRequest) -> str:
    return request.param
