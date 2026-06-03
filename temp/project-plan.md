# COVID-19 Data Platform — Project Plan

## Project Overview

| Item | Detail |
|------|--------|
| **Project Name** | COVID-19 Data Platform — Reporting and Prediction |
| **Owner** | Ak |
| **Start Date** | June 2026 |
| **Goal** | Build a full ETL pipeline that serves data analysts (reporting) and data scientists (prediction) |
| **Stack** | SSIS + SQL Server (local) → Snowflake (cloud, future phase) |
| **Reporting** | Power BI connected to SQL Server star schema |
| **Prediction** | Python connected to ML feature table |

---

## Business Problem

**Problem 1 — Reporting gap:**
Analysts have no clean structured platform to answer COVID-19 trend questions.
Raw CSV is not queryable by business users. No warehouse = decisions made without data.

**Problem 2 — Prediction gap:**
Data scientists have no feature-ready dataset for ML models.
Raw CSV has no lag features, inconsistent date series, and mixed types.

**One sentence:**
> COVID-19 data exists but is not structured for either reporting or prediction
> — causing slow, uninformed decisions about outbreak response.

---

## Datasets

| File | Purpose | Rows | Null risk |
|------|---------|------|-----------|
| `owid-covid-data.csv` | Core cases, deaths, testing, vaccination, hospitalisation, demographics | 429,435 | Medium — testing 82% null, hospitalisation 90% null |

**Source:** Our World in Data — https://ourworldindata.org/covid-deaths
**License:** Creative Commons BY 4.0 — safe for personal and learning use.
**Geographic scope:** Global — all countries (~195 after filtering aggregates)
**Date range:** 2020-01-01 → 2024-08-14

---

## Tech Stack

| Tool | Purpose | Cost |
|------|---------|------|
| SQL Server Developer Edition | Local staging + warehouse | Free |
| SSMS | Query, manage, verify loaded data | Free |
| Visual Studio Community + SSIS | Design and build ETL packages | Free |
| SSIS (Integration Services) | Extract, transform, load | Free (included with SQL Server) |
| Power BI Desktop | Reporting dashboards | Free |
| Python | ML feature table consumption + model training | Free |
| Snowflake | Cloud warehouse (future phase) | Free trial ($400 credits) |

---

## Data Models

**Two models — built from the same staging table:**

**Model 1 — Star schema (reporting)**
```
dim_date ── fact_covid_daily ── dim_location
```
- Grain: one row = one country + one date
- dim_location: ~195 rows, 19 static demographic columns
- dim_date: ~1,688 rows, generated calendar table
- fact_covid_daily: ~400k rows, 52 daily-changing columns

**Model 2 — ML feature table (prediction)**
- Name: ml_covid_features
- Wide flat table — no JOINs required
- Pre-computed lag features: 7-day, 14-day, 28-day
- Demographics joined in per country
- Clean numeric types throughout

---

## Phase Plan

---

### Phase 1 — Study Raw Data
**Status: ✅ Complete**

| Task | Done? |
|------|-------|
| Download owid-covid-data.csv | ✅ |
| Run data_dictionary.py — profile all 67 columns | ✅ |
| Confirm row count (429,435), date range, unique locations (255) | ✅ |
| Identify null % per column — 29 columns >75% null | ✅ |
| Confirm continent IS NULL rows = aggregate locations (DQ-01) | ✅ |
| Identify static vs dynamic columns — 15 dim, 52 fact | ✅ |
| Confirm no artifact columns to drop (unlike old CSV) | ✅ |
| Document all findings in eda_findings.md | ✅ |

**Deliverable:** `docs/eda_findings.md`

---

### Phase 2 — Define Requirements and Business Questions
**Status: ✅ Complete**

| Task | Done? |
|------|-------|
| Define business problem — two objectives (reporting + prediction) | ✅ |
| Confirm geographic scope — Global (all ~195 countries) | ✅ |
| Write functional requirements FR-01 to FR-05 | ✅ |
| Write 38 business questions across 6 categories | ✅ |
| Write 8 prediction questions with feature columns | ✅ |
| Map every question to tables and columns | ✅ |
| Document report-to-table traceability | ✅ |

**Deliverable:** `docs/requirements.md` · `docs/questions.md`

---

### Phase 3 — Design Warehouse Schema
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 2 complete ✅

