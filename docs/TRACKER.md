# Project Tracker — COVID-19 Data Warehouse
**Owner:** Ak
**Last Updated:** June 2026
**Pipeline:** CSV → SSIS → SQL Server → Snowflake → Power BI / SSRS

---

## Overall Progress

| Metric | Value |
|--------|-------|
| Total tasks | 57 |
| Done | 2 |
| In Progress | 1 |
| Not Started | 54 |
| Completion | 3% |

---

## Phase 1 — EDA on Raw Data
**Status:** 🔄 In Progress
**Tool:** Python + Pandas
**Goal:** Fully understand raw data before writing any ETL

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 1.1 | Download COVID ECDC CSV file | ✅ Done | `raw_data/covid_ecdc.csv` |
| 1.2 | Identify all 40 column names | ✅ Done | Listed in README.md |
| 1.3 | Group columns into categories (Geography, Demographics, Facts, Dimension, Drop) | 🔄 In Progress | Column categories in README.md |
| 1.4 | Run profiling script — row count, date range, unique locations | ⬜ Not Started | `src/profiler.py` |
| 1.5 | Check null % per column — identify heavily null columns | ⬜ Not Started | `docs/eda_findings.md` |
| 1.6 | Check data types — are dates dates? are numbers numbers? | ⬜ Not Started | `docs/eda_findings.md` |
| 1.7 | Check for duplicate rows (same country + same date) | ⬜ Not Started | `docs/eda_findings.md` |
| 1.8 | Check granularity — confirm one row = one country + one date | ⬜ Not Started | `docs/eda_findings.md` |
| 1.9 | Check for anomalies — negative cases, positive_rate > 1, stringency > 100 | ⬜ Not Started | `docs/eda_findings.md` |
| 1.10 | Confirm static vs dynamic columns (dimension vs fact classification) | ⬜ Not Started | `docs/eda_findings.md` |
| 1.11 | Inspect artifact columns — Number of Records, Waterfall | ⬜ Not Started | `docs/eda_findings.md` |
| 1.12 | Document all findings in eda_findings.md | ⬜ Not Started | `docs/eda_findings.md` |

**Phase 1 Deliverables:**
- [ ] `src/profiler.py`
- [ ] `docs/eda_findings.md`

---

## Phase 2 — Generate Business Questions
**Status:** ⬜ Not Started
**Tool:** Brain + paper
**Goal:** 30-50+ questions the warehouse must answer

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 2.1 | Define business problem and stakeholder role | ⬜ Not Started | README.md business problem section |
| 2.2 | Write Descriptive questions — "What happened?" (min 7) | ⬜ Not Started | `docs/questions.md` |
| 2.3 | Write Diagnostic questions — "Why did it happen?" (min 7) | ⬜ Not Started | `docs/questions.md` |
| 2.4 | Write Trend/Pattern questions — "How did it change?" (min 6) | ⬜ Not Started | `docs/questions.md` |
| 2.5 | Write Comparative questions — "How do groups differ?" (min 7) | ⬜ Not Started | `docs/questions.md` |
| 2.6 | Write Correlation questions — "What relates to what?" (min 6) | ⬜ Not Started | `docs/questions.md` |
| 2.7 | Write Anomaly questions — "What doesn't fit?" (min 5) | ⬜ Not Started | `docs/questions.md` |
| 2.8 | For each question — map to which table and column answers it | ⬜ Not Started | `docs/questions.md` |
| 2.9 | Identify any question that CANNOT be answered — flag for redesign | ⬜ Not Started | `docs/questions.md` |
| 2.10 | Final count — confirm minimum 30 questions achieved | ⬜ Not Started | `docs/questions.md` |

**Phase 2 Deliverables:**
- [ ] `docs/questions.md` (minimum 30 questions)

---

