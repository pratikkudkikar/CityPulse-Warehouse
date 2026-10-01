from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg

TRAFFIC_REQUIRED_FIELDS = {
    "source_record_id",
    "location_code",
    "location_name",
    "latitude",
    "longitude",
    "observed_at",
    "vehicle_count",
    "average_speed_kph",
    "congestion_level",
}

WEATHER_REQUIRED_FIELDS = {
    "source_record_id",
    "location_code",
    "location_name",
    "latitude",
    "longitude",
    "observed_at",
    "condition_code",
    "condition_description",
    "severity_level",
    "temperature_c",
    "precipitation_mm",
    "wind_speed_kph",
    "humidity_pct",
}

VALID_CONGESTION_LEVELS = {"LOW", "MEDIUM", "HIGH", "SEVERE"}


class IngestionValidationError(ValueError):
    """Raised when one or more rows fail validation."""


@dataclass(frozen=True)
class TrafficRow:
    source_record_id: str
    location_code: str
    location_name: str
    latitude: float
    longitude: float
    observed_at: datetime
    vehicle_count: int
    average_speed_kph: float
    congestion_level: str


@dataclass(frozen=True)
class WeatherRow:
    source_record_id: str
    location_code: str
    location_name: str
    latitude: float
    longitude: float
    observed_at: datetime
    condition_code: str
    condition_description: str
    severity_level: int
    temperature_c: float
    precipitation_mm: float
    wind_speed_kph: float
    humidity_pct: float


def parse_timestamp(value: str, field_name: str) -> datetime:
    raw = require_non_empty(value, field_name)
    raw = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise IngestionValidationError(f"{field_name} must be ISO-8601 timestamp: {raw}") from exc


def require_non_empty(value: str | None, field_name: str) -> str:
    if value is None:
        raise IngestionValidationError(f"{field_name} is required")
    normalized = value.strip()
    if not normalized:
        raise IngestionValidationError(f"{field_name} is required")
    return normalized


def parse_float(value: str | None, field_name: str) -> float:
    normalized = require_non_empty(value, field_name)
    try:
        return float(normalized)
    except ValueError as exc:
        raise IngestionValidationError(f"{field_name} must be numeric: {normalized}") from exc


def parse_int(value: str | None, field_name: str) -> int:
    normalized = require_non_empty(value, field_name)
    try:
        return int(normalized)
    except ValueError as exc:
        raise IngestionValidationError(f"{field_name} must be an integer: {normalized}") from exc


def compute_date_key(observed_at: datetime) -> int:
    return int(observed_at.strftime("%Y%m%d"))


def validate_traffic_row(row: dict[str, str], row_number: int) -> TrafficRow:
    try:
        congestion_level = require_non_empty(
            row.get("congestion_level"), "congestion_level"
        ).upper()
        if congestion_level not in VALID_CONGESTION_LEVELS:
            raise IngestionValidationError(
                "congestion_level must be one of "
                f"{sorted(VALID_CONGESTION_LEVELS)}: {congestion_level}"
            )

        return TrafficRow(
            source_record_id=require_non_empty(row.get("source_record_id"), "source_record_id"),
            location_code=require_non_empty(row.get("location_code"), "location_code"),
            location_name=require_non_empty(row.get("location_name"), "location_name"),
            latitude=parse_float(row.get("latitude"), "latitude"),
            longitude=parse_float(row.get("longitude"), "longitude"),
            observed_at=parse_timestamp(row.get("observed_at", ""), "observed_at"),
            vehicle_count=parse_int(row.get("vehicle_count"), "vehicle_count"),
            average_speed_kph=parse_float(row.get("average_speed_kph"), "average_speed_kph"),
            congestion_level=congestion_level,
        )
    except IngestionValidationError as exc:
        raise IngestionValidationError(f"traffic row {row_number}: {exc}") from exc