| Task | Done? |
|------|-------|
| Confirm grain — one row = one country + one date | ⬜ |
| Finalise dim_location columns (15 static demographic cols + HDI) | ⬜ |
| Finalise dim_date columns (9 cols — generated) | ⬜ |
| Finalise fact_covid_daily columns (52 daily cols across 6 domains) | ⬜ |
| Finalise ml_covid_features columns (fact cols + lags + demographics) | ⬜ |
| Draw star schema diagram | ⬜ |
| Map every Phase 2 question to a JOIN path | ⬜ |
| Validate — every question answerable? If not, redesign | ⬜ |
| Write DDL — stg_covid_raw (67 cols, all VARCHAR) | ⬜ |
| Write DDL — dim_location | ⬜ |
| Write DDL — dim_date | ⬜ |
| Write DDL — fact_covid_daily | ⬜ |
| Write DDL — ml_covid_features | ⬜ |
| Write DDL — dq_rejected_rows | ⬜ |
| Write DDL — etl_metadata, etl_execution_log, etl_hist_metadata, etl_validation | ⬜ |
| Populate etl_metadata with step rows | ⬜ |
| Document schema design rationale | ⬜ |

**Deliverable:** `sql/sqlserver/01_create_staging.sql` · `02_create_dim_location.sql` · `03_create_dim_date.sql` · `04_create_fact_covid_daily.sql` · `05_create_ml_features.sql` · `06_create_metadata_tables.sql` · `docs/schema-design-rationale.md`

**Gate:** Every Phase 2 question must be answerable from schema before moving to Phase 4.

---

### Phase 4 — Build SSIS Package 1 (Staging Load)
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 3 complete — all DDL scripts verified in SSMS ✅

| Task | Done? |
|------|-------|
| Install Visual Studio Community + SSIS extension | ⬜ |
| Create new SSIS project — covid_etl | ⬜ |
| Configure Flat File Connection Manager — owid-covid-data.csv, all 67 cols as string | ⬜ |
| Configure OLE DB Connection Manager — SQL Server covid_dwh | ⬜ |
| Add Execute SQL Task — TRUNCATE TABLE stg_covid_raw | ⬜ |
| Add Data Flow Task — Flat File Source → OLE DB Destination (stg_covid_raw) | ⬜ |
| Add error output — route failed rows to log | ⬜ |
| Run package — verify 429,435 rows in stg_covid_raw | ⬜ |
| Run staging validation (SSMS) — all 7 checks PASS | ⬜ |

**Deliverable:** `ssis/Package1_Staging.dtsx`
**Verify:** `SELECT COUNT(*) FROM stg_covid_raw` → 429,435

---

### Phase 5 — Build SSIS Package 2 (Warehouse Build)
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 4 complete — stg_covid_raw verified ✅

| Task | Done? |
|------|-------|
| Generate run_id (GUID) as SSIS variable at package start | ⬜ |
| Add ForEach Loop — reads etl_metadata, executes in step_order | ⬜ |
| Log each step to etl_execution_log (RUNNING → DONE / FAILED) | ⬜ |
| Build Data Flow 1 — dim_date (Script Task generates dates, Derived Column, OLE DB Dest) | ⬜ |
| Build Data Flow 2 — dim_location (Flat File Source, DQ-01 filter, dedup, type cast, OLE DB Dest) | ⬜ |
| Build Data Flow 3 — fact_covid_daily (source, DQ filters DQ-01 to DQ-04, type cast, FK lookups, OLE DB Dest, reject path) | ⬜ |
| Build Data Flow 4 — ml_covid_features (fact source + lag Derived Columns + demographics join) | ⬜ |
| Add failure path — restart_flag=Y on step failure | ⬜ |
| Add final Execute SQL Task — EXEC usp_verify_etl_load | ⬜ |
| Run package end-to-end | ⬜ |
| Verify: dim_location ~195 rows | ⬜ |
| Verify: dim_date ~1,688 rows | ⬜ |
| Verify: fact_covid_daily ~400k rows | ⬜ |
| Verify: ml_covid_features ~400k rows | ⬜ |
| Inspect dq_rejected_rows — confirm DQ-01 aggregates captured | ⬜ |

**Deliverable:** `ssis/Package2_Warehouse.dtsx` · `sql/sqlserver/usp_verify_etl_load.sql`

---

### Phase 6 — Test Framework
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 5 complete — all warehouse tables populated ✅

| Task | Done? |
|------|-------|
| Write test_volume.sql — row counts per table vs staging | ⬜ |
| Write test_schema.sql — columns exist, no null FKs | ⬜ |
| Write test_accuracy.sql — SUM/MIN/MAX staging vs fact | ⬜ |
| Write test_business_rules.sql — rates in range, no future dates, no duplicates | ⬜ |
| Write run_all_tests.sql — executes all tests, inserts into etl_validation | ⬜ |
| Run full test suite — all CRITICAL tests PASS | ⬜ |
| Document results in test report | ⬜ |