## Phase 3 — Design Warehouse
**Status:** ⬜ Not Started
**Tool:** Paper + SSMS
**Goal:** Star schema that answers every Phase 2 question

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 3.1 | Confirm grain — one row = one country + one date | ⬜ Not Started | `docs/schema.md` |
| 3.2 | List all fact columns (daily changing, measurable, SUM-able) | ⬜ Not Started | `docs/schema.md` |
| 3.3 | List all dimension columns (static per country) | ⬜ Not Started | `docs/schema.md` |
| 3.4 | Draw star schema diagram on paper | ⬜ Not Started | Photo in `docs/` |
| 3.5 | Map every Phase 2 question to a JOIN path | ⬜ Not Started | `docs/questions.md` updated |
| 3.6 | Validate — every question answerable? If not, redesign | ⬜ Not Started | Sign-off in `docs/schema.md` |
| 3.7 | Write DDL — stg_covid_raw (SQL Server staging) | ⬜ Not Started | `sql/sqlserver/01_create_staging.sql` |
| 3.8 | Write DDL — dim_country (Snowflake) | ⬜ Not Started | `sql/snowflake/02_create_dims.sql` |
| 3.9 | Write DDL — dim_date (Snowflake) | ⬜ Not Started | `sql/snowflake/02_create_dims.sql` |
| 3.10 | Write DDL — fact_covid_daily (Snowflake) | ⬜ Not Started | `sql/snowflake/03_create_facts.sql` |

**Phase 3 Deliverables:**
- [ ] `docs/schema.md`
- [ ] `sql/sqlserver/01_create_staging.sql`
- [ ] `sql/snowflake/02_create_dims.sql`
- [ ] `sql/snowflake/03_create_facts.sql`

---

## Phase 4 — SSIS ETL Pipeline
**Status:** ⬜ Not Started
**Tool:** Visual Studio + SSIS
**Goal:** Load CSV into SQL Server staging using SSIS package

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 4.1 | Install SQL Server Developer Edition (free) | ⬜ Not Started | SQL Server running locally |
| 4.2 | Install Visual Studio + SSIS extension | ⬜ Not Started | VS with SSIS ready |
| 4.3 | Create new SSIS project in Visual Studio | ⬜ Not Started | `ssis/covid_etl.dtsx` |
| 4.4 | Create Flat File Connection Manager — point to CSV | ⬜ Not Started | Connection in package |
| 4.5 | Create OLE DB Connection Manager — point to SQL Server | ⬜ Not Started | Connection in package |
| 4.6 | Build Control Flow — Truncate task → Data Flow task | ⬜ Not Started | Control flow complete |
| 4.7 | Build Data Flow — Flat File Source → Data Conversion → Derived Column → OLE DB Destination | ⬜ Not Started | Data flow complete |
| 4.8 | Add error output — route bad rows to error CSV | ⬜ Not Started | `logs/ssis_errors.csv` |
| 4.9 | Run package — verify row count matches CSV | ⬜ Not Started | Row count confirmed |
| 4.10 | Document load metrics — rows loaded, rejected, time taken | ⬜ Not Started | `docs/load_metrics.md` |

**Phase 4 Deliverables:**
- [ ] `ssis/covid_etl.dtsx`
- [ ] `logs/ssis_errors.csv`
- [ ] `docs/load_metrics.md`

---

## Phase 5 — SQL Server Validation
**Status:** ⬜ Not Started
**Tool:** SSMS
**Goal:** Validate staging data before pushing to Snowflake

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 5.1 | Check row count — staging count matches CSV line count | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.2 | Check null location — no empty location values | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.3 | Check null date — no empty date values | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.4 | Check date format — all dates parseable as DATE | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.5 | Check duplicates — no duplicate location + date | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.6 | Check negative new_cases — flag count (warn not fail) | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.7 | Check positive_rate range — all values between 0 and 1 | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.8 | Check stringency_index range — all values between 0 and 100 | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.9 | Confirm artifact columns excluded — Waterfall, Number of Records not in table | ⬜ Not Started | `sql/sqlserver/02_validate_staging.sql` |
| 5.10 | Document all checks as PASS / FAIL / WARN | ⬜ Not Started | `docs/validation_report.md` |

