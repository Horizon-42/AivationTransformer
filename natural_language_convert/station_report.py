class StationReport:
    def __init__(self, station_id, report_data, report_type, report_time, valid_period):
        self.station_id = station_id
        self.report_data = report_data
        self.report_type = report_type  # 'METAR' or 'TAF'
        self.report_time = report_time
        self.valid_period = valid_period  # (start_time, end_time)

a:StationReport = StationReport(
    station_id="KJFK",
    report_data="there will be light rain with a temperature of 75°F",
    report_type="METAR",
    report_time="2024-06-12T16:51:00Z",
    valid_period=("2024-06-12T16:00:00Z", "2024-06-12T17:00:00Z"))

print(a.station_id)  # Output: KJFK
reports:list[StationReport] = [a]
print(reports)  # Output: [<__main__.StationReport object at ...>]