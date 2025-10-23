"""Canadian station catalog for Nav Canada integrations.

This module centralizes the curated list of Canadian aviation weather stations
used throughout the project. The list originates from the validation workflow
in ``data_query_canada_stations_v2.py`` and is shared by the SQLite repository
seed routine and data collection scripts.
"""

from __future__ import annotations

from typing import List

__all__ = [
    "CANADIAN_STATION_CODES",
    "INVALID_CANADIAN_STATIONS",
    "VALID_CANADIAN_STATIONS",
]

# Top Canadian airport stations (ICAO codes) sourced from Nav Canada queries.
CANADIAN_STATION_CODES: List[str] = [
    'CYYC', 'CYBW', 'CYOD', 'CYXD', 'CYEG', 'CYED', 'CZVL', 'CYPY', 'CYMM', 'CYQU',
    'CYOJ', 'CYQL', 'CYLL', 'CYXH', 'CYPE', 'CYQF', 'CYZH', 'CYZU', 'CYXX', 'CBBC',
    'CYBL', 'CYCG', 'CYQQ', 'CYXC', 'CYDQ', 'CYDL', 'CYYE', 'CYXJ', 'CYKA', 'CYLW',
    'CYZY', 'CZMT', 'CYCD', 'CYYF', 'CYZT', 'CYXS', 'CYPR', 'CYDC', 'CYQZ', 'CYZP',
    'CYYD', 'CYXT', 'CYAZ', 'CYVR', 'CYWH', 'CYYJ', 'CYWL', 'CYBR', 'CYYQ', 'CYDN',
    'CYGX', 'CYIV', 'CYYL', 'CYPG', 'CYQD', 'CYTH', 'CYWG', 'CYNE', 'CZBF', 'CYFC',
    'CYCX', 'CACQ', 'CYQM', 'CYSJ', 'CYSL', 'CYCA', 'CZUM', 'CYDF', 'CYQX', 'CYYR',
    'CWWU', 'CYMH', 'CYDP', 'CYAY', 'CYYT', 'CYJT', 'CYWK', 'CYZX', 'CYHZ', 'CWSA',
    'CYSA', 'CYAW', 'CYQY', 'CYQI', 'CYOA', 'CYWJ', 'CYGH', 'CZFM', 'CYFS', 'CYSM',
    'CYHY', 'CYHI', 'CYEV', 'CYLK', 'CYVQ', 'CYPC', 'CYRA', 'CYSY', 'CYUB', 'CYWE',
    'CYZF', 'CYLT', 'CYAB', 'CYEK', 'CYBK', 'CYVM', 'CYCB', 'CYTE', 'CYCO', 'CYZS',
    'CYCY', 'CYEU', 'CYFB', 'CYHK', 'CYUX', 'CYGT', 'CYWO', 'CYSR', 'CYXP', 'CYBB',
    'CYIO', 'CYRT', 'CYUT', 'CYRB', 'CYYH', 'CYTL', 'CYBN', 'CYLD', 'CYHD', 'CYXR',
    'CYEL', 'CYGQ', 'CYZE', 'CYHM', 'CYYU', 'CYQK', 'CYGK', 'CWSN', 'CYXU', 'CYSP',
    'CYMO', 'CYQA', 'CYYB', 'CYOW', 'CYWA', 'CYPQ', 'CYPL', 'CYRL', 'CYZR', 'CYAM',
    'CYXL', 'CYSN', 'CYSB', 'CYTJ', 'CYQT', 'CYTS', 'CYKZ', 'CYTZ', 'CYYZ', 'CYTR',
    'CYKF', 'CYXZ', 'CYVV', 'CYQG', 'CYYG', 'CYBG', 'CYBC', 'CYBX', 'CYMT', 'CYGP',
    'CYND', 'CYGV', 'CYGR', 'CYPH', 'CYIK', 'CYVP', 'CYGW', 'CYAH', 'CYGL', 'CYYY',
    'CYUL', 'CYMX', 'CYNA', 'CYPX', 'CYHA', 'CYQB', 'CYRJ', 'CYUY', 'CYHU', 'CYKL',
    'CYZV', 'CYSC', 'CYTQ', 'CYRQ', 'CYVO', 'CYOY', 'CYKQ', 'CYVT', 'CWVP', 'CYEN',
    'CYKJ', 'CYVC', 'CYMJ', 'CYQW', 'CYPA', 'CYQR', 'CYXE', 'CYSF', 'CYYN', 'CYQV',
    'CYDB', 'CYDA', 'CZFA', 'CYMA', 'CYOC', 'CYZW', 'CYQH', 'CYXY'
]

# Stations identified as invalid during validation campaigns.
INVALID_CANADIAN_STATIONS: List[str] = [
    'CACQ', 'CWSN', 'CWVP', 'CYTJ', 'CYWO', 'CYXD', 'CYKZ', 'CYSR'
]

VALID_CANADIAN_STATIONS: List[str] = [
    code for code in CANADIAN_STATION_CODES if code not in set(INVALID_CANADIAN_STATIONS)
]