**Phase 5 Deliverables:**
- [ ] `sql/sqlserver/02_validate_staging.sql`
- [ ] `docs/validation_report_staging.md`

---

## Phase 6 — Load SQL Server → Snowflake
**Status:** ⬜ Not Started
**Tool:** Snowflake UI + SnowSQL CLI
**Goal:** Move clean staged data into Snowflake, build dim and fact tables

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 6.1 | Export clean staging table from SQL Server to CSV | ⬜ Not Started | `exports/covid_clean.csv` |
| 6.2 | Create Snowflake database — COVID_DWH | ⬜ Not Started | `sql/snowflake/01_setup.sql` |
| 6.3 | Create Snowflake schema — ANALYTICS | ⬜ Not Started | `sql/snowflake/01_setup.sql` |
| 6.4 | Create Snowflake warehouse — COMPUTE_WH | ⬜ Not Started | `sql/snowflake/01_setup.sql` |
| 6.5 | Create file format — CSV_FORMAT | ⬜ Not Started | `sql/snowflake/01_setup.sql` |
| 6.6 | Create stage — COVID_STAGE | ⬜ Not Started | `sql/snowflake/01_setup.sql` |
| 6.7 | PUT exported CSV to Snowflake stage | ⬜ Not Started | Stage file confirmed |
| 6.8 | COPY INTO Snowflake staging table | ⬜ Not Started | stg_covid_raw populated |
| 6.9 | INSERT...SELECT → build dim_country | ⬜ Not Started | `sql/snowflake/04_load_dims.sql` |
| 6.10 | INSERT...SELECT → build dim_date | ⬜ Not Started | `sql/snowflake/04_load_dims.sql` |
| 6.11 | INSERT...SELECT → build fact_covid_daily | ⬜ Not Started | `sql/snowflake/05_load_facts.sql` |
| 6.12 | Verify row counts match SQL Server staging | ⬜ Not Started | Row counts documented |

**Phase 6 Deliverables:**
- [ ] `sql/snowflake/01_setup.sql`
- [ ] `sql/snowflake/04_load_dims.sql`
- [ ] `sql/snowflake/05_load_facts.sql`

---

## Phase 7 — Snowflake Validation
**Status:** ⬜ Not Started
**Tool:** Snowflake UI
**Goal:** Confirm warehouse data is correct, complete, and answers all questions

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 7.1 | Row count — fact_covid_daily matches staging count | ⬜ Not Started | `sql/snowflake/06_validate.sql` |
| 7.2 | Referential integrity — no orphan country_keys in fact table | ⬜ Not Started | `sql/snowflake/06_validate.sql` |
| 7.3 | Referential integrity — no orphan date_keys in fact table | ⬜ Not Started | `sql/snowflake/06_validate.sql` |
| 7.4 | No null keys — date_key and country_key never null | ⬜ Not Started | `sql/snowflake/06_validate.sql` |
| 7.5 | Aggregate reconciliation — SUM(new_cases) matches staging total | ⬜ Not Started | `sql/snowflake/06_validate.sql` |
| 7.6 | Spot check — run 5 Phase 2 questions, confirm non-empty results | ⬜ Not Started | `sql/snowflake/07_questions.sql` |
| 7.7 | Document all checks as PASS / FAIL | ⬜ Not Started | `docs/validation_report_snowflake.md` |

**Phase 7 Deliverables:**
- [ ] `sql/snowflake/06_validate.sql`
- [ ] `docs/validation_report_snowflake.md`

---

## Phase 8 — Power BI Reporting
**Status:** ⬜ Not Started
**Tool:** Power BI Desktop
**Goal:** Answer all Phase 2 questions visually

