class StationReport:
    def __init__(self, station_id, report_data, report_type, report_time, valid_period):
        self.station_id = station_id
        self.report_data = report_data
        self.report_type = report_type  # 'METAR' or 'TAF'
        self.report_time = report_time
        self.valid_period = valid_period  # (start_time, end_time)


list[StationReport] = []