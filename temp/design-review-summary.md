# Design Review Summary — COVID-19 Data Platform

This document records design decisions made, issues identified,
and resolutions applied during the planning phase.

---

## Review Date: June 2026

---

## Issues Identified and Resolved

### DR-01 — Source file column count changed
**Issue:** Original design assumed 40 columns (ECDC extract).
Full OWID dataset has 67 columns across 6 domains.

**Impact:** Staging table DDL, fact table DDL, field lineage tables
all needed to be rebuilt from scratch.

**Resolution:** Rebuilt all DDL for 67 columns. Split into domains:
cases (6), deaths (6), hospitalisation (8), testing (9),
vaccination (13), policy (1), demographics (15), excess mortality (4),
identity (4), population (1).

**Status:** ✅ Resolved

---

### DR-02 — Artifact columns in old CSV not in OWID file
**Issue:** Original design excluded `Number of Records` and `Waterfall`
as Tableau artifacts. These do not exist in the full OWID file.

**Impact:** No columns to exclude. DQ rule for artifacts removed.

**Resolution:** No action needed. Noted in eda_findings.md.

**Status:** ✅ Resolved

---

### DR-03 — 255 locations includes aggregate rows
**Issue:** OWID includes World, continents, and income groups as
rows in the same file. These have continent IS NULL.

**Impact:** dim_location would be polluted with non-country rows
if DQ-01 filter not applied. Fact table would include aggregate rows.

**Resolution:** DQ-01 rule added — continent IS NULL → dq_rejected_rows.
Expected ~26,000 rows (~6%) routed to reject table per run.

**Status:** ✅ Resolved

---

### DR-04 — Single fact table vs multiple fact tables
**Issue:** Original design considered separate fact tables for
vaccination and hospitalisation (similar to teammate's 3-table design).

**Impact:** Would add JOIN complexity for analysts and
separate ETL flows for data that shares the same source and grain.

**Resolution:** Single fact table retained. All 52 daily columns
in fact_covid_daily. Hospitalisation and vaccination nulls accepted.
Separate fact tables only justified if source files differ.

**Status:** ✅ Resolved — documented in schema-design-rationale.md

---

### DR-05 — ML feature table missing from original design
**Issue:** Original design had no dedicated ML layer.
Data scientists would need to write complex queries with
self-joins to compute lag features every time.

**Impact:** Slow model training. Risk of inconsistent lag definitions
across different data scientists' notebooks.

**Resolution:** ml_covid_features table added as separate flat table.
Pre-computed lags: 7-day, 14-day, 28-day.
Built from same staging data as star schema — no extra ingestion.

**Status:** ✅ Resolved

---

### DR-06 — Snowflake premature in original design
**Issue:** Original design included Snowflake as an active phase
before SQL Server pipeline was working end-to-end.

**Impact:** Added complexity, cost, and a migration step before
the data was even validated.

**Resolution:** Snowflake deferred to future phase.
Current pipeline: CSV → SSIS → SQL Server → Tests → Power BI.
Snowflake migration added as Phase 9 (deferred).

**Status:** ✅ Resolved

---

### DR-07 — Test strategy was reporting only
**Issue:** Original plan had `usp_verify_etl_load` as the only
validation — equivalent to reporting after the fact.

**Impact:** Row count matching alone cannot detect column swaps,
decimal shifts, or value truncation errors.

**Resolution:** Four-layer test strategy added:
Volume + Schema + Accuracy + Business rules.
Results stored in etl_validation table per run_id.
All critical tests must PASS before Power BI connects.

**Status:** ✅ Resolved — documented in testing.md

---

### DR-08 — SSMS connection blocked by Azure AD account
**Issue:** SSMS connection to local SQL Server failed because
machine was logged in with Azure AD work account
(AzureAD\akanksha.bokare@veradigm.me).
SQL Server Developer Edition was installed under a different account.

**Impact:** Could not connect to SQL Server to run DDL scripts.

**Resolution:** Installed a new SQL Server instance (MSSQLSERVER02)
with "Add current user" checked during setup.
Connected successfully via Windows Authentication on new instance.

**Server name:** PF3NN97E-924916\MSSQLSERVER02

**Status:** ✅ Resolved

---

### DR-09 — Geographic scope undefined
**Issue:** Project brief specified EU + UK only.
Team decision was needed before schema design.

**Impact:** Row counts, country list, and ML training data size
all depend on scope decision.

**Resolution:** Team chose Global scope (all ~195 countries).
Rationale: single CSV, ETL complexity unchanged, richer analysis,
more ML training data. EU+UK scope adds filter without simplifying ETL.

**Status:** ✅ Resolved — Global scope confirmed

---

### DR-10 — project-plan.md vs HLD/LLD scope confusion
**Issue:** Manager clarified that HLD and LLD are retroactive documents
written after implementation. Planning document is forward-looking.

**Impact:** Early versions of README and PLAN conflated planning
content with implementation documentation.

**Resolution:** Documents restructured:
- project-plan.md: forward-looking phases, tasks, status
- requirements.md: business problem, questions, FR/NFR
- hld.md: architecture (retroactive after implementation)
- lld.md: implementation detail (retroactive after implementation)
- schema-design-rationale.md: Kimball decisions
- data-quality.md: DQ rules taxonomy
- testing.md: verification strategy
- design-review-summary.md: this document

**Status:** ✅ Resolved

---

## Open Items

| ID | Issue | Owner | Priority |
|----|-------|-------|---------|
| OI-01 | SSIS Visual Studio not yet installed | Ak | High — blocks Phase 4 |
| OI-02 | covid_dwh database created in SSMS — DDL scripts not yet run | Ak | High — blocks Phase 4 |
| OI-03 | ML null handling strategy not confirmed (impute vs flag) | Data science team | Medium — needed before Phase 5 |
| OI-04 | Power BI licence availability | Manager | Medium — needed before Phase 7 |
| OI-05 | Snowflake free trial not activated | Ak | Low — deferred phase |

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | June 2026 | Initial design — 40 cols, 1 fact table, no ML layer |
| 0.2 | June 2026 | Updated for 67 cols, added ML feature table, deferred Snowflake |
| 0.3 | June 2026 | Added four-layer test strategy, two-model design |
| 0.4 | June 2026 | Global scope confirmed, Azure AD connection issue resolved |
| 1.0 | June 2026 | All 8 planning documents complete — ready for Phase 3 |
