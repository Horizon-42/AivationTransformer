"""SIGMET data model and parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


_COORD_PATTERN = re.compile(
    r"([NS])\s*(\d{2})(\d{2})\s*([EW])\s*(\d{3})(\d{2})")


@dataclass
class SIGMET:
    """Structured representation of a single SIGMET advisory."""

    raw_text: str
    sigmet_id: str
    fir: str
    sequence: Optional[str]
    phenomenon: str
    observation_type: Optional[str]
    observation_time: Optional[str]
    valid_from: str
    valid_to: str
    levels: Optional[str]
    movement: Optional[str]
    change: Optional[str]
    area_description: str
    area_points: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise SIGMET to dictionary for JSON export."""
        return {
            "sigmet_id": self.sigmet_id,
            "fir": self.fir,
            "sequence": self.sequence,
            "phenomenon": self.phenomenon,
            "observation_type": self.observation_type,
            "observation_time": self.observation_time,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "levels": self.levels,
            "movement": self.movement,
            "change": self.change,
            "area_description": self.area_description,
            "area_points": self.area_points,
            "raw_text": self.raw_text,
        }

    def __repr__(self) -> str:
        return (
            f"SIGMET({self.sigmet_id}, {self.fir}, {self.phenomenon}, "
            f"{self.valid_from}-{self.valid_to})"
        )


def _coord_to_decimal(match: re.Match[str]) -> Dict[str, float]:
    """Convert coordinate match to decimal lat/lon."""
    lat_hem, lat_deg, lat_min, lon_hem, lon_deg, lon_min = match.groups()
    lat = int(lat_deg) + int(lat_min) / 60.0
    lon = int(lon_deg) + int(lon_min) / 60.0
    if lat_hem == "S":
        lat = -lat
    if lon_hem == "W":
        lon = -lon
    return {"latitude": round(lat, 4), "longitude": round(lon, 4)}


def _parse_area_points(area_text: str) -> List[Dict[str, float]]:
    """Parse polygon description ("WI ...") into coordinate list."""
    points: List[Dict[str, float]] = []
    if not area_text:
        return points

    # Normalise dashes and whitespace
    tokens = [token.strip()
              for token in area_text.replace("–", "-").split("-")]
    for token in tokens:
        if not token:
            continue
        normalised = token.replace("  ", " ")
        match = _COORD_PATTERN.search(normalised)
        if match:
            points.append(_coord_to_decimal(match))
    return points


def parse_sigmet_text(text: str) -> List[SIGMET]:
    """Parse SIGMET text block into SIGMET objects."""

    sigmets: List[SIGMET] = []
    blocks = [block.strip() for block in text.split("=") if block.strip()]

    for block in blocks:
        raw = block

        header_match = re.search(
            r"(?P<broadcast>[A-Z0-9]{6}\s+[A-Z]{4}\s+\d{6})\s+"
            r"(?P<fir>[A-Z]{4})\s+SIGMET\s+(?P<sequence>\S+)\s+VALID\s+"
            r"(?P<valid_from>\d{6})/(?P<valid_to>\d{6})",
            block,
        )

        fir = header_match.group("fir") if header_match else ""
        sequence = header_match.group("sequence") if header_match else None
        valid_from = header_match.group("valid_from") if header_match else ""
        valid_to = header_match.group("valid_to") if header_match else ""

        fir_name_match = re.search(r"([A-Z\s]+)\s+FIR", block)
        phenomenon_match = re.search(
            r"(SEV\s+TURB|SEV\s+ICE|SEV\s+TS|VA\s+ERUPTION\s+MT\s+[A-Z]+|VA\s+CLD|TC|RDOACT\s+CLD)",
            block,
        )

        obs_match = re.search(r"\b(OBS|FCST)\b", block)
        obs_time_match = re.search(r"AT\s+(\d{4})Z", block)
        levels_match = re.search(
            r"(SFC/FL\d{3}|FL\d{3}/FL\d{3}|FL\d{3}/\d{3})", block)
        movement_match = re.search(
            r"(MOV\s+[A-Z]{1,2}\s*\d{2,3}KT|STNR)", block)
        change_match = re.search(r"\b(NC|WKN|INTSF|DISS)\b", block)
        area_match = re.search(
            r"WI\s+(.+?)(SFC/FL\d{3}|FL\d{3}/FL\d{3}|FL\d{3}/\d{3}|MOV\s+[A-Z]|STNR|NC|WKN|INTSF|DISS)",
            block,
        )

        area_description = area_match.group(1).strip() if area_match else ""
        area_points = _parse_area_points(area_description)

        sigmets.append(
            SIGMET(
                raw_text=raw,
                sigmet_id=(header_match.group("broadcast")
                           if header_match else ""),
                fir=fir,
                sequence=sequence,
                phenomenon=phenomenon_match.group(
                    0) if phenomenon_match else "",
                observation_type=obs_match.group(0) if obs_match else None,
                observation_time=obs_time_match.group(
                    1) if obs_time_match else None,
                valid_from=valid_from,
                valid_to=valid_to,
                levels=levels_match.group(0) if levels_match else None,
                movement=movement_match.group(0) if movement_match else None,
                change=change_match.group(0) if change_match else None,
                area_description=area_description,
                area_points=area_points,
            )
        )

    return sigmets


def _demo() -> None:
    from pathlib import Path

    sample_path = Path("weather_data/SIGMET_example.txt")
    if not sample_path.exists():
        print("❌ Sample SIGMET file not found.")
        return

    sigmet_text = sample_path.read_text(encoding="utf-8")
    sigmets = parse_sigmet_text(sigmet_text)
    for sigmet in sigmets:
        print(sigmet)
        print(f"  FIR: {sigmet.fir} ({sigmet.sequence})")
        print(f"  Phenomenon: {sigmet.phenomenon}")
        print(
            f"  Observation: {sigmet.observation_type} at {sigmet.observation_time}Z")
        print(f"  Valid: {sigmet.valid_from} to {sigmet.valid_to}")
        print(f"  Levels: {sigmet.levels}")
        print(f"  Movement: {sigmet.movement}")
        print(f"  Change: {sigmet.change}")
        print(f"  Area points: {sigmet.area_points}")
        print()


if __name__ == "__main__":
    _demo()
