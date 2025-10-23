"""SQLite-backed persistence for aviation weather data."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Protocol, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    select,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from metar import METAR
from sigmet import SIGMET
from taf import TAF
from upper_wind import UpperWind

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from navcanada_weather_server import NavCanadaWeatherResponse

# ---------------------------------------------------------------------------
# SQLAlchemy base / ORM models
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for ORM models."""


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elevation_meters: Mapped[Optional[int]
                             ] = mapped_column(Integer, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(
        String(4), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    metar_reports: Mapped[List["MetarObservation"]] = relationship(
        back_populates="station", cascade="all, delete", passive_deletes=True
    )
    taf_reports: Mapped[List["TafBulletin"]] = relationship(
        back_populates="station", cascade="all, delete", passive_deletes=True
    )
    upper_wind_periods: Mapped[List["UpperWindPeriodRecord"]] = relationship(
        back_populates="station", cascade="all, delete", passive_deletes=True
    )


class MetarObservation(Base):
    __tablename__ = "metar_observations"
    __table_args__ = (
        UniqueConstraint("station_id", "observation_time", name="uq_metar_station_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), index=True
    )

    observation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    receipt_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observation_timestamp: Mapped[int] = mapped_column(Integer)

    temperature_celsius: Mapped[float] = mapped_column(Float)
    dewpoint_celsius: Mapped[float] = mapped_column(Float)
    wind_direction_degrees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_speed_knots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_gust_knots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_variable: Mapped[bool] = mapped_column(Boolean, default=False)

    visibility: Mapped[str] = mapped_column(String(16))
    visibility_meters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    altimeter_hpa: Mapped[float] = mapped_column(Float)
    sea_level_pressure_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pressure_tendency_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    sky_coverage: Mapped[str] = mapped_column(String(8))
    flight_category: Mapped[str] = mapped_column(String(8))
    max_temperature_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_temperature_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    quality_control_field: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    report_type: Mapped[str] = mapped_column(String(10))
    raw_observation: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    station: Mapped["Station"] = relationship(back_populates="metar_reports")

    cloud_layers: Mapped[List["MetarCloudLayer"]] = relationship(
        back_populates="metar", cascade="all, delete-orphan"
    )
    weather: Mapped[List["MetarWeatherPhenomenon"]] = relationship(
        back_populates="metar", cascade="all, delete-orphan"
    )


class MetarCloudLayer(Base):
    __tablename__ = "metar_cloud_layers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metar_id: Mapped[int] = mapped_column(
        ForeignKey("metar_observations.id", ondelete="CASCADE"), index=True
    )
    coverage: Mapped[str] = mapped_column(String(8))
    altitude_feet: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cloud_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    metar: Mapped["MetarObservation"] = relationship(back_populates="cloud_layers")


class MetarWeatherPhenomenon(Base):
    __tablename__ = "metar_weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metar_id: Mapped[int] = mapped_column(
        ForeignKey("metar_observations.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(16))

    metar: Mapped["MetarObservation"] = relationship(back_populates="weather")


class TafBulletin(Base):
    __tablename__ = "taf_bulletins"
    __table_args__ = (
        UniqueConstraint("station_id", "issue_time", name="uq_taf_station_issue"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), index=True
    )

    bulletin_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    issue_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    database_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_from_timestamp: Mapped[int] = mapped_column(Integer)
    valid_to_timestamp: Mapped[int] = mapped_column(Integer)

    is_most_recent: Mapped[bool] = mapped_column(Boolean, default=True)
    is_prior_version: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_taf: Mapped[str] = mapped_column(Text)
    remarks: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    station: Mapped["Station"] = relationship(back_populates="taf_reports")

    forecast_periods: Mapped[List["TafForecastPeriodRecord"]] = relationship(
        back_populates="taf", cascade="all, delete-orphan"
    )


class TafForecastPeriodRecord(Base):
    __tablename__ = "taf_forecast_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taf_id: Mapped[int] = mapped_column(ForeignKey("taf_bulletins.id", ondelete="CASCADE"), index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_from_timestamp: Mapped[int] = mapped_column(Integer)
    valid_to_timestamp: Mapped[int] = mapped_column(Integer)
    becomes_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    forecast_change_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    probability_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    wind_direction_degrees: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    wind_speed_knots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_gust_knots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    wind_shear_height_feet: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_shear_direction_degrees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_shear_speed_knots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    visibility: Mapped[str] = mapped_column(String(16))
    vertical_visibility_feet: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weather_phenomena: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    altimeter_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    not_decoded: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cloud_layers: Mapped[List["TafCloudLayerRecord"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    icing_turbulence: Mapped[List["TafIcingTurbulenceRecord"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    temperature_forecasts: Mapped[List["TafTemperatureForecastRecord"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )

    taf: Mapped["TafBulletin"] = relationship(back_populates="forecast_periods")


class TafCloudLayerRecord(Base):
    __tablename__ = "taf_cloud_layers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        ForeignKey("taf_forecast_periods.id", ondelete="CASCADE"), index=True
    )
    coverage: Mapped[str] = mapped_column(String(8))
    base_altitude_feet: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cloud_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    period: Mapped["TafForecastPeriodRecord"] = relationship(back_populates="cloud_layers")


class TafIcingTurbulenceRecord(Base):
    __tablename__ = "taf_icing_turbulence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        ForeignKey("taf_forecast_periods.id", ondelete="CASCADE"), index=True
    )
    intensity: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    base_altitude_feet: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    top_altitude_feet: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    period: Mapped["TafForecastPeriodRecord"] = relationship(back_populates="icing_turbulence")


class TafTemperatureForecastRecord(Base):
    __tablename__ = "taf_temperature_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        ForeignKey("taf_forecast_periods.id", ondelete="CASCADE"), index=True
    )
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    period: Mapped["TafForecastPeriodRecord"] = relationship(back_populates="temperature_forecasts")


class UpperWindPeriodRecord(Base):
    __tablename__ = "upper_wind_periods"
    __table_args__ = (
        UniqueConstraint(
            "station_id", "valid_time", "use_period", name="uq_upper_wind_identity"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), index=True
    )
    valid_time: Mapped[str] = mapped_column(String(16))
    use_period: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    levels: Mapped[List["UpperWindLevelRecord"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )

    station: Mapped["Station"] = relationship(
        back_populates="upper_wind_periods")


class UpperWindLevelRecord(Base):
    __tablename__ = "upper_wind_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        ForeignKey("upper_wind_periods.id", ondelete="CASCADE"), index=True
    )
    altitude_ft: Mapped[int] = mapped_column(Integer)
    direction_deg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    speed_kt: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature_c: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    period: Mapped["UpperWindPeriodRecord"] = relationship(back_populates="levels")


class SigmetReport(Base):
    __tablename__ = "sigmet_reports"
    __table_args__ = (
        UniqueConstraint("sigmet_identifier", name="uq_sigmet_identifier"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigmet_identifier: Mapped[str] = mapped_column(String(64))
    fir: Mapped[str] = mapped_column(String(8))
    sequence: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    phenomenon: Mapped[str] = mapped_column(String(40))
    observation_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    observation_time: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    valid_from: Mapped[str] = mapped_column(String(12))
    valid_to: Mapped[str] = mapped_column(String(12))
    levels: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    movement: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    change: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    area_description: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    area_points: Mapped[List["SigmetAreaPointRecord"]] = relationship(
        back_populates="sigmet", cascade="all, delete-orphan"
    )


class SigmetAreaPointRecord(Base):
    __tablename__ = "sigmet_area_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigmet_id: Mapped[int] = mapped_column(
        ForeignKey("sigmet_reports.id", ondelete="CASCADE"), index=True
    )
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    sigmet: Mapped["SigmetReport"] = relationship(back_populates="area_points")


# ---------------------------------------------------------------------------
# Repository protocol & implementation
# ---------------------------------------------------------------------------


class WeatherRepository(Protocol):
    """Protocol describing persistence behaviour used by the server."""

    def store_response(self, response: "NavCanadaWeatherResponse") -> None:
        ...

    def close(self) -> None:
        ...


class SQLiteWeatherRepository:
    """SQLite-backed repository that persists decoded weather objects via SQLAlchemy."""

    def __init__(self, db_path: str | Path = "weather_data/weather.db", echo: bool = False) -> None:
        if isinstance(db_path, Path):
            db_url = f"sqlite:///{db_path.expanduser().resolve()}"
        else:
            db_url = db_path if db_path.startswith("sqlite") else f"sqlite:///{Path(db_path).expanduser().resolve()}"

        self.engine = create_engine(db_url, echo=echo, future=True)
        self._apply_legacy_migrations()
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)
        self._seed_canadian_stations()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def store_response(self, response: "NavCanadaWeatherResponse") -> None:
        """Persist the NavCanada weather response to SQLite."""
        with self._session_scope() as session:
            self._store_metars(session, response.metars)
            self._store_tafs(session, response.tafs)
            self._store_upper_winds(session, response.upper_winds)
            self._store_sigmets(session, response.sigmets)

    def close(self) -> None:
        """Dispose the underlying SQLAlchemy engine."""
        self.engine.dispose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @contextmanager
    def _session_scope(self) -> Session:
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _seed_canadian_stations(self) -> None:
        """Populate the stations table with vetted Canadian stations if missing."""
        try:
            from canadian_station_catalog import VALID_CANADIAN_STATIONS
            from station_lookup import StationDatabase
        except Exception:
            # Seeding is a best-effort enrichment; skip if dependencies are unavailable.
            return

        target_ids = {code.strip().upper()
                      for code in VALID_CANADIAN_STATIONS if code}
        if not target_ids:
            return

        target_list = sorted(target_ids)

        with self._session_scope() as session:
            existing_ids = set(
                session.scalars(select(Station.id).where(
                    Station.id.in_(target_list)))
            )
            missing = [code for code in target_list if code not in existing_ids]
            if not missing:
                return

            db = StationDatabase()
            for code in missing:
                info = db.lookup(code) or {}
                self._upsert_station(
                    session,
                    code,
                    name=info.get("name"),
                    latitude=info.get("latitude"),
                    longitude=info.get("longitude"),
                    elevation_meters=info.get("elevation_m"),
                    country_code="CA",
                    region=info.get("province"),
                )

    # ------------------------------------------------------------------
    # Station management helpers
    # ------------------------------------------------------------------
    def _upsert_station(
        self,
        session: Session,
        station_id: str,
        *,
        name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        elevation_meters: Optional[int] = None,
        country_code: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Optional[Station]:
        station_id = (station_id or "").strip().upper()
        if not station_id:
            return None

        station: Optional[Station] = session.get(Station, station_id)

        name_value = self._clean_station_str(name)
        latitude_value = self._clean_station_float(latitude)
        longitude_value = self._clean_station_float(longitude)
        elevation_value = self._clean_station_int(elevation_meters)
        country_value = self._clean_station_str(country_code)
        region_value = self._clean_station_str(region)

        if station is None:
            station = Station(
                id=station_id,
                name=name_value,
                latitude=latitude_value,
                longitude=longitude_value,
                elevation_meters=elevation_value,
                country_code=country_value,
                region=region_value,
            )
            session.add(station)
            return station

        updated = False

        if name_value and station.name != name_value:
            station.name = name_value
            updated = True
        if latitude_value is not None:
            if station.latitude is None or abs(latitude_value) > 1e-6:
                if station.latitude != latitude_value:
                    station.latitude = latitude_value
                    updated = True
        if longitude_value is not None:
            if station.longitude is None or abs(longitude_value) > 1e-6:
                if station.longitude != longitude_value:
                    station.longitude = longitude_value
                    updated = True
        if elevation_value is not None:
            if station.elevation_meters is None or elevation_value != 0:
                if station.elevation_meters != elevation_value:
                    station.elevation_meters = elevation_value
                    updated = True
        if country_value and station.country_code != country_value:
            station.country_code = country_value
            updated = True
        if region_value and station.region != region_value:
            station.region = region_value
            updated = True

        if updated:
            station.updated_at = datetime.utcnow()

        return station

    @staticmethod
    def _clean_station_str(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _clean_station_float(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        return round(numeric, 6)

    @staticmethod
    def _clean_station_int(value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            return None
        return numeric

    def _store_metars(self, session: Session, metars: Dict[str, List[METAR]]) -> None:
        for station_metars in metars.values():
            for metar in station_metars:
                station = self._upsert_station(
                    session,
                    metar.station_id,
                    name=metar.station_name,
                    latitude=metar.latitude,
                    longitude=metar.longitude,
                    elevation_meters=metar.elevation_meters,
                )
                if station is None:
                    continue

                session.execute(
                    delete(MetarObservation)
                    .where(MetarObservation.station_id == metar.station_id)
                    .where(MetarObservation.observation_time == metar.observation_time)
                )

                record = MetarObservation(
                    station_id=metar.station_id,
                    observation_time=metar.observation_time,
                    receipt_time=metar.receipt_time,
                    observation_timestamp=metar.observation_timestamp,
                    temperature_celsius=metar.temperature_celsius,
                    dewpoint_celsius=metar.dewpoint_celsius,
                    wind_direction_degrees=metar.wind_direction_degrees,
                    wind_speed_knots=metar.wind_speed_knots,
                    wind_gust_knots=metar.wind_gust_knots,
                    wind_variable=metar.wind_variable,
                    visibility=metar.visibility,
                    visibility_meters=metar.visibility_meters,
                    altimeter_hpa=metar.altimeter_hpa,
                    sea_level_pressure_hpa=metar.sea_level_pressure_hpa,
                    pressure_tendency_hpa=metar.pressure_tendency_hpa,
                    sky_coverage=metar.sky_coverage,
                    flight_category=metar.flight_category,
                    max_temperature_celsius=metar.max_temperature_celsius,
                    min_temperature_celsius=metar.min_temperature_celsius,
                    quality_control_field=metar.quality_control_field,
                    report_type=metar.report_type,
                    raw_observation=metar.raw_observation,
                    cloud_layers=[
                        MetarCloudLayer(
                            coverage=layer.coverage,
                            altitude_feet=layer.altitude_feet,
                            cloud_type=layer.cloud_type,
                        )
                        for layer in metar.cloud_layers
                    ],
                    weather=[
                        MetarWeatherPhenomenon(code=code)
                        for code in metar.present_weather
                        if code
                    ],
                )
                session.add(record)

    def _store_tafs(self, session: Session, tafs: Dict[str, List[TAF]]) -> None:
        for station_tafs in tafs.values():
            for taf in station_tafs:
                station = self._upsert_station(
                    session,
                    taf.station_id,
                    name=taf.station_name,
                    latitude=taf.latitude,
                    longitude=taf.longitude,
                    elevation_meters=taf.elevation_meters,
                )
                if station is None:
                    continue

                session.execute(
                    delete(TafBulletin)
                    .where(TafBulletin.station_id == taf.station_id)
                    .where(TafBulletin.issue_time == taf.issue_time)
                )

                record = TafBulletin(
                    station_id=taf.station_id,
                    bulletin_time=taf.bulletin_time,
                    issue_time=taf.issue_time,
                    database_time=taf.database_time,
                    valid_from=taf.valid_from,
                    valid_to=taf.valid_to,
                    valid_from_timestamp=taf.valid_from_timestamp,
                    valid_to_timestamp=taf.valid_to_timestamp,
                    is_most_recent=taf.is_most_recent,
                    is_prior_version=taf.is_prior_version,
                    raw_taf=taf.raw_taf,
                    remarks=taf.remarks,
                    forecast_periods=[
                        TafForecastPeriodRecord(
                            valid_from=period.valid_from,
                            valid_to=period.valid_to,
                            valid_from_timestamp=period.valid_from_timestamp,
                            valid_to_timestamp=period.valid_to_timestamp,
                            becomes_time=period.becomes_time,
                            forecast_change_type=period.forecast_change_type,
                            probability_percent=period.probability_percent,
                            wind_direction_degrees=(
                                str(period.wind_direction_degrees)
                                if period.wind_direction_degrees is not None
                                else None
                            ),
                            wind_speed_knots=period.wind_speed_knots,
                            wind_gust_knots=period.wind_gust_knots,
                            wind_shear_height_feet=period.wind_shear_height_feet,
                            wind_shear_direction_degrees=period.wind_shear_direction_degrees,
                            wind_shear_speed_knots=period.wind_shear_speed_knots,
                            visibility=period.visibility,
                            vertical_visibility_feet=period.vertical_visibility_feet,
                            weather_phenomena=period.weather_phenomena,
                            altimeter_hpa=period.altimeter_hpa,
                            not_decoded=period.not_decoded,
                            cloud_layers=[
                                TafCloudLayerRecord(
                                    coverage=layer.coverage,
                                    base_altitude_feet=layer.base_altitude_feet,
                                    cloud_type=layer.cloud_type,
                                )
                                for layer in period.cloud_layers
                            ],
                            icing_turbulence=[
                                TafIcingTurbulenceRecord(
                                    intensity=item.intensity,
                                    type=item.type,
                                    base_altitude_feet=item.base_altitude_feet,
                                    top_altitude_feet=item.top_altitude_feet,
                                )
                                for item in period.icing_turbulence
                            ],
                            temperature_forecasts=[
                                TafTemperatureForecastRecord(
                                    temperature_celsius=temp.temperature_celsius,
                                    time=temp.time,
                                )
                                for temp in period.temperature_forecasts
                            ],
                        )
                        for period in taf.forecast_periods
                    ],
                )
                session.add(record)

    def _store_upper_winds(self, session: Session, upper_winds: List[UpperWind]) -> None:
        for upper_wind in upper_winds:
            station = self._upsert_station(session, upper_wind.station)
            if station is None:
                continue
            for period in upper_wind.periods:
                session.execute(
                    delete(UpperWindPeriodRecord)
                    .where(UpperWindPeriodRecord.station_id == upper_wind.station)
                    .where(UpperWindPeriodRecord.valid_time == period.valid_time)
                    .where(UpperWindPeriodRecord.use_period == period.use_period)
                )

                record = UpperWindPeriodRecord(
                    station_id=upper_wind.station,
                    valid_time=period.valid_time,
                    use_period=period.use_period,
                    levels=[
                        UpperWindLevelRecord(
                            altitude_ft=level.altitude_ft,
                            direction_deg=level.direction_deg,
                            speed_kt=level.speed_kt,
                            temperature_c=level.temperature_c,
                        )
                        for level in period.levels
                    ],
                )
                session.add(record)

    def _store_sigmets(self, session: Session, sigmets: List[SIGMET]) -> None:
        for sigmet in sigmets:
            identifier = sigmet.sigmet_id or f"{sigmet.fir}-{sigmet.valid_from}-{sigmet.valid_to}"
            session.execute(
                delete(SigmetReport).where(SigmetReport.sigmet_identifier == identifier)
            )

            record = SigmetReport(
                sigmet_identifier=identifier,
                fir=sigmet.fir,
                sequence=sigmet.sequence,
                phenomenon=sigmet.phenomenon,
                observation_type=sigmet.observation_type,
                observation_time=sigmet.observation_time,
                valid_from=sigmet.valid_from,
                valid_to=sigmet.valid_to,
                levels=sigmet.levels,
                movement=sigmet.movement,
                change=sigmet.change,
                area_description=sigmet.area_description,
                raw_text=sigmet.raw_text,
                area_points=[
                    SigmetAreaPointRecord(
                        latitude=point["latitude"],
                        longitude=point["longitude"],
                    )
                    for point in sigmet.area_points
                ],
            )
            session.add(record)

    # ------------------------------------------------------------------
    # Schema migrations
    # ------------------------------------------------------------------
    def _apply_legacy_migrations(self) -> None:
        """Handle schema adjustments for previously created databases."""
        try:
            with self.engine.begin() as connection:
                self._drop_legacy_taf_index(connection)
                self._ensure_station_catalog(connection)
                self._populate_station_catalog(connection)

                if self._table_has_legacy_station_fields(connection, "metar_observations"):
                    self._rebuild_metar_observations(connection)

                if self._table_has_legacy_station_fields(connection, "taf_bulletins"):
                    self._rebuild_taf_bulletins(connection)

                if not self._upper_wind_periods_have_station_fk(connection):
                    self._rebuild_upper_wind_periods(connection)

                if self._taf_forecast_periods_has_legacy_unique(connection):
                    self._rebuild_taf_forecast_periods(connection)
        except Exception:
            # Best-effort migration; ignore if database is fresh or index missing
            pass

    # ------------------------------------------------------------------
    # Migration helpers
    # ------------------------------------------------------------------
    def _drop_legacy_taf_index(self, connection) -> None:
        connection.execute(text("DROP INDEX IF EXISTS uq_taf_period_identity"))

    def _ensure_station_catalog(self, connection) -> None:
        if self._table_exists(connection, "stations"):
            return

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS stations (
                    id VARCHAR(8) PRIMARY KEY,
                    name VARCHAR(128),
                    latitude FLOAT,
                    longitude FLOAT,
                    elevation_meters INTEGER,
                    country_code VARCHAR(4),
                    region VARCHAR(8),
                    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

    def _populate_station_catalog(self, connection) -> None:
        if not self._table_exists(connection, "stations"):
            return

        if self._table_has_legacy_station_fields(connection, "metar_observations"):
            self._populate_station_catalog_from_table(
                connection, "metar_observations")

        if self._table_has_legacy_station_fields(connection, "taf_bulletins"):
            self._populate_station_catalog_from_table(
                connection, "taf_bulletins")

    def _populate_station_catalog_from_table(self, connection, table_name: str) -> None:
        connection.execute(
            text(
                f"""
                INSERT INTO stations (id, name, latitude, longitude, elevation_meters)
                SELECT
                    TRIM(station_id) AS station_id,
                    MAX(NULLIF(station_name, '')) AS station_name,
                    MAX(NULLIF(latitude, 0)) AS latitude,
                    MAX(NULLIF(longitude, 0)) AS longitude,
                    MAX(NULLIF(elevation_meters, 0)) AS elevation_meters
                FROM {table_name}
                WHERE station_id IS NOT NULL AND TRIM(station_id) != ''
                GROUP BY TRIM(station_id)
                ON CONFLICT(id) DO UPDATE SET
                    name = COALESCE(excluded.name, stations.name),
                    latitude = COALESCE(excluded.latitude, stations.latitude),
                    longitude = COALESCE(excluded.longitude, stations.longitude),
                    elevation_meters = COALESCE(excluded.elevation_meters, stations.elevation_meters),
                    updated_at = CURRENT_TIMESTAMP
                """
            )
        )

    def _table_exists(self, connection, table_name: str) -> bool:
        result = connection.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table_name},
        ).scalar()
        return bool(result)

    def _get_table_columns(self, connection, table_name: str) -> set[str]:
        if not self._table_exists(connection, table_name):
            return set()

        rows = connection.execute(
            text(f"PRAGMA table_info('{table_name}')")).fetchall()
        return {row[1] for row in rows}

    def _table_has_legacy_station_fields(self, connection, table_name: str) -> bool:
        legacy_columns = {"station_name", "latitude",
                          "longitude", "elevation_meters"}
        columns = self._get_table_columns(connection, table_name)
        return bool(columns) and legacy_columns.issubset(columns)

    def _upper_wind_periods_have_station_fk(self, connection) -> bool:
        if not self._table_exists(connection, "upper_wind_periods"):
            return True

        refs = connection.execute(
            text("PRAGMA foreign_key_list('upper_wind_periods')")).fetchall()
        return any(row[2] == "stations" for row in refs)

    def _taf_forecast_periods_has_legacy_unique(self, connection) -> bool:
        if not self._table_exists(connection, "taf_forecast_periods"):
            return False

        schema_sql = connection.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='taf_forecast_periods'"
            )
        ).scalar()
        return bool(schema_sql and "UNIQUE" in schema_sql.upper())

    def _rebuild_metar_observations(self, connection) -> None:
        try:
            connection.execute(text("PRAGMA foreign_keys=OFF"))
            connection.execute(
                text("DROP TABLE IF EXISTS metar_observations__new"))
            connection.execute(
                text(
                    """
                    CREATE TABLE metar_observations__new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        station_id VARCHAR(8) NOT NULL,
                        observation_time TIMESTAMP NOT NULL,
                        receipt_time TIMESTAMP NOT NULL,
                        observation_timestamp INTEGER NOT NULL,
                        temperature_celsius FLOAT NOT NULL,
                        dewpoint_celsius FLOAT NOT NULL,
                        wind_direction_degrees INTEGER,
                        wind_speed_knots INTEGER,
                        wind_gust_knots INTEGER,
                        wind_variable BOOLEAN NOT NULL DEFAULT 0,
                        visibility VARCHAR(16) NOT NULL,
                        visibility_meters INTEGER,
                        altimeter_hpa FLOAT NOT NULL,
                        sea_level_pressure_hpa FLOAT,
                        pressure_tendency_hpa FLOAT,
                        sky_coverage VARCHAR(8) NOT NULL,
                        flight_category VARCHAR(8) NOT NULL,
                        max_temperature_celsius FLOAT,
                        min_temperature_celsius FLOAT,
                        quality_control_field INTEGER,
                        report_type VARCHAR(10) NOT NULL,
                        raw_observation TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(station_id, observation_time),
                        FOREIGN KEY(station_id) REFERENCES stations(id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO metar_observations__new (
                        id,
                        station_id,
                        observation_time,
                        receipt_time,
                        observation_timestamp,
                        temperature_celsius,
                        dewpoint_celsius,
                        wind_direction_degrees,
                        wind_speed_knots,
                        wind_gust_knots,
                        wind_variable,
                        visibility,
                        visibility_meters,
                        altimeter_hpa,
                        sea_level_pressure_hpa,
                        pressure_tendency_hpa,
                        sky_coverage,
                        flight_category,
                        max_temperature_celsius,
                        min_temperature_celsius,
                        quality_control_field,
                        report_type,
                        raw_observation,
                        created_at
                    )
                    SELECT
                        id,
                        station_id,
                        observation_time,
                        receipt_time,
                        observation_timestamp,
                        temperature_celsius,
                        dewpoint_celsius,
                        wind_direction_degrees,
                        wind_speed_knots,
                        wind_gust_knots,
                        wind_variable,
                        visibility,
                        visibility_meters,
                        altimeter_hpa,
                        sea_level_pressure_hpa,
                        pressure_tendency_hpa,
                        sky_coverage,
                        flight_category,
                        max_temperature_celsius,
                        min_temperature_celsius,
                        quality_control_field,
                        report_type,
                        raw_observation,
                        created_at
                    FROM metar_observations
                    """
                )
            )
            connection.execute(text("DROP TABLE metar_observations"))
            connection.execute(
                text("ALTER TABLE metar_observations__new RENAME TO metar_observations"))
        finally:
            connection.execute(text("PRAGMA foreign_keys=ON"))

        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_metar_observations_station_id ON metar_observations (station_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_metar_observations_observation_time ON metar_observations (observation_time)"
            )
        )

    def _rebuild_taf_bulletins(self, connection) -> None:
        try:
            connection.execute(text("PRAGMA foreign_keys=OFF"))
            connection.execute(text("DROP TABLE IF EXISTS taf_bulletins__new"))
            connection.execute(
                text(
                    """
                    CREATE TABLE taf_bulletins__new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        station_id VARCHAR(8) NOT NULL,
                        bulletin_time TIMESTAMP NOT NULL,
                        issue_time TIMESTAMP NOT NULL,
                        database_time TIMESTAMP NOT NULL,
                        valid_from TIMESTAMP NOT NULL,
                        valid_to TIMESTAMP NOT NULL,
                        valid_from_timestamp INTEGER NOT NULL,
                        valid_to_timestamp INTEGER NOT NULL,
                        is_most_recent BOOLEAN NOT NULL DEFAULT 1,
                        is_prior_version BOOLEAN NOT NULL DEFAULT 0,
                        raw_taf TEXT NOT NULL,
                        remarks TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(station_id, issue_time),
                        FOREIGN KEY(station_id) REFERENCES stations(id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO taf_bulletins__new (
                        id,
                        station_id,
                        bulletin_time,
                        issue_time,
                        database_time,
                        valid_from,
                        valid_to,
                        valid_from_timestamp,
                        valid_to_timestamp,
                        is_most_recent,
                        is_prior_version,
                        raw_taf,
                        remarks,
                        created_at
                    )
                    SELECT
                        id,
                        station_id,
                        bulletin_time,
                        issue_time,
                        database_time,
                        valid_from,
                        valid_to,
                        valid_from_timestamp,
                        valid_to_timestamp,
                        is_most_recent,
                        is_prior_version,
                        raw_taf,
                        remarks,
                        created_at
                    FROM taf_bulletins
                    """
                )
            )
            connection.execute(text("DROP TABLE taf_bulletins"))
            connection.execute(
                text("ALTER TABLE taf_bulletins__new RENAME TO taf_bulletins"))
        finally:
            connection.execute(text("PRAGMA foreign_keys=ON"))

        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_taf_bulletins_station_id ON taf_bulletins (station_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_taf_bulletins_issue_time ON taf_bulletins (issue_time)"
            )
        )

    def _rebuild_upper_wind_periods(self, connection) -> None:
        try:
            connection.execute(text("PRAGMA foreign_keys=OFF"))
            connection.execute(
                text("DROP TABLE IF EXISTS upper_wind_periods__new"))
            connection.execute(
                text(
                    """
                    CREATE TABLE upper_wind_periods__new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        station_id VARCHAR(8) NOT NULL,
                        valid_time VARCHAR(16) NOT NULL,
                        use_period VARCHAR(24) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(station_id, valid_time, use_period),
                        FOREIGN KEY(station_id) REFERENCES stations(id) ON DELETE CASCADE
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO upper_wind_periods__new (
                        id,
                        station_id,
                        valid_time,
                        use_period,
                        created_at
                    )
                    SELECT
                        id,
                        station_id,
                        valid_time,
                        use_period,
                        created_at
                    FROM upper_wind_periods
                    """
                )
            )
            connection.execute(text("DROP TABLE upper_wind_periods"))
            connection.execute(
                text("ALTER TABLE upper_wind_periods__new RENAME TO upper_wind_periods"))
        finally:
            connection.execute(text("PRAGMA foreign_keys=ON"))

        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_upper_wind_periods_station_id ON upper_wind_periods (station_id)"
            )
        )

    def _rebuild_taf_forecast_periods(self, connection) -> None:
        """Rebuild taf_forecast_periods table without legacy UNIQUE constraint."""
        try:
            connection.execute(text("PRAGMA foreign_keys=OFF"))

            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS taf_forecast_periods__new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        taf_id INTEGER NOT NULL,
                        valid_from TIMESTAMP,
                        valid_to TIMESTAMP,
                        valid_from_timestamp INTEGER,
                        valid_to_timestamp INTEGER,
                        becomes_time TIMESTAMP,
                        forecast_change_type TEXT,
                        probability_percent INTEGER,
                        wind_direction_degrees TEXT,
                        wind_speed_knots INTEGER,
                        wind_gust_knots INTEGER,
                        wind_shear_height_feet INTEGER,
                        wind_shear_direction_degrees INTEGER,
                        wind_shear_speed_knots INTEGER,
                        visibility TEXT NOT NULL,
                        vertical_visibility_feet INTEGER,
                        weather_phenomena TEXT,
                        altimeter_hpa REAL,
                        not_decoded TEXT,
                        FOREIGN KEY(taf_id) REFERENCES taf_bulletins(id) ON DELETE CASCADE
                    )
                    """
                )
            )

            connection.execute(
                text(
                    """
                    INSERT INTO taf_forecast_periods__new (
                        id,
                        taf_id,
                        valid_from,
                        valid_to,
                        valid_from_timestamp,
                        valid_to_timestamp,
                        becomes_time,
                        forecast_change_type,
                        probability_percent,
                        wind_direction_degrees,
                        wind_speed_knots,
                        wind_gust_knots,
                        wind_shear_height_feet,
                        wind_shear_direction_degrees,
                        wind_shear_speed_knots,
                        visibility,
                        vertical_visibility_feet,
                        weather_phenomena,
                        altimeter_hpa,
                        not_decoded
                    )
                    SELECT
                        id,
                        taf_id,
                        valid_from,
                        valid_to,
                        valid_from_timestamp,
                        valid_to_timestamp,
                        becomes_time,
                        forecast_change_type,
                        probability_percent,
                        wind_direction_degrees,
                        wind_speed_knots,
                        wind_gust_knots,
                        wind_shear_height_feet,
                        wind_shear_direction_degrees,
                        wind_shear_speed_knots,
                        visibility,
                        vertical_visibility_feet,
                        weather_phenomena,
                        altimeter_hpa,
                        not_decoded
                    FROM taf_forecast_periods
                    """
                )
            )

            connection.execute(text("DROP TABLE taf_forecast_periods"))
            connection.execute(
                text("ALTER TABLE taf_forecast_periods__new RENAME TO taf_forecast_periods"))
        finally:
            connection.execute(text("PRAGMA foreign_keys=ON"))


__all__ = [
    "SQLiteWeatherRepository",
    "WeatherRepository",
    "Station",
    "MetarObservation",
    "MetarCloudLayer",
    "MetarWeatherPhenomenon",
    "TafBulletin",
    "TafForecastPeriodRecord",
    "TafCloudLayerRecord",
    "TafIcingTurbulenceRecord",
    "TafTemperatureForecastRecord",
    "UpperWindPeriodRecord",
    "UpperWindLevelRecord",
    "SigmetReport",
    "SigmetAreaPointRecord",
]