**Deliverable:** `sql/sqlserver/tests/test_volume.sql` · `test_schema.sql` · `test_accuracy.sql` · `test_business_rules.sql` · `run_all_tests.sql` · `docs/test_results.md`

**Gate:** All CRITICAL tests must PASS before Power BI connects.

---

### Phase 7 — Power BI Reporting
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 6 complete — all critical tests passing ✅

| Task | Done? |
|------|-------|
| Connect Power BI Desktop to SQL Server covid_dwh | ⬜ |
| Import dim_location, dim_date, fact_covid_daily | ⬜ |
| Verify star schema relationships in Model view | ⬜ |
| Create DAX measures — Total Cases, Total Deaths, Mortality Rate %, Avg Stringency, Vaccination % | ⬜ |
| Build Page 1 — Global Overview (cards, line chart, bar by continent, map) | ⬜ |
| Build Page 2 — Country Deep Dive (slicers, trends, comparison table) | ⬜ |
| Build Page 3 — Risk Factors (scatter: GDP vs mortality, age vs mortality) | ⬜ |
| Build Page 4 — Vaccination Analysis (rollout timeline, % vaccinated by country) | ⬜ |
| Build Page 5 — Testing Analysis (positivity rate, tests per case) | ⬜ |
| Write SQL for all 38 business questions | ⬜ |
| Verify every question answered — cross-check requirements.md | ⬜ |

**Deliverable:** `powerbi/covid_dashboard.pbix` · `sql/sqlserver/analytical_queries.sql`

---

### Phase 8 — ML Platform (Python)
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 6 complete — ml_covid_features table populated and tested ✅

| Task | Done? |
|------|-------|
| Connect Python to SQL Server — read ml_covid_features | ⬜ |
| Exploratory analysis — feature distributions, correlations | ⬜ |
| Handle nulls — impute or forward-fill strategy | ⬜ |
| Build prediction model — new_cases next 7 days (P-01) | ⬜ |
| Build classification model — surge risk per country (P-02) | ⬜ |
| Evaluate models — RMSE, MAE, accuracy | ⬜ |
| Document model results | ⬜ |

**Deliverable:** `notebooks/01_eda.ipynb` · `notebooks/02_prediction.ipynb` · `models/`

---

### Future — Snowflake Migration
**Status: ⏸ Deferred**

| Task | Done? |
|------|-------|
| Sign up for Snowflake free trial | ⬜ |
| Recreate schema in Snowflake (same DDL — remove partition syntax) | ⬜ |
| Export SQL Server tables to CSV | ⬜ |
| PUT to Snowflake stage → COPY INTO | ⬜ |
| Rerun full test suite against Snowflake | ⬜ |
| Reconnect Power BI and Python to Snowflake | ⬜ |

---

## Progress Summary

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 1 — EDA | ✅ Done | docs/eda_findings.md |
| 2 — Requirements | ✅ Done | docs/requirements.md · docs/questions.md |
| 3 — Schema design | ⬜ Not started | DDL scripts · schema-design-rationale.md |
| 4 — SSIS Package 1 | ⬜ Not started | Package1_Staging.dtsx |
| 5 — SSIS Package 2 | ⬜ Not started | Package2_Warehouse.dtsx |
| 6 — Test framework | ⬜ Not started | Test scripts · test_results.md |
| 7 — Power BI | ⬜ Not started | covid_dashboard.pbix |
| 8 — ML platform | ⬜ Not started | notebooks + models |
| Future — Snowflake | ⏸ Deferred | Migration scripts |

---

## Skills Demonstrated

| Skill | Phase |
|-------|-------|
| EDA and data profiling | ✅ Phase 1 |
| Requirements gathering and business question definition | ✅ Phase 2 |
| Kimball dimensional modelling — star schema design | Phase 3 |
| SQL Server DDL — constraints, indexes | Phase 3 |
| ETL pipeline design — DQ rules, reject handling, metadata-driven | Phase 3 |
| SSIS Control Flow — Execute SQL Task, Script Task, ForEach Loop | Phase 4–5 |
| SSIS Data Flow — Flat File Source, Sort, Derived Column, Conditional Split, Lookup, OLE DB Destination | Phase 4–5 |
| Post-load verification with stored procedures | Phase 5 |
| SQL test suite — volume, schema, accuracy, business rules | Phase 6 |
| Power BI — star schema modelling, DAX measures, dashboards | Phase 7 |
| Python ML — feature engineering, model training, evaluation | Phase 8 |
| Snowflake — cloud warehouse migration | Future |