| # | Task | Status | Deliverable |
|---|------|--------|-------------|
| 8.1 | Connect Power BI to Snowflake | ⬜ Not Started | Connection working |
| 8.2 | Import dim_country, dim_date, fact_covid_daily | ⬜ Not Started | Tables loaded in Power BI |
| 8.3 | Verify star schema relationships in Model view | ⬜ Not Started | Relationships confirmed |
| 8.4 | Create DAX measures — Total Cases, Total Deaths, Mortality Rate %, Avg Stringency | ⬜ Not Started | Measures panel |
| 8.5 | Build Page 1 — Global Overview (cards, line chart, bar chart, map) | ⬜ Not Started | `powerbi/covid_dashboard.pbix` |
| 8.6 | Build Page 2 — Country Deep Dive (slicers, scatter, table) | ⬜ Not Started | `powerbi/covid_dashboard.pbix` |
| 8.7 | Build Page 3 — Risk Factors (scatter plots for correlations) | ⬜ Not Started | `powerbi/covid_dashboard.pbix` |
| 8.8 | Build Page 4 — Testing Analysis (positivity rate, tests vs cases) | ⬜ Not Started | `powerbi/covid_dashboard.pbix` |
| 8.9 | Write SQL for all Phase 2 questions | ⬜ Not Started | `sql/snowflake/07_questions.sql` |
| 8.10 | Confirm every Phase 2 question is answered | ⬜ Not Started | Sign-off in questions.md |

**Phase 8 Deliverables:**
- [ ] `powerbi/covid_dashboard.pbix`
- [ ] `sql/snowflake/07_questions.sql`

---

## Decisions Log

| Date | Decision | Choice | Reason |
|------|----------|--------|--------|
| June 2026 | Modelling approach | Kimball dimensional | Analytics-first, business-question-driven |
| June 2026 | Schema type | Star schema | Simple queries, fast, BI tool compatible |
| June 2026 | ETL tool | SSIS | Manager requirement, enterprise standard |
| June 2026 | Staging DB | SQL Server | Pairs with SSIS natively |
| June 2026 | Warehouse | Snowflake | Cloud-native, existing expertise |
| June 2026 | Reporting | Power BI | Interactive dashboards, connects to Snowflake |
| June 2026 | SSRS | Deferred | Use only if scheduled PDF delivery needed |
| June 2026 | EDA timing | Before ETL | Understand quality issues before building pipeline |
| June 2026 | Artifact columns | Drop | Waterfall and Number of Records are BI artifacts |
| June 2026 | Load strategy | VARCHAR first | Load all as string, cast in SQL — safest approach |

---

## Document Index

| Document | Purpose | Status |
|----------|---------|--------|
| `README.md` | Project overview, tool stack, warehouse design, folder structure | ✅ Done |
| `LLD.md` | Step-by-step implementation guide for all 8 phases | ✅ Done |
| `TRACKER.md` | This file — task by task progress tracker | ✅ Done |
| `docs/eda_findings.md` | EDA output — nulls, types, anomalies, quality issues | ⬜ Not Started |
| `docs/questions.md` | 30-50+ business questions mapped to tables | ⬜ Not Started |
| `docs/schema.md` | Warehouse schema diagram + column dictionary | ⬜ Not Started |
| `docs/load_metrics.md` | SSIS load statistics | ⬜ Not Started |
| `docs/validation_report_staging.md` | SQL Server validation results | ⬜ Not Started |
| `docs/validation_report_snowflake.md` | Snowflake validation results | ⬜ Not Started |

---

## Blocked / Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Visual Studio + SSIS not installed | Blocks Phase 4 | Install now — 20-30 mins |
| Phase 2 questions too few (<30) | Warehouse design will be weak | Aim for 40+, use LLD examples as starting point |
| Snowflake credits run out | Blocks Phase 6-8 | Use X-SMALL warehouse, auto-suspend after 60 seconds |
| Negative new_cases in source | May break validations | Decision: flag as WARN, do not fail the load |