def validate_weather_row(row: dict[str, str], row_number: int) -> WeatherRow:
    try:
        severity_level = parse_int(row.get("severity_level"), "severity_level")
        if severity_level < 0 or severity_level > 5:
            raise IngestionValidationError("severity_level must be between 0 and 5")

        humidity_pct = parse_float(row.get("humidity_pct"), "humidity_pct")
        if humidity_pct < 0 or humidity_pct > 100:
            raise IngestionValidationError("humidity_pct must be between 0 and 100")

        return WeatherRow(
            source_record_id=require_non_empty(row.get("source_record_id"), "source_record_id"),
            location_code=require_non_empty(row.get("location_code"), "location_code"),
            location_name=require_non_empty(row.get("location_name"), "location_name"),
            latitude=parse_float(row.get("latitude"), "latitude"),
            longitude=parse_float(row.get("longitude"), "longitude"),
            observed_at=parse_timestamp(row.get("observed_at", ""), "observed_at"),
            condition_code=require_non_empty(row.get("condition_code"), "condition_code"),
            condition_description=require_non_empty(
                row.get("condition_description"), "condition_description"
            ),
            severity_level=severity_level,
            temperature_c=parse_float(row.get("temperature_c"), "temperature_c"),
            precipitation_mm=parse_float(row.get("precipitation_mm"), "precipitation_mm"),
            wind_speed_kph=parse_float(row.get("wind_speed_kph"), "wind_speed_kph"),
            humidity_pct=humidity_pct,
        )
    except IngestionValidationError as exc:
        raise IngestionValidationError(f"weather row {row_number}: {exc}") from exc


def ensure_required_fields(
    fieldnames: list[str] | None, required_fields: set[str], dataset: str
) -> None:
    if not fieldnames:
        raise IngestionValidationError(f"{dataset} CSV has no header row")
    missing = sorted(required_fields - set(fieldnames))
    if missing:
        raise IngestionValidationError(
            f"{dataset} CSV missing required columns: {', '.join(missing)}"
        )


def upsert_date_dimension(cursor: psycopg.Cursor[Any], observed_at: datetime) -> int:
    date_key = compute_date_key(observed_at)
    date_value = observed_at.date()
    cursor.execute(
        """
        INSERT INTO dim_date (date_key, full_date, year, month, day, day_of_week, is_weekend)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date_key) DO NOTHING
        """,
        (
            date_key,
            date_value,
            date_value.year,
            date_value.month,
            date_value.day,
            date_value.isoweekday(),
            date_value.isoweekday() >= 6,
        ),
    )
    return date_key


def upsert_location(
    cursor: psycopg.Cursor[Any],
    location_code: str,
    location_name: str,
    latitude: float,
    longitude: float,
) -> int:
    cursor.execute(
        """
        INSERT INTO dim_location (location_code, location_name, latitude, longitude)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (location_code)
        DO UPDATE SET
            location_name = EXCLUDED.location_name,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            updated_at = NOW()
        RETURNING location_key
        """,
        (location_code, location_name, latitude, longitude),
    )
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Failed to upsert location")
    return int(row[0])


def upsert_weather_condition(
    cursor: psycopg.Cursor[Any],
    condition_code: str,
    condition_description: str,
    severity_level: int,
) -> int:
    cursor.execute(
        """
        INSERT INTO dim_weather_condition (condition_code, condition_description, severity_level)
        VALUES (%s, %s, %s)
        ON CONFLICT (condition_code)
        DO UPDATE SET
            condition_description = EXCLUDED.condition_description,
            severity_level = EXCLUDED.severity_level,
            updated_at = NOW()
        RETURNING weather_condition_key
        """,
        (condition_code, condition_description, severity_level),
    )
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Failed to upsert weather condition")
    return int(row[0])


def ingest_traffic_csv(
    conn: psycopg.Connection[Any], csv_path: Path, source_system: str
) -> tuple[int, int]:
    inserted = 0
    updated = 0
    errors: list[str] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        ensure_required_fields(reader.fieldnames, TRAFFIC_REQUIRED_FIELDS, "traffic")
        with conn.cursor() as cursor:
            for row_number, row in enumerate(reader, start=2):
                try:
                    record = validate_traffic_row(row, row_number)
                    date_key = upsert_date_dimension(cursor, record.observed_at)
                    location_key = upsert_location(
                        cursor,
                        record.location_code,
                        record.location_name,
                        record.latitude,
                        record.longitude,
                    )
                    cursor.execute(
                        """
                        INSERT INTO fact_traffic (
                            date_key,
                            location_key,
                            observed_at,
                            vehicle_count,
                            average_speed_kph,
                            congestion_level,
                            source_system,
                            source_record_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (location_key, observed_at, source_system, source_record_id)
                        DO UPDATE SET
                            vehicle_count = EXCLUDED.vehicle_count,
                            average_speed_kph = EXCLUDED.average_speed_kph,
                            congestion_level = EXCLUDED.congestion_level,
                            ingested_at = NOW()
                        RETURNING (xmax = 0) AS inserted
                        """,
                        (
                            date_key,
                            location_key,
                            record.observed_at,
                            record.vehicle_count,
                            record.average_speed_kph,
                            record.congestion_level,
                            source_system,
                            record.source_record_id,
                        ),
                    )
                    result = cursor.fetchone()
                    if result and result[0]:
                        inserted += 1
                    else:
                        updated += 1
                except IngestionValidationError as exc:
                    errors.append(str(exc))
    if errors:
        preview = "\n".join(errors[:10])
        raise IngestionValidationError(
            f"traffic CSV validation failed ({len(errors)} row errors).\n{preview}"
        )
    return inserted, updated


