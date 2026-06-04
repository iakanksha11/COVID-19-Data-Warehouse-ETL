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

Analysts have no clean structured platform to answer questions
about COVID-19 trends. Raw CSV from OWID is not queryable by
business users. No warehouse = no reporting = decisions made
without data.

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

| Tool | Purpose | Why |
|------|---------|-----|
| SQL Server Developer Edition | Staging + warehouse | Free, pairs natively with SSIS, standard enterprise tool |
| SSMS | DDL, validation queries, ad hoc SQL | Standard SQL Server IDE |
| Visual Studio Community + SSIS | ETL packages | Enterprise ETL standard, visual pipeline builder |
| Power BI / Tableau / SSRS | Reporting | Connects directly to SQL Server star schema |

---

## Warehouse Design

### Step 1 — Start from business questions, not from the CSV

The warehouse design is derived from the 38 business questions,
not from the shape of the source file. Every table, column,
and relationship exists to answer a specific question.

Example questions that drove the design:

> "Which country had the highest deaths per million?" — needs country as a dimension
> "How did cases trend month by month?" — needs date as a dimension
> "Does GDP correlate with mortality?" — needs GDP in the same row as deaths

These questions have two parts:
- A **measure** (new_cases, total_deaths, positive_rate) — something that changes daily
- A **context** (by country, by month, by continent) — something we slice or filter by

This separation is the foundation of the warehouse design.

---

### Step 2 — Classify columns by behaviour, not by source

Each of the 67 source columns was classified by asking one question:

> Does this value change per day for the same country?

| Answer | Classification | Example columns | Table |
|--------|---------------|----------------|-------|
| Yes — changes daily | Fact / Measure | new_cases, stringency_index, positive_rate | fact_covid_daily |
| No — same every day | Dimension / Context | median_age, gdp_per_capita, population | dim_location |
| Time reference | Date dimension | date, year, month, quarter | dim_date |

This produced:
- **15 static demographic columns** → dim_location
- **52 daily changing columns** → fact_covid_daily
- **Date** → dim_date (generated, not from CSV)

---

### Step 3 — Define the grain

The grain is the most important decision in dimensional modelling.
It defines what one row in the fact table represents.

**Declared grain: one country × one day**

This is the finest level of detail in the source data.
All roll-ups (weekly, monthly, continental) are computed
at query time — never pre-aggregated in the warehouse.

Reason: Pre-aggregating loses detail. If we store only monthly
totals, we cannot answer "what was the peak single-day case count
in Germany?" The finest grain gives maximum flexibility.

---

### Step 4 — Define entities, relationships, and cardinality

```
dim_location          dim_date
(location_id PK)      (date_id PK)
     │                     │
     │ 1                   │ 1
     │                     │
     └──────── ∞ ──────────┘
           fact_covid_daily
           (location_id FK, date_id FK)
```

**dim_location → fact_covid_daily: One-to-Many**
One country appears on many dates in the fact table.
Afghanistan has one row in dim_location but 1,688 rows in fact_covid_daily.
The foreign key location_id enforces this relationship.

**dim_date → fact_covid_daily: One-to-Many**
One date appears for many countries in the fact table.
2020-03-15 has one row in dim_date but ~195 rows in fact_covid_daily.
The foreign key date_id enforces this relationship.

**fact_covid_daily grain constraint:**
The combination (location_id, date_id) must be unique.
One country cannot appear twice on the same date.
Enforced by UNIQUE constraint uq_loc_date.

---

### Step 5 — Why star schema, not flat table or 3NF

**Why not a flat table (everything in one table)?**
If we kept all 67 columns in one table, median_age for Afghanistan
would be repeated 1,688 times — once per day. This is:
- Storage waste
- Update anomaly risk (if median_age changes, must update 1,688 rows)
- Analytically misleading (aggregating median_age over time makes no sense)

**Why not 3NF (fully normalised)?**
3NF is designed for transactional systems — banking, orders, inventory.
It minimises redundancy but requires many JOINs for every query.
For analytical reporting, 3NF is too slow and too complex to query.

**Why star schema?**
Star schema is the standard for analytical warehouses (Kimball method) because:
- One JOIN to any dimension — simple queries, fast execution
- BI tools (Power BI, Tableau) auto-detect and use star schema relationships
- Dimensions store context once — no redundancy
- Facts store measures at finest grain — full flexibility for aggregation

---

### Step 6 — Table summary with justification

| Table | Rows | Why it exists |
|-------|------|--------------|
| stg_covid_raw | 429,435 | Landing zone — all 67 cols as VARCHAR. Decouples ingestion from transformation. Allows validation before warehouse load. |
| dim_location | ~195 | One row per country. Stores static demographics that never change daily. Answers "which country" and "what is the country profile" questions. |
| dim_date | ~1,688 | Generated calendar table. Stores pre-computed date attributes (year, month, quarter) so queries never need to calculate them at runtime. |
| fact_covid_daily | ~400k | One row per country per date. Stores all 52 daily measures. The primary query table for all 38 business questions. |
| dq_rejected_rows | ~26k | Audit trail for every rejected row. No row is ever silently dropped. Enables investigation of data quality issues without re-reading the CSV. |
| etl_validation | grows | Test results per run. Enables go/no-go decision before reporting connects. |

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
| Derive grain from business questions | ✅ |
| Classify 67 columns — 15 dim, 52 fact | ✅ |
| Define entities, relationships, cardinality | ✅ |
| Design star schema — dim_location, dim_date, fact_covid_daily | ✅ |
| Create covid_dwh database in SSMS | ✅ |
| Create all 6 tables with constraints | ✅ |

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

---

### Phase 5 — SSIS Package 2 (Warehouse Build)
**Status: 🔄 In Progress**

| Task | Done? |
|------|-------|
| Create Package2_Warehouse.dtsx | ✅ |
| Build Control Flow — parallel dim load + fact | ✅ |
| Build Data Flow 1 — dim_date (Script Task) | ✅ |
| Build Data Flow 2 — dim_location | ✅ |
| Build Data Flow 3 — fact_covid_daily | ✅ |
| Fix dim_location — 243 rows → ~195 | ⬜ |
| Run package end-to-end — verify all counts | ⬜ |
| Verify dim_location ~195 rows | ⬜ |
| Verify dim_date ~2,346 rows | ✅ |
| Verify fact_covid_daily ~400k rows | ✅ 401,502 |
| Truncate dq_rejected_rows and reload cleanly | ⬜ |

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
