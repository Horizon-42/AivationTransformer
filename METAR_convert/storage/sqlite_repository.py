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


class MetarObservation(Base):
    __tablename__ = "metar_observations"
    __table_args__ = (
        UniqueConstraint("station_id", "observation_time", name="uq_metar_station_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(8), index=True)
    station_name: Mapped[str] = mapped_column(String(128))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    elevation_meters: Mapped[int] = mapped_column(Integer)

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
    station_id: Mapped[str] = mapped_column(String(8), index=True)
    station_name: Mapped[str] = mapped_column(String(128))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    elevation_meters: Mapped[int] = mapped_column(Integer)

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
    station_id: Mapped[str] = mapped_column(String(8), index=True)
    valid_time: Mapped[str] = mapped_column(String(16))
    use_period: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    levels: Mapped[List["UpperWindLevelRecord"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )


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
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

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

    def _store_metars(self, session: Session, metars: Dict[str, List[METAR]]) -> None:
        for station_metars in metars.values():
            for metar in station_metars:
                session.execute(
                    delete(MetarObservation)
                    .where(MetarObservation.station_id == metar.station_id)
                    .where(MetarObservation.observation_time == metar.observation_time)
                )

                record = MetarObservation(
                    station_id=metar.station_id,
                    station_name=metar.station_name,
                    latitude=metar.latitude,
                    longitude=metar.longitude,
                    elevation_meters=metar.elevation_meters,
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
                session.execute(
                    delete(TafBulletin)
                    .where(TafBulletin.station_id == taf.station_id)
                    .where(TafBulletin.issue_time == taf.issue_time)
                )

                record = TafBulletin(
                    station_id=taf.station_id,
                    station_name=taf.station_name,
                    latitude=taf.latitude,
                    longitude=taf.longitude,
                    elevation_meters=taf.elevation_meters,
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


__all__ = [
    "SQLiteWeatherRepository",
    "WeatherRepository",
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
