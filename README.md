# CityPulse-Warehouse

Smart-city data warehouse MVP integrating traffic and weather data for urban planning and management.

## MVP architecture

- **Warehouse**: PostgreSQL (Docker Compose) with dimensional model and analytics views.
- **Model**:
  - Dimensions: `dim_date`, `dim_location`, `dim_weather_condition`
  - Facts: `fact_traffic`, `fact_weather`
- **Ingestion**: Python CSV pipeline (`src/citypulse_ingestion/ingest.py`) with validation, error handling, and idempotent upserts.
- **Sample data**: `data/sample/traffic.csv` and `data/sample/weather.csv`.
- **Analytics layer**: SQL views in `sql/002_views.sql`.

## Project layout

```text
.
├── .env.example
├── docker-compose.yml
├── data/
│   └── sample/
├── sql/
│   ├── 001_schema.sql
│   └── 002_views.sql
├── src/
│   └── citypulse_ingestion/
│       └── ingest.py
└── tests/
    └── test_ingest_validation.py
```

## Setup

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```
2. Start PostgreSQL:
   ```bash
   docker compose up -d warehouse
   ```
3. Install Python dependencies:
   ```bash
   python -m pip install -e '.[dev]'
   ```

## Data flow

1. Docker starts PostgreSQL and runs SQL initialization scripts from `sql/`.
2. Run ingestion command to validate and load traffic/weather CSVs.
3. Ingestion upserts dimensions and facts with source metadata and timestamps.
4. Query analytics views for planning and operational analysis.

## Run ingestion

```bash
python -m citypulse_ingestion.ingest \
  --traffic-csv data/sample/traffic.csv \
  --weather-csv data/sample/weather.csv \
  --source-system sample_csv
```

### Ingestion behavior

- Validates required fields, timestamp format, numeric fields, and value ranges.
- Returns clear errors for malformed rows (row-level context included).
- Uses unique constraints + `ON CONFLICT DO UPDATE` for idempotent re-runs.

## Analytics views and example queries

### 1) Hourly traffic volume and average speed by location

```sql
SELECT *
FROM vw_hourly_traffic_by_location
ORDER BY hour_bucket, location_code;
```

### 2) Traffic conditions correlated with weather conditions

```sql
SELECT *
FROM vw_traffic_weather_correlation
ORDER BY hour_bucket, location_code, condition_code;
```

### 3) Congestion hotspot ranking

```sql
SELECT *
FROM vw_congestion_hotspot_ranking
LIMIT 10;
```

### 4) Daily weather summaries

```sql
SELECT *
FROM vw_daily_weather_summary
ORDER BY full_date, location_code;
```

## Tests and quality

Run validation tests:

```bash
pytest -q
```

Optional lint:

```bash
ruff check .
```

## Notes

- This MVP is intentionally local-first and avoids cloud dependencies.
- API adapters can be added later by plugging additional source loaders into the ingestion pipeline.

## Web UI integration (React + TypeScript + Tailwind)

A new UI workspace is available in `/home/runner/work/CityPulse-Warehouse/CityPulse-Warehouse/web`.

### What was added

- Vite React + TypeScript app.
- Tailwind CSS via `@tailwindcss/vite`.
- shadcn-style component structure under `src/components/ui`.
- `gradient-bar-hero-section.tsx` at `src/components/ui/gradient-bar-hero-section.tsx`.
- `demo.tsx` that imports from `@/components/ui/gradient-bar-hero-section`.
- A satellite map section with state-level coordinates at `src/components/ui/state-satellite-map.tsx`.

### Default paths used

- Components path: `src/components/ui`
- Global styles path: `src/index.css`

`/components/ui` is important because shadcn and related examples assume a centralized UI-component folder for predictable imports and reusable design-system primitives.

### Run UI locally

```bash
cd web
npm install
npm run dev
```

### Build UI

```bash
cd web
npm run build
```
