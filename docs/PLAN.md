# Project Plan — COVID-19 Data Platform

## Project Overview

| Item | Detail |
|------|--------|
| **Project Name** | COVID-19 Data Platform — Reporting |
| **Owner** | Ak |
| **Goal** | Build a full ETL pipeline from raw CSV to reporting warehouse |
| **Stack** | SSIS + SQL Server → Power BI / Tableau / SSRS |

---

## Business Problem

> COVID-19 data exists but is not structured for reporting —
> causing slow, uninformed decisions about outbreak response.

---

## Dataset

| Attribute | Value |
|-----------|-------|
| File | owid-covid-data.csv |
| Source | Our World in Data (OWID) |
| Rows | 429,435 |
| Columns | 67 |
| Date range | 2020-01-01 → 2024-08-14 |
| Locations | 255 (195 countries + aggregates) |
| License | Creative Commons BY 4.0 |

---

## Tech Stack

| Tool | Purpose | Cost |
|------|---------|------|
| SQL Server Developer Edition | Staging + warehouse | Free |
| SSMS | DDL, validation queries, ad hoc SQL | Free |
| Visual Studio Community + SSIS | ETL packages | Free |
| Power BI / Tableau / SSRS | Reporting | TBD |

---

## Warehouse Design

**Star schema — Kimball dimensional modelling**

```
dim_date ── fact_covid_daily ── dim_location
```

| Table | Rows | Purpose |
|-------|------|---------|
| stg_covid_raw | 429,435 | Staging — all 67 cols as VARCHAR |
| dim_location | ~195 | One row per country — static demographics |
| dim_date | ~1,688 | Generated calendar table |
| fact_covid_daily | ~400k | One row per country per date — daily measures |
| dq_rejected_rows | ~26k | Rejected rows with reason codes |
| etl_validation | grows | Test results per run |

---

## Phase Plan

### Phase 1 — Study Raw Data
**Status: ✅ Complete**

| Task | Done? |
|------|-------|
| Download owid-covid-data.csv | ✅ |
| Run data_dictionary.py — profile all 67 columns | ✅ |
| Confirm 429,435 rows, 67 columns, 255 locations | ✅ |
| Identify null % per column | ✅ |
| Confirm continent IS NULL = aggregate rows (DQ-01) | ✅ |
| Classify 15 dim columns and 52 fact columns | ✅ |
| Document findings in eda_findings.md | ✅ |

**Deliverable:** `docs/eda_findings.md`

---

### Phase 2 — Define Requirements and Business Questions
**Status: ✅ Complete**

| Task | Done? |
|------|-------|
| Define business problem | ✅ |
| Confirm global scope | ✅ |
| Write functional requirements | ✅ |
| Write 38 business questions across 6 categories | ✅ |
| Map every question to tables and columns | ✅ |

**Deliverable:** `docs/requirements.md`

---

### Phase 3 — Design and Create Warehouse Schema
**Status: ✅ Complete**

| Task | Done? |
|------|-------|
| Confirm grain — one row = one country + one date | ✅ |
| Design star schema — dim_location, dim_date, fact_covid_daily | ✅ |
| Create covid_dwh database in SSMS | ✅ |
| Create stg_covid_raw (67 cols, all VARCHAR) | ✅ |
| Create dim_location (19 cols) | ✅ |
| Create dim_date (9 cols) | ✅ |
| Create fact_covid_daily (54 cols, FK constraints) | ✅ |
| Create dq_rejected_rows | ✅ |
| Create etl_validation | ✅ |

**Deliverable:** All 6 tables in `covid_dwh`

---

### Phase 4 — SSIS Package 1 (Staging Load)
**Status: ✅ Complete**

| Task | Done? |
|------|-------|
| Install Visual Studio + SSIS extension | ✅ |
| Create SSIS project — covid_etl | ✅ |
| Create FF_CovidCSV flat file connection | ✅ |
| Create OLE_SqlServer OLE DB connection | ✅ |
| Build Control Flow — Truncate → Data Flow | ✅ |
| Build Data Flow — Flat File Source → OLE DB Destination | ✅ |
| Run package — verify 429,435 rows in stg_covid_raw | ✅ |
| Run staging validation — V-01 to V-07 | ✅ |

**Deliverable:** `ssis/Package.dtsx`
**Verify:** `SELECT COUNT(*) FROM stg_covid_raw` → 429,435

---

### Phase 5 — SSIS Package 2 (Warehouse Build)
**Status: 🔄 In Progress**

| Task | Done? |
|------|-------|
| Create Package2_Warehouse.dtsx | ✅ |
| Build Control Flow — parallel dim load + fact | ✅ |
| Build Data Flow 1 — dim_date (Script Task) | ⬜ |
| Build Data Flow 2 — dim_location (DQ filter + dedup + cast) | ⬜ |
| Build Data Flow 3 — fact_covid_daily (DQ filters + lookups) | ⬜ |
| Run package — verify all tables populated | ⬜ |
| Verify dim_location ~195 rows | ⬜ |
| Verify dim_date ~1,688 rows | ⬜ |
| Verify fact_covid_daily ~400k rows | ⬜ |
| Inspect dq_rejected_rows — DQ-01 aggregates captured | ⬜ |

**Deliverable:** `ssis/Package2_Warehouse.dtsx`

---

### Phase 6 — Test and Validate
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 5 complete

| Task | Done? |
|------|-------|
| Write usp_verify_etl_load stored procedure (11 checks) | ⬜ |
| Run Volume tests — row counts per table vs staging | ⬜ |
| Run Schema tests — columns, no null FKs | ⬜ |
| Run Accuracy tests — SUM/MIN/MAX staging vs fact | ⬜ |
| Run Business rule tests — rates, dates, duplicates | ⬜ |
| All critical tests PASS | ⬜ |

**Deliverable:** `sql/usp_verify_etl_load.sql` · `docs/test_results.md`

---

### Phase 7 — Reporting
**Status: ⬜ Not Started**

**Pre-requisite:** Phase 6 complete — all critical tests passing

| Task | Done? |
|------|-------|
| Connect reporting tool to SQL Server covid_dwh | ⬜ |
| Verify star schema relationships | ⬜ |
| Build dashboards answering 38 business questions | ⬜ |
| Write SQL for all 38 questions | ⬜ |

**Deliverable:** Dashboard + `sql/analytical_queries.sql`
