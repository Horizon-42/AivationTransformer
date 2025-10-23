import pytest

from upper_wind import _decode_upper_wind_cell


def test_decode_regular_entry_with_temperature():
    direction, speed, temperature = _decode_upper_wind_cell("30 118 -39", 30000)
    assert direction == 30
    assert speed == 118
    assert temperature == -39


def test_decode_high_speed_with_direction_offset():
    direction, speed, temperature = _decode_upper_wind_cell("731 06", 30000)
    assert direction == 230
    assert speed == 106
    assert temperature is None


def test_decode_compact_group_without_whitespace():
    direction, speed, temperature = _decode_upper_wind_cell("73106", 30000)
    assert direction == 230
    assert speed == 106
    assert temperature is None


def test_decode_calm_group():
    direction, speed, temperature = _decode_upper_wind_cell("9900", 3000)
    assert direction == 0
    assert speed == 0
    assert temperature is None
