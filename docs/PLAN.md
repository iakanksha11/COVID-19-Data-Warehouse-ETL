# Project Plan — COVID-19 Data Platform

**Owner:** Ak
**Date:** June 2026
**Status:** Phase 1 complete · Phase 2 in progress

---

## Business Problem

During the COVID-19 pandemic, decision-makers had data but couldn't use it effectively.

**Problem 1 — Reporting**
> Analysts had no clean, structured platform to answer basic questions:
> which countries were hardest hit, did lockdowns work, how fast did
> vaccines roll out? Raw CSV data from OWID is not queryable by business
> users. No warehouse = no reporting = decisions made on gut feel.

**Problem 2 — Prediction**
> Data scientists had no feature-ready dataset to train ML models on.
> No lagged features, no consistent date series, no clean numeric types.
> Raw CSV is not ML-ready. No prediction = reactive response instead
> of proactive outbreak management.

**Problem statement (single sentence):**
> *COVID-19 data exists but is not structured for either reporting or
> prediction — causing slow, uninformed decisions about outbreak response.*

**What we are building to solve it:**
A data platform that takes raw OWID data and produces two outputs:
- A clean star schema warehouse for analysts to report on trends
- A wide ML feature table for data scientists to predict spread

---

## Objectives

| # | Objective | Consumer |
|---|-----------|----------|
| 1 | Reporting platform — COVID-19 trends and insights | Data analysts → Power BI |
| 2 | Prediction platform — ML models for spread prediction | Data scientists → Python |

---

## Scope

**Geographic:** To be decided by the team
**Time range:** 2020-01-01 → 2024-08-14
**Source:** Our World in Data (OWID) — owid-covid-data.csv

---

## Dataset

| Attribute | Value |
|-----------|-------|
| File | owid-covid-data.csv |
| Rows | 429,435 |
| Columns | 67 |
| Date range | 2020-01-01 → 2024-08-14 |
| Locations | 255 (countries + continents + income groups) |
| File size | 93.83 MB |

---

## Requirements

### Functional Requirements

**FR-01 — Data Ingestion**
- Load COVID-19 data from OWID CSV
- Filter to countries in scope (exclude aggregate rows — World, Asia, etc.)
- Retain full historical date range
- Support re-load when OWID publishes corrections

**FR-02 — Data Quality**
- Reject aggregate rows (continent IS NULL) — route to dq_rejected_rows
- Flag but retain negative new_cases (OWID historical corrections)
- Validate row counts, column types, value ranges after every load
- Capture all rejected rows with reason codes
- Full test suite must pass before data is available to any consumer

**FR-03 — Reporting Layer (Data Analysts)**
- Star schema optimised for Power BI
- Support slicing by country, date, continent
- Time aggregations — daily, weekly, monthly, quarterly
- Answer 30+ business questions about trends, comparisons, correlations
- Refresh on demand

**FR-04 — ML / Prediction Layer (Data Scientists)**
- Wide flat table — all features in one row, no JOINs required
- Consistent date series per country — no gaps
- Pre-computed lag features: 7-day, 14-day, 28-day rolling averages
- Demographic features joined per country
- Clean numeric types — no VARCHAR

**FR-05 — Audit and Traceability**
- Every ETL run logged — start time, end time, rows loaded, status
- Every test result stored with run ID — full history
- Failed steps can be re-run without restarting from scratch

### Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| ETL completion | < 10 minutes for full reload |
| Data freshness | Within 24 hours of OWID update |
| Test coverage | All 4 layers passing before data available |
| Re-runability | Safe to re-run without creating duplicates |
| Reject tracking | Every rejected row captured with reason code |

---

## Tool Decisions

| Tool | Role | Why |
|------|------|-----|
| SQL Server | Staging + warehouse | Local, free, pairs natively with SSIS |
| SSIS | ETL pipeline | Enterprise standard, metadata-driven |
| SSMS | Write + validate SQL | Standard SQL Server IDE |
| Power BI | Reporting dashboards | Connects to SQL Server, visual |
| Python | ML model training | Data science standard |
| Snowflake | Future migration | Cloud warehouse — deferred |

