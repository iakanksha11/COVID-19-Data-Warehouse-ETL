# High Level Design — COVID-19 Data Warehouse

## What this project does

Takes one raw CSV file containing global COVID-19 data and builds a queryable
star-schema warehouse that answers 30-50 business questions about mortality,
testing, policy effectiveness, and socioeconomic risk factors.

---

## Source Dataset

| Attribute | Value |
|-----------|-------|
| File | owid-covid-data.csv |
| Source | Our World in Data (OWID) |
| Rows | 429,435 |
| Columns | 67 |
| Date range | 2020-01-01 → 2024-08-14 |
| Locations | 255 (195 countries + continents + income groups) |
| File size | 93.83 MB |

---

## Pipeline Overview

```
  owid-covid-data.csv
  (67 columns · 429,435 rows · country × day)
         │
         ▼
  ┌─────────────────────┐
  │   SQL Server        │  SSIS Package 1 loads raw CSV into staging
  │   Staging Layer     │  All 67 columns loaded as VARCHAR first
  │   stg_covid_raw     │  No transformation — just get data in safely
  └─────────┬───────────┘
            │  Staging validation gate (SSMS)
            │  7 checks — FAIL blocks Package 2
            ▼
  ┌─────────────────────┐
  │   SQL Server        │  SSIS Package 2 — metadata-driven
  │   Warehouse Layer   │  Reads etl_metadata → executes in step_order
  │                     │  dim_date → dim_location → fact_covid_daily
  │   dim_location      │  Bad rows → dq_rejected_rows with reason code
  │   dim_date          │  Every step logged to etl_execution_log
  │   fact_covid_daily  │  restart_flag=Y on failure — safe to re-run
  └─────────┬───────────┘
            │  Run test suite before migrating
            ▼
  ┌─────────────────────┐
  │   Test Layer        │  Four guards — ALL must pass before Snowflake
  │   SQL Server        │
  │                     │  Layer 1: Volume   — source vs destination counts
  │   etl_validation    │  Layer 2: Schema   — columns, nulls, types
  │   (test results)    │  Layer 3: Accuracy — SUM/MIN/MAX source vs fact
  │                     │  Layer 4: Business — domain rules (rates, dates)
  └─────────┬───────────┘
            │  All CRITICAL tests PASS → proceed
            │  Any CRITICAL FAIL → stop, fix ETL, re-run
            ▼
  ┌─────────────────────┐
  │   Snowflake         │  Production warehouse
  │   Warehouse         │  Same star schema — rebuilt via COPY INTO
  │                     │  Same test suite reruns after migration
  │   COVID_DWH         │  All tests must PASS before Power BI connects
  └─────────┬───────────┘
            │  All Snowflake tests PASS → proceed
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

**Load everything as VARCHAR first.** The staging table loads all 67 columns as
strings. Type casting happens in SSIS Package 2 after staging validation passes.
This prevents the entire package from crashing on one malformed date or null number.

**Reject table with reason codes.** Bad rows are never silently dropped. Every
rejected row goes to `dq_rejected_rows` with a DQ reason code (DQ-01 through DQ-06),
the source values, and a timestamp. This lets you investigate what went wrong
without re-reading the CSV.

**Full reload strategy.** The fact table is truncated and fully reloaded on every run.
OWID publishes historical corrections — incremental load would miss them. At 429k rows,
full reload completes in minutes and is far simpler to maintain than change detection.

**Four-layer test strategy.** Reporting alone does not assure correctness. A dedicated
test suite runs after every ETL load — before data reaches Power BI. Tests are stored
in `etl_validation` table with full history per run_id. Results drive a go/no-go
decision at two gates: after SQL Server load, and after Snowflake migration.

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

**dim_location** — one row per country (~195 rows after DQ-01 filter removes
aggregate locations). Stores 15 static country-level attributes that do not change
daily: population, GDP per capita, median age, life expectancy, hospital beds,
smoking rates, poverty levels, HDI.

**dim_date** — one row per calendar date. Generated programmatically — not read
from CSV. Stores year, month, quarter, week number, day of week, is_weekend.
Covers 2020-01-01 to today (~1,688 rows).

**fact_covid_daily** — one row per country per date (~400k rows after DQ filtering).
Stores 52 daily-changing measures: case counts, death counts, testing, vaccination
rollout, hospitalisation, reproduction rate, policy stringency, excess mortality.
Foreign keys to both dimensions.

---

## Test Strategy

Testing sits between the SQL Server warehouse load and Snowflake migration.
The same test suite runs twice — once against SQL Server, once against Snowflake.

### Why four layers — not just row counts

Row count matching alone can lie. If SSIS loads new_cases into new_deaths column,
row count shows 100% match but data is completely wrong.
Four layers together catch what counts alone cannot.

### The four test layers

**Layer 1 — Volume** *(right number of rows?)*
- dim_location count vs distinct countries in staging
- dim_date count vs expected date range
- fact_covid_daily count vs staging count (allow 5% for DQ rejects)
- dq_rejected_rows count and rejection rate %

**Layer 2 — Schema** *(right columns with right constraints?)*
- All 52 fact columns exist and are correct type
- No NULL location_id or date_id in fact table
- No NULL primary keys in any dim table

**Layer 3 — Accuracy** *(right values?)*
- SUM(new_cases) staging = SUM(new_cases) fact
- SUM(new_deaths) staging = SUM(new_deaths) fact
- MIN(date) and MAX(date) staging = fact
- COUNT(DISTINCT location) staging = dim_location count

**Layer 4 — Business Rules** *(values make domain sense?)*
- positive_rate always between 0 and 1
- stringency_index always between 0 and 100
- No future dates in fact table
- No duplicate (location_id, date_id) in fact

### Test results table

```
etl_validation
├─ run_id             ties to etl_execution_log
├─ table_name         which table was tested
├─ test_layer         VOLUME / SCHEMA / ACCURACY / BUSINESS
├─ test_name          human readable description
├─ source_count       count or value from staging
├─ destination_count  count or value from warehouse table
├─ match_pct          (destination / source) * 100
├─ status             PASS / FAIL / WARN
├─ severity           CRITICAL / HIGH / LOW
└─ message            explanation of result
```

### Go / no-go decision

| Result | Action |
|--------|--------|
| All CRITICAL tests PASS | Proceed to next layer |
| Any CRITICAL test FAIL | Stop — fix ETL — re-run |
| WARN | Log and proceed — investigate after |

---

## Layer Summary

| Layer | Tool | Role |
|-------|------|------|
| Source | owid-covid-data.csv | 67 columns · 429,435 rows · country × day |
| Staging load | SSIS Package 1 | CSV → stg_covid_raw (all 67 cols as VARCHAR) |
| Staging validation | SSMS | 7 checks — gate before warehouse load |
| Warehouse load | SSIS Package 2 | Metadata-driven — builds dims + fact |
| Audit | etl_execution_log | Every step logged — status, rows, timing, errors |
| **Test layer** | **etl_validation table** | **Four layers — CRITICAL pass required** |
| SQL Server → Snowflake | ODBC / COPY INTO | Migrate only after all CRITICAL tests pass |
| Snowflake validation | Same test suite | Reruns against Snowflake after migration |
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
| Artifact columns | None to drop | Full OWID dataset has no Tableau artifacts |
| Test strategy | Four layers in etl_validation | Row count alone cannot detect column swaps or value errors |
| Test gates | Two gates — SQL Server + Snowflake | Verify data at each environment before proceeding |
| SQL Server role | Staging + validation + test gate | Don't move untested data to Snowflake |
| Snowflake role | Production warehouse | Power BI connects here — tests rerun after migration |
