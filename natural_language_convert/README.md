Requirements

Python 3.10+

Built-in modules only (json, pathlib, dataclasses, argparse, etc.)

The parsed input file (e.g. test_group_01_parsed.json) must contain:

{
  "metars": {...},
  "tafs": {...},
  "upper_winds": [...]
}

🧩 Step-by-Step Usage
1️⃣ Navigate to the project root

2️⃣ Verify Python environment
python --version

3️⃣ Generate rule-based text (optional checks)

(preview individual sections if desired:)

Section	Command	Description

    METAR only	python -m natural_language_convert.run_group_metar	Generates METAR summaries per station

    TAF only	python -m natural_language_convert.run_group_taf	Generates TAF forecasts

    Upperwinds only	python -m natural_language_convert.run_group_upperwind	Generates winds-aloft summaries

    All combined	python -m natural_language_convert.run_group_all	Prints METAR + TAF + Upperwind sequentially

These print formatted text blocks to the terminal.

4️⃣ Build the final station_reports.json


Run the main builder:

python -m natural_language_convert.station_report


This:

- Reads data/test_group_01_parsed.json

- Converts all stations to natural language

- Writes the final structured file:

- data/station_reports.json


Output:

Wrote 9 StationReport objects to data/station_reports.json

🗃️ Output Format

Each JSON entry looks like:

{
  "station_id": "CYVR",
  "report_type": "Weather data -> Natural Language",
  "report_time": "2025-10-13T19:07:00",
  "valid_period": ["13/2140Z", "13/2140Z"],
  "report_data": "CYVR METAR: Winds WSW at 6 knots. ...\n\nCYVR TAF: ...\n\nCYVR Upperwinds: ..."
}

All text is UTF-8 encoded (ensure_ascii=False), so symbols like ° and – appear normally.


Notes for Integrators

station_reports.json updates (overwrites) each time you run the module.

Your teammate can read it using:

import json
reports = json.load(open("data/station_reports.json"))


Each object’s report_data is directly ready for:

- Text-to-Speech (TTS) conversion

- Route filtering / personalization


Missing sections are clearly labeled:

"no METAR available ..."

"no TAF available ..."

"no winds-aloft data available ..."