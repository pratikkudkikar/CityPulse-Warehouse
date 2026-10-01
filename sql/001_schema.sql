CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    day SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_key BIGSERIAL PRIMARY KEY,
    location_code TEXT NOT NULL UNIQUE,
    location_name TEXT NOT NULL,
    latitude NUMERIC(8, 5),
    longitude NUMERIC(8, 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_weather_condition (
    weather_condition_key BIGSERIAL PRIMARY KEY,
    condition_code TEXT NOT NULL UNIQUE,
    condition_description TEXT NOT NULL,
    severity_level SMALLINT NOT NULL CHECK (severity_level BETWEEN 0 AND 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fact_traffic (
    traffic_fact_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dim_date (date_key),
    location_key BIGINT NOT NULL REFERENCES dim_location (location_key),
    observed_at TIMESTAMPTZ NOT NULL,
    vehicle_count INTEGER NOT NULL CHECK (vehicle_count >= 0),
    average_speed_kph NUMERIC(6, 2) NOT NULL CHECK (average_speed_kph >= 0),
    congestion_level TEXT NOT NULL,
    source_system TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (location_key, observed_at, source_system, source_record_id)
);

CREATE TABLE IF NOT EXISTS fact_weather (
    weather_fact_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dim_date (date_key),
    location_key BIGINT NOT NULL REFERENCES dim_location (location_key),
    weather_condition_key BIGINT NOT NULL REFERENCES dim_weather_condition (weather_condition_key),
    observed_at TIMESTAMPTZ NOT NULL,
    temperature_c NUMERIC(5, 2),
    precipitation_mm NUMERIC(6, 2),
    wind_speed_kph NUMERIC(6, 2),
    humidity_pct NUMERIC(5, 2) CHECK (humidity_pct BETWEEN 0 AND 100),
    source_system TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (location_key, observed_at, source_system, source_record_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_traffic_time_loc
    ON fact_traffic (observed_at, location_key);

CREATE INDEX IF NOT EXISTS idx_fact_weather_time_loc
    ON fact_weather (observed_at, location_key);

CREATE INDEX IF NOT EXISTS idx_fact_traffic_date_key
    ON fact_traffic (date_key);

CREATE INDEX IF NOT EXISTS idx_fact_weather_date_key
    ON fact_weather (date_key);
