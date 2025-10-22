"""
SIGMET Data Model and Parser

Provides a class for SIGMET aviation weather advisories and a parser for standard ICAO/WMO SIGMET text format.
"""
import re
from typing import List, Optional

class SIGMET:
    """
    Represents a single SIGMET advisory.
    """
    def __init__(self,
                 raw_text: str,
                 sigmet_id: str,
                 fir: str,
                 phenomenon: str,
                 valid_from: str,
                 valid_to: str,
                 location: str,
                 levels: str,
                 movement: str,
                 change: str):
        self.raw_text = raw_text
        self.sigmet_id = sigmet_id
        self.fir = fir
        self.phenomenon = phenomenon
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.location = location  # Polygon or area string
        self.levels = levels      # e.g. SFC/FL100, FL120/240
        self.movement = movement  # e.g. MOV NE 05KT
        self.change = change      # e.g. NC, WKN

    def __repr__(self):
        return f"SIGMET({self.sigmet_id}, {self.fir}, {self.phenomenon}, {self.valid_from}-{self.valid_to})"


def parse_sigmet_text(text: str) -> List[SIGMET]:
    """
    Parse SIGMET text block into SIGMET objects.
    Args:
        text: Raw SIGMET text (multiple advisories)
    Returns:
        List of SIGMET objects
    """
    sigmets = []
    # Split advisories by '='
    blocks = [b.strip() for b in text.split('=') if b.strip()]
    for block in blocks:
        raw = block
        # Extract SIGMET ID and FIR
        m_id = re.search(r'(SIGMET\s+\d+|SIGMET\s+[A-Z0-9]+)', block)
        sigmet_id = m_id.group(0) if m_id else ''
        m_fir = re.search(r'([A-Z]{4,6}\s+FIR)', block)
        fir = m_fir.group(0).replace('FIR','').strip() if m_fir else ''
        # Extract phenomenon
        m_phen = re.search(r'(SEV\s+TURB|SEV\s+ICE|VA\s+ERUPTION|VA\s+CLD)', block)
        phenomenon = m_phen.group(0) if m_phen else ''
        # Extract validity
        m_valid = re.search(r'VALID\s+(\d{6})/(\d{6})', block)
        valid_from = m_valid.group(1) if m_valid else ''
        valid_to = m_valid.group(2) if m_valid else ''
        # Extract location polygon
        m_loc = re.search(r'WI\s+([A-Z0-9\s\-\.]+?)(SFC/FL|FL\d{3}/\d{3}|MOV|WKN|NC)', block)
        location = m_loc.group(1).strip() if m_loc else ''
        # Extract levels
        m_lvl = re.search(r'(SFC/FL\d{3}|FL\d{3}/\d{3})', block)
        levels = m_lvl.group(0) if m_lvl else ''
        # Extract movement
        m_mov = re.search(r'MOV\s+[A-Z]{2,3}\s*\d{2,3}KT', block)
        movement = m_mov.group(0) if m_mov else ''
        # Extract change
        m_chg = re.search(r'(NC|WKN|INTSF|DISS)', block)
        change = m_chg.group(0) if m_chg else ''
        sigmets.append(SIGMET(
            raw_text=raw,
            sigmet_id=sigmet_id,
            fir=fir,
            phenomenon=phenomenon,
            valid_from=valid_from,
            valid_to=valid_to,
            location=location,
            levels=levels,
            movement=movement,
            change=change
        ))
    return sigmets

# --- Test logic ---
if __name__ == "__main__":
    with open("weather_data/SIGMET_example.txt", "r") as f:
        sigmet_text = f.read()
    sigmets = parse_sigmet_text(sigmet_text)
    for s in sigmets:
        print(s)
        print(f"  FIR: {s.fir}")
        print(f"  Phenomenon: {s.phenomenon}")
        print(f"  Valid: {s.valid_from} to {s.valid_to}")
        print(f"  Location: {s.location}")
        print(f"  Levels: {s.levels}")
        print(f"  Movement: {s.movement}")
        print(f"  Change: {s.change}")
        print()