def ingest_weather_csv(
    conn: psycopg.Connection[Any], csv_path: Path, source_system: str
) -> tuple[int, int]:
    inserted = 0
    updated = 0
    errors: list[str] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        ensure_required_fields(reader.fieldnames, WEATHER_REQUIRED_FIELDS, "weather")
        with conn.cursor() as cursor:
            for row_number, row in enumerate(reader, start=2):
                try:
                    record = validate_weather_row(row, row_number)
                    date_key = upsert_date_dimension(cursor, record.observed_at)
                    location_key = upsert_location(
                        cursor,
                        record.location_code,
                        record.location_name,
                        record.latitude,
                        record.longitude,
                    )
                    weather_condition_key = upsert_weather_condition(
                        cursor,
                        record.condition_code,
                        record.condition_description,
                        record.severity_level,
                    )
                    cursor.execute(
                        """
                        INSERT INTO fact_weather (
                            date_key,
                            location_key,
                            weather_condition_key,
                            observed_at,
                            temperature_c,
                            precipitation_mm,
                            wind_speed_kph,
                            humidity_pct,
                            source_system,
                            source_record_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (location_key, observed_at, source_system, source_record_id)
                        DO UPDATE SET
                            weather_condition_key = EXCLUDED.weather_condition_key,
                            temperature_c = EXCLUDED.temperature_c,
                            precipitation_mm = EXCLUDED.precipitation_mm,
                            wind_speed_kph = EXCLUDED.wind_speed_kph,
                            humidity_pct = EXCLUDED.humidity_pct,
                            ingested_at = NOW()
                        RETURNING (xmax = 0) AS inserted
                        """,
                        (
                            date_key,
                            location_key,
                            weather_condition_key,
                            record.observed_at,
                            record.temperature_c,
                            record.precipitation_mm,
                            record.wind_speed_kph,
                            record.humidity_pct,
                            source_system,
                            record.source_record_id,
                        ),
                    )
                    result = cursor.fetchone()
                    if result and result[0]:
                        inserted += 1
                    else:
                        updated += 1
                except IngestionValidationError as exc:
                    errors.append(str(exc))
    if errors:
        preview = "\n".join(errors[:10])
        raise IngestionValidationError(
            f"weather CSV validation failed ({len(errors)} row errors).\n{preview}"
        )
    return inserted, updated


def build_connection_params() -> dict[str, str]:
    return {
        "dbname": os.getenv("POSTGRES_DB", "citypulse"),
        "user": os.getenv("POSTGRES_USER", "citypulse"),
        "password": os.getenv("POSTGRES_PASSWORD", "citypulse"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load CityPulse traffic and weather CSV data")
    parser.add_argument("--traffic-csv", required=True, type=Path, help="Path to traffic CSV")
    parser.add_argument("--weather-csv", required=True, type=Path, help="Path to weather CSV")
    parser.add_argument(
        "--source-system", default="sample_csv", help="Source system metadata value"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with psycopg.connect(**build_connection_params()) as conn:
            traffic_inserted, traffic_updated = ingest_traffic_csv(
                conn, args.traffic_csv, args.source_system
            )
            weather_inserted, weather_updated = ingest_weather_csv(
                conn, args.weather_csv, args.source_system
            )
            conn.commit()
    except (OSError, psycopg.Error, IngestionValidationError) as exc:
        print(f"Ingestion failed: {exc}")
        return 1

    print(
        "Ingestion complete: "
        f"traffic inserted={traffic_inserted}, traffic updated={traffic_updated}, "
        f"weather inserted={weather_inserted}, weather updated={weather_updated}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
