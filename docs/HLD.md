# High Level Design — COVID-19 Data Warehouse

## What this project does

Takes one raw CSV file containing global COVID-19 data and builds a queryable
star-schema warehouse that answers 30-50 business questions about mortality,
testing, policy effectiveness, and socioeconomic risk factors.

---

## Pipeline Overview

```
  covid_ecdc.csv
  (40 columns, country × day)
         │
         ▼
  ┌─────────────────────┐
  │   SQL Server        │  SSIS loads raw CSV into staging table
  │   Staging Layer     │  All columns loaded as VARCHAR first
  │   stg_covid_raw     │  No transformation yet — just get data in
  └─────────┬───────────┘
            │  Validate in SSMS before proceeding
            ▼
  ┌─────────────────────┐
  │   SQL Server        │  SSIS reads etl_metadata table
  │   Warehouse Layer   │  Executes steps in order per package
  │                     │  dim_location → dim_date → fact_covid_daily
  │   dim_location      │  Bad rows → dq_rejected_rows with reason code
  │   dim_date          │  etl_execution_log records every step result
  │   fact_covid_daily  │
  └─────────┬───────────┘
            │  Migrate to Snowflake (same schema, ODBC connector)
            ▼
  ┌─────────────────────┐
  │   Snowflake         │  Production warehouse
  │   Warehouse         │  Same star schema — rebuilt via COPY INTO
  │                     │  Power BI connects here for reporting
  └─────────┬───────────┘
            │
            ▼
  ┌─────────────────────┐
  │   Analytics         │  Power BI dashboards (exploratory)
  │                     │  SSMS SQL queries (ad hoc)
  │                     │  8 business question reports
  └─────────────────────┘
```

---

## What makes this design different from a standard approach

**Metadata-driven ETL.** Instead of hardcoding steps inside SSIS, a configuration
table (`etl_metadata`) defines what to run and in what order. SSIS reads the table
and executes accordingly. Adding a new step means inserting a row — not rebuilding
the package. Every execution is logged to `etl_execution_log` with start time,
end time, rows affected, and status. Full audit trail from day one.

**Load everything as VARCHAR first.** The staging table loads all 40 columns as
strings. Type casting happens in a second SSIS pass after staging validation passes.
This prevents the entire package from crashing on one malformed date or null number.

**Reject table with reason codes.** Bad rows are never silently dropped. Every
rejected row goes to `dq_rejected_rows` with a DQ reason code, the source values,
and a timestamp. This lets you investigate what went wrong without re-reading the CSV.

**Full reload strategy.** The fact table is truncated and fully reloaded on every run.
OWID publishes historical corrections — incremental load would miss them. At ~100k rows,
full reload is fast enough and far simpler to maintain than change detection.

---

## Warehouse Design — Star Schema

```
              dim_date
              (date_id PK)
                   │
                   │ date_id FK
                   │
  dim_location ─── fact_covid_daily
  (location_id PK)  (location_id FK)
```

**Grain:** one row = one country on one date.

**dim_location** — one row per country. Stores static country-level attributes
that do not change day to day: population, GDP, median age, hospital capacity,
smoking rates, poverty levels. Loaded once, joined at query time.

**dim_date** — one row per calendar date. Generated programmatically — not read
from CSV. Stores year, month, quarter, week number, day of week, is_weekend.
Enables time-based slicing without string manipulation at query time.

**fact_covid_daily** — one row per country per date. Stores everything that
changes daily: case counts, death counts, test counts, positivity rate, policy
stringency. Foreign keys to both dimensions. This is the table Power BI queries.

---

## Layer Summary

| Layer | Tool | Role |
|-------|------|------|
| Source | covid_ecdc.csv | Raw data — 40 columns, country × day |
| Staging load | SSIS Package 1 | CSV → stg_covid_raw (all VARCHAR) |
| Staging validation | SSMS | Null checks, type checks, duplicates — gate before warehouse load |
| Warehouse load | SSIS Package 2 | Metadata-driven — reads etl_metadata, builds dims + fact |
| Audit | etl_execution_log | Every step logged — status, rows, timing, errors |
| SQL Server → Snowflake | ODBC / COPY INTO | Migrate warehouse to cloud |
| Reporting | Power BI | Star schema dashboards — 8 business reports |

---

## Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Schema type | Star schema | One JOIN to any dimension — simple queries, fast, BI-friendly |
| Modelling approach | Kimball | Build from business questions outward, not from source inward |
| ETL control | Metadata-driven | Config change instead of package rebuild when steps change |
| Staging type cast | VARCHAR first, cast second | Prevents package crash on dirty data |
| Load strategy | Full truncate + reload | OWID publishes corrections — incremental would miss them |
| Reject handling | dq_rejected_rows table | Never silently drop bad rows — always traceable |
| Artifact columns | Excluded entirely | `Number of Records` and `Waterfall` are Tableau metadata |
| SQL Server role | Staging + validation gate | ETL and validation before Snowflake — don't load bad data to cloud |
| Snowflake role | Production warehouse | Power BI connects here — not to SQL Server |
