from datetime import datetime

import pytest

from citypulse_ingestion.ingest import (
    IngestionValidationError,
    compute_date_key,
    ensure_required_fields,
    validate_traffic_row,
    validate_weather_row,
)


def test_compute_date_key_uses_calendar_date() -> None:
    observed_at = datetime.fromisoformat("2026-09-28T09:00:00+00:00")
    assert compute_date_key(observed_at) == 20260928


def test_validate_traffic_row_rejects_invalid_timestamp() -> None:
    row = {
        "source_record_id": "TRF-1",
        "location_code": "LOC-1",
        "location_name": "Location 1",
        "latitude": "40.0",
        "longitude": "-74.0",
        "observed_at": "bad-value",
        "vehicle_count": "10",
        "average_speed_kph": "25.0",
        "congestion_level": "HIGH",
    }
    with pytest.raises(IngestionValidationError, match="traffic row 3"):
        validate_traffic_row(row, row_number=3)


def test_validate_weather_row_rejects_humidity_out_of_range() -> None:
    row = {
        "source_record_id": "WTH-1",
        "location_code": "LOC-1",
        "location_name": "Location 1",
        "latitude": "40.0",
        "longitude": "-74.0",
        "observed_at": "2026-09-28T09:00:00+00:00",
        "condition_code": "CLEAR",
        "condition_description": "Clear",
        "severity_level": "0",
        "temperature_c": "20.0",
        "precipitation_mm": "0.0",
        "wind_speed_kph": "5.0",
        "humidity_pct": "120",
    }
    with pytest.raises(IngestionValidationError, match="humidity_pct"):
        validate_weather_row(row, row_number=5)


def test_validate_traffic_row_normalizes_congestion_level() -> None:
    row = {
        "source_record_id": "TRF-2",
        "location_code": "LOC-2",
        "location_name": "Location 2",
        "latitude": "40.0",
        "longitude": "-74.0",
        "observed_at": "2026-09-28T09:00:00+00:00",
        "vehicle_count": "20",
        "average_speed_kph": "35.0",
        "congestion_level": "medium",
    }
    record = validate_traffic_row(row, row_number=2)
    assert record.congestion_level == "MEDIUM"


def test_ensure_required_fields_rejects_missing_columns() -> None:
    with pytest.raises(IngestionValidationError, match="missing required columns"):
        ensure_required_fields(["source_record_id"], {"source_record_id", "observed_at"}, "traffic")
