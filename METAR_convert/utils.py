"""Shared utility functions for the METAR_convert package."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def parse_iso8601(value: Optional[str]) -> datetime:
    """Parse a potentially simple ISO-8601 string into a timezone-aware datetime.
    
    This function handles various ISO-8601 formats and edge cases:
    - Standard ISO format with 'Z' suffix
    - Datetime objects (adds timezone if missing)
    - Invalid/empty values (returns current UTC time)
    
    Args:
        value: ISO-8601 string, datetime object, or None
        
    Returns:
        Timezone-aware datetime object
        
    Examples:
        >>> parse_iso8601("2025-10-24T15:30:00Z")
        datetime(2025, 10, 24, 15, 30, tzinfo=timezone.utc)
        
        >>> parse_iso8601(None)
        # Returns current UTC time
    """
    if not value:
        return datetime.now(timezone.utc)

    try:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def from_timestamp(value: Optional[float]) -> datetime:
    """Convert epoch seconds into a UTC datetime.
    
    Args:
        value: Unix timestamp as float/int or None
        
    Returns:
        Timezone-aware datetime object
        
    Examples:
        >>> from_timestamp(1698163800.0)
        datetime(2023, 10, 24, 15, 30, tzinfo=timezone.utc)
        
        >>> from_timestamp(None)
        # Returns current UTC time
    """
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (ValueError, OSError):
        return datetime.now(timezone.utc)


def decode_temperature_code(code: str) -> Optional[int]:
    """Decode two-digit temperature codes used below 24,000 ft in upper wind data.
    
    Temperature codes are offset by 50 and represent negative values.
    For example: '52' = -2°C, '99' = -49°C
    
    Args:
        code: Two-digit temperature code string
        
    Returns:
        Temperature in Celsius or None if invalid
        
    Examples:
        >>> decode_temperature_code("52")
        -2
        
        >>> decode_temperature_code("99")
        -49
        
        >>> decode_temperature_code("invalid")
        None
    """
    if not code or not code.isdigit():
        return None
    
    try:
        # Temperature codes are offset by 50 and represent negative values
        temp_code = int(code)
        if temp_code < 50:
            return None
        return -(temp_code - 50)
    except ValueError:
        return None


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit.
    
    Args:
        celsius: Temperature in Celsius
        
    Returns:
        Temperature in Fahrenheit
        
    Examples:
        >>> celsius_to_fahrenheit(0)
        32.0
        
        >>> celsius_to_fahrenheit(25)
        77.0
    """
    return (celsius * 9/5) + 32


def knots_to_mph(knots: float) -> float:
    """Convert wind speed from knots to miles per hour.
    
    Args:
        knots: Speed in knots
        
    Returns:
        Speed in miles per hour
        
    Examples:
        >>> knots_to_mph(10)
        11.5078
        
        >>> knots_to_mph(0)
        0.0
    """
    return knots * 1.15078


def hpa_to_inches_hg(hpa: float) -> float:
    """Convert pressure from hectopascals to inches of mercury.
    
    Args:
        hpa: Pressure in hectopascals (hPa)
        
    Returns:
        Pressure in inches of mercury
        
    Examples:
        >>> hpa_to_inches_hg(1013.25)
        29.921...
        
        >>> hpa_to_inches_hg(1000)
        29.53
    """
    return hpa * 0.02953


def inches_hg_to_hpa(inches_hg: float) -> float:
    """Convert pressure from inches of mercury to hectopascals.
    
    Args:
        inches_hg: Pressure in inches of mercury
        
    Returns:
        Pressure in hectopascals (hPa)
        
    Examples:
        >>> inches_hg_to_hpa(29.92)
        1013.25...
        
        >>> inches_hg_to_hpa(30.0)
        1015.96...
    """
    return inches_hg * 33.8639