CREATE OR REPLACE VIEW vw_hourly_traffic_by_location AS
SELECT
    l.location_code,
    l.location_name,
    date_trunc('hour', t.observed_at) AS hour_bucket,
    SUM(t.vehicle_count) AS total_vehicle_count,
    AVG(t.average_speed_kph) AS avg_speed_kph
FROM fact_traffic t
JOIN dim_location l ON l.location_key = t.location_key
GROUP BY l.location_code, l.location_name, date_trunc('hour', t.observed_at);

CREATE OR REPLACE VIEW vw_traffic_weather_correlation AS
SELECT
    l.location_code,
    l.location_name,
    date_trunc('hour', t.observed_at) AS hour_bucket,
    wcond.condition_code,
    wcond.condition_description,
    AVG(t.average_speed_kph) AS avg_speed_kph,
    AVG(t.vehicle_count) AS avg_vehicle_count,
    AVG(w.temperature_c) AS avg_temperature_c,
    AVG(w.precipitation_mm) AS avg_precipitation_mm
FROM fact_traffic t
JOIN fact_weather w
    ON w.location_key = t.location_key
    AND date_trunc('hour', w.observed_at) = date_trunc('hour', t.observed_at)
JOIN dim_location l ON l.location_key = t.location_key
JOIN dim_weather_condition wcond ON wcond.weather_condition_key = w.weather_condition_key
GROUP BY l.location_code, l.location_name, date_trunc('hour', t.observed_at),
         wcond.condition_code, wcond.condition_description;

CREATE OR REPLACE VIEW vw_congestion_hotspot_ranking AS
SELECT
    l.location_code,
    l.location_name,
    AVG(t.vehicle_count) AS avg_vehicle_count,
    AVG(t.average_speed_kph) AS avg_speed_kph,
    COUNT(*) FILTER (WHERE UPPER(t.congestion_level) IN ('HIGH', 'SEVERE')) AS high_congestion_intervals
FROM fact_traffic t
JOIN dim_location l ON l.location_key = t.location_key
GROUP BY l.location_code, l.location_name
ORDER BY high_congestion_intervals DESC, avg_vehicle_count DESC;

CREATE OR REPLACE VIEW vw_daily_weather_summary AS
SELECT
    l.location_code,
    l.location_name,
    d.full_date,
    AVG(w.temperature_c) AS avg_temperature_c,
    MIN(w.temperature_c) AS min_temperature_c,
    MAX(w.temperature_c) AS max_temperature_c,
    SUM(w.precipitation_mm) AS total_precipitation_mm,
    AVG(w.humidity_pct) AS avg_humidity_pct
FROM fact_weather w
JOIN dim_location l ON l.location_key = w.location_key
JOIN dim_date d ON d.date_key = w.date_key
GROUP BY l.location_code, l.location_name, d.full_date;