---

## Data Models

### Why two models

Data analysts and data scientists have opposite needs:

| Need | Analyst | Data Scientist |
|------|---------|---------------|
| Query style | GROUP BY, aggregate, slice | Row-level features, no JOINs |
| Nulls | Acceptable | Must be handled |
| Shape | Star schema with JOINs | One wide flat table |
| Date gaps | Acceptable | Must be filled for time series |

Both are built from the same staging table.

---

### Model 1 — Star Schema (Reporting)

```
        dim_date
        (date_id PK)
             │
dim_location ── fact_covid_daily
(location_id PK)  (location_id FK · date_id FK)
```

**Grain:** one row = one country + one date

**dim_location** — one row per country
Static demographics: population, GDP, median age,
hospital beds, smoking rates, life expectancy, HDI

**dim_date** — one row per calendar date
Generated programmatically — not from CSV
Year, month, quarter, week number, day of week, is_weekend

**fact_covid_daily** — one row per country per date
Cases, deaths, testing, vaccination, hospitalisation,
reproduction rate, stringency index, excess mortality

---

### Model 2 — ML Feature Table (Prediction)

**Name:** ml_covid_features
**Grain:** one row = one country + one date
**Shape:** wide flat — everything in one row, no JOINs needed

| Column group | Contents |
|-------------|---------|
| Identity | iso_code, country, date |
| Target | new_cases, new_deaths |
| Case features | total_cases, new_cases_smoothed, per_million |
| Testing features | positive_rate, tests_per_case |
| Vaccination features | people_vaccinated_per_hundred, boosters_per_hundred |
| Policy features | stringency_index |
| Lag features | new_cases_lag_7, lag_14, lag_28 |
| Rolling features | new_cases_rolling_7d_avg, rolling_14d_avg |
| Demographics | population, median_age, gdp_per_capita, hospital_beds |

---

## Business Questions

### Reporting questions (Data Analysts)

**Descriptive — what happened**
1. Which country had the most total deaths?
2. What was the peak daily new cases?
3. Which country had the highest mortality rate (deaths / cases)?
4. How did total cases grow by month?
5. Which country had the fastest vaccination rollout?
6. What was the peak ICU occupancy per country?
7. How many countries crossed 1 million total cases and when?

**Comparative — how countries differ**
8. Which 5 countries had the highest deaths per million?
9. Which 5 countries had the lowest mortality despite high cases?
10. How did stringency index differ between countries?
11. Which countries maintained the lowest positive_rate?
12. High income vs low income countries — mortality rate difference?

**Trend — how it changed over time**
13. How did reproduction rate trend after major lockdowns?
14. When did vaccination rates cross 50% per country?
15. Did ICU occupancy peak before or after case peaks?
16. Did new_deaths_smoothed decline after vaccination reached 60%?
17. How did stringency_index change over 2020–2024?

**Correlation — what relates to what**
18. Does hospital_beds_per_thousand correlate with lower ICU pressure?
19. Does median_age correlate with mortality rate?
20. Does GDP per capita correlate with vaccination rollout speed?
21. Does stringency_index correlate with reproduction_rate reduction?
22. Does handwashing_facilities correlate with early case spread?

### Prediction questions (Data Scientists)

23. Given last 14 days of cases — predict new_cases for next 7 days
24. Which country is most likely to see a surge in next 30 days?
25. Given vaccination rate + stringency — predict reproduction_rate
26. What demographic factors most predict high mortality rate?
27. Given ICU occupancy — predict peak ICU load in 14 days
28. Which countries have similar outbreak trajectories? (clustering)
29. At what vaccination % did new_deaths_smoothed begin declining?
30. Did lockdown timing measurably reduce deaths? (causal inference)

---

## ETL Pipeline

```
owid-covid-data.csv
       │
       ▼
Package 1 — stg_covid_raw (all 67 cols, all rows, VARCHAR)
       │
       ▼
Staging validation gate (7 SSMS checks — FAIL blocks Package 2)
       │
       ▼
Package 2 — metadata-driven warehouse build
       ├──→ dim_location   (~195 rows — static demographics)
       ├──→ dim_date        (~1,688 rows — generated)
       ├──→ fact_covid_daily (~400k rows — analyst layer)
       └──→ ml_covid_features (~400k rows — ML layer with lags)
       │
       ▼
Test suite — 4 layers (Volume · Schema · Accuracy · Business rules)
       │
       ▼
Power BI (analysts) + Python notebooks (data scientists)
```

---

## Phase Plan

### Phase 1 — Study raw data ✅ Complete
Profiled all 67 columns — null %, types, ranges, anomalies.
Identified 15 dim columns and 52 fact columns.
Key finding: 29 columns >75% null, continent IS NULL = aggregates.
**Output:** docs/eda_findings.md

---

### Phase 2 — Generate business questions 🔄 In progress
30 questions written across reporting and prediction categories.
Each question mapped to tables and columns.
**Output:** docs/questions.md
**Gate:** every question answerable from warehouse → if not, redesign.

---

### Phase 3 — Design warehouse ⬜ Not started
Finalise both data models (star schema + ML feature table).
Write DDL for all tables including staging and metadata tables.
Map every question to a JOIN path.
Sign off before writing any SSIS.
**Output:** sql/sqlserver/*.sql · docs/schema.md

---

### Phase 4 — SSIS Package 1 ⬜ Not started
Build staging load: CSV → stg_covid_raw (all VARCHAR, 67 cols).
Run and verify 429,435 rows in SQL Server.
**Output:** ssis/Package1_Staging.dtsx

---

### Phase 5 — SSIS Package 2 ⬜ Not started
Metadata-driven warehouse build.
Four data flows: dim_date, dim_location, fact_covid_daily, ml_covid_features.
DQ filters, type conversion, FK lookups, lag feature computation.
**Output:** ssis/Package2_Warehouse.dtsx

---

### Phase 6 — Test framework ⬜ Not started
4-layer SQL test suite: volume, schema, accuracy, business rules.
All CRITICAL tests must PASS before consumers connect.
**Output:** sql/sqlserver/tests/*.sql · docs/test_results.md

---

### Phase 7 — Reporting (Power BI) ⬜ Not started
Connect Power BI to SQL Server star schema.
Build dashboards answering 22 reporting questions.
**Output:** powerbi/covid_dashboard.pbix

---

### Phase 8 — ML Platform (Python) ⬜ Not started
Connect Python to ml_covid_features table.
Data science team builds and trains prediction models.
**Output:** notebooks/ · models/

---

### Future — Snowflake Migration ⏸ Deferred
Migrate SQL Server warehouse to Snowflake (same schema).
Reconnect Power BI and Python to Snowflake.
Run full test suite after migration.

---

## Open Decisions

| Decision | Options | Owner |
|----------|---------|-------|
| Geographic scope | Global / EU+UK / custom | Team |
| ML target variable | new_cases / new_deaths / both | Data science team |
| Null handling in ML table | Impute / forward-fill / flag | Data science team |
| Power BI licence | Available? | Manager |
| ML model type | ARIMA / LSTM / XGBoost / other | Data science team |

---

## Progress Summary

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 1 — EDA | ✅ Done | docs/eda_findings.md |
| 2 — Questions | 🔄 In progress | docs/questions.md |
| 3 — Warehouse design | ⬜ Not started | DDL scripts |
| 4 — SSIS Package 1 | ⬜ Not started | Package1_Staging.dtsx |
| 5 — SSIS Package 2 | ⬜ Not started | Package2_Warehouse.dtsx |
| 6 — Test framework | ⬜ Not started | Test scripts |
| 7 — Power BI | ⬜ Not started | covid_dashboard.pbix |
| 8 — ML platform | ⬜ Not started | notebooks + models |
| Future — Snowflake | ⏸ Deferred | Migration scripts |
