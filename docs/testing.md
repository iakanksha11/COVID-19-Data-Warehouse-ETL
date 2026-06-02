# ETL Testing and Verification Strategy — COVID-19 Data Platform

After every SSIS Package 2 run, the stored procedure `usp_verify_etl_load`
runs automatically as the final step. It executes 11 checks, logs results
to `etl_validation` table, and raises an error if any critical check fails
— causing SSIS to mark the package as Failed.

> Stored procedure: `sql/sqlserver/usp_verify_etl_load.sql`
> Test scripts: `sql/sqlserver/tests/`

---

## How to Run

**One-time setup — run once in SSMS before first package execution:**
```sql
-- Creates etl_validation table and stored procedure
-- Open sql/sqlserver/usp_verify_etl_load.sql in SSMS and press F5
```

**After every SSIS run — called automatically as last Package 2 step:**
```sql
EXEC dbo.usp_verify_etl_load;
```

**To run the full test suite manually:**
```sql
-- Open sql/sqlserver/tests/run_all_tests.sql in SSMS and press F5
```

**To review verification history across all runs:**
```sql
SELECT * FROM dbo.etl_validation ORDER BY executed_at DESC;
```

---

## How SSIS Uses the Stored Procedure

Add an **Execute SQL Task** as the final step in SSIS Package 2 Control Flow:
- Connection: your SQL Server OLE DB connection
- SQL Statement: `EXEC dbo.usp_verify_etl_load;`
- On failure (RAISERROR): SSIS marks the package as Failed

**Critical checks — trigger RAISERROR and fail the package: 2, 3, 4, 7, 8, 10**
**Informational checks — logged but do not fail the package: 1, 5, 6, 9, 11**

---

## When to Run Verification

| Trigger | Action |
|---------|--------|
| After every full SSIS Package 2 run | All 11 checks run automatically |
| After re-loading a single table | Run checks relevant to that table |
| Before connecting Power BI | All 11 checks must show no critical failures |
| After schema change | Re-run all checks — verify nothing broken |

---

## Verification Checks

### Check 1 — Row Count Reconciliation (Informational)
**What:** Reports how many rows are in each table after load —
dim_location, dim_date, fact_covid_daily, ml_covid_features.

**Pass condition:** Always PASS — informational only.
Used to compare run sizes over time.

**Expected values:**
- dim_location: ~195
- dim_date: ~1,688
- fact_covid_daily: ~400,000
- ml_covid_features: ~400,000

---

### Check 2 — Null Foreign Key Check (Critical)
**What:** Confirm every row in fact_covid_daily has a valid
location_id and date_id — no nulls.

**Pass condition:** 0 rows with null FKs.

**Failure means:** SSIS Lookup transformation failed to resolve
a country name or date. Check the Lookup no-match output configuration.

```sql
SELECT COUNT(*) AS null_fk_count
FROM dbo.fact_covid_daily
WHERE location_id IS NULL OR date_id IS NULL;
-- Expected: 0
```

---

### Check 3 — Duplicate Key Check (Critical)
**What:** Confirm no (location_id, date_id) combination appears
more than once in fact_covid_daily.

**Pass condition:** 0 duplicate combinations.

**Failure means:** Package ran twice without truncating first,
or deduplication step in SSIS misconfigured.

```sql
SELECT location_id, date_id, COUNT(*) AS cnt
FROM dbo.fact_covid_daily
GROUP BY location_id, date_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows
```

---

### Check 4 — Referential Integrity Check (Critical)
**What:** Confirm every location_id in fact table exists in
dim_location, and every date_id exists in dim_date.

**Pass condition:** 0 orphan FK references.

**Failure means:** Dimensions were not loaded before facts,
or surrogate key mismatch occurred.

```sql
-- Orphan location_ids
SELECT COUNT(*) FROM dbo.fact_covid_daily f
LEFT JOIN dbo.dim_location l ON f.location_id = l.location_id
WHERE l.location_id IS NULL;
-- Expected: 0

-- Orphan date_ids
SELECT COUNT(*) FROM dbo.fact_covid_daily f
LEFT JOIN dbo.dim_date d ON f.date_id = d.date_id
WHERE d.date_id IS NULL;
-- Expected: 0
```

---

### Check 5 — Aggregate Reconciliation (Informational)
**What:** Reports SUM of key metrics (new_cases, new_deaths)
in staging vs fact table. Used as sanity check.

**Pass condition:** Always PASS — informational only.
Compare against staging totals to detect value drift.

```sql
SELECT
    'staging'         AS source,
    SUM(TRY_CAST(new_cases AS FLOAT))  AS total_new_cases,
    SUM(TRY_CAST(new_deaths AS FLOAT)) AS total_new_deaths
FROM dbo.stg_covid_raw
WHERE continent IS NOT NULL

UNION ALL

SELECT
    'fact_covid_daily' AS source,
    SUM(new_cases)     AS total_new_cases,
    SUM(new_deaths)    AS total_new_deaths
FROM dbo.fact_covid_daily;
-- Values should match
```

---

### Check 6 — DQ Reject Audit (Informational)
**What:** Reports total rejected rows in current run by reason code.

**Pass condition:** Always PASS — informational only.

```sql
SELECT reject_reason, COUNT(*) AS rejected_count
FROM dbo.dq_rejected_rows
WHERE CAST(load_timestamp AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY reject_reason
ORDER BY rejected_count DESC;
```

---

### Check 7 — Negative Value Check (Critical)
**What:** Confirm negative new_cases and new_deaths counts are
within expected range (small — OWID corrections only).

**Pass condition:** negative count < 1% of total rows.

**Failure means:** DQ rules DQ-07 not configured — too many
negative values suggests a data loading issue not corrections.

```sql
SELECT
    SUM(CASE WHEN new_cases < 0 THEN 1 ELSE 0 END)  AS neg_cases,
    SUM(CASE WHEN new_deaths < 0 THEN 1 ELSE 0 END) AS neg_deaths,
    COUNT(*) AS total_rows
FROM dbo.fact_covid_daily;
```

---

### Check 8 — Date Coverage Check (Critical)
**What:** Confirm dim_date has no gaps between 2020-01-01 and today.

**Pass condition:** Every date from 2020-01-01 to GETDATE()
exists in dim_date with no missing days.

**Failure means:** dim_date Script Task missed a range.
Re-run dim_date generation step.

```sql
WITH expected AS (
    SELECT CAST('2020-01-01' AS DATE) AS dt
    UNION ALL
    SELECT DATEADD(DAY, 1, dt) FROM expected
    WHERE dt < CAST(GETDATE() AS DATE)
)
SELECT COUNT(*) AS missing_dates
FROM expected e
LEFT JOIN dbo.dim_date d ON e.dt = d.date
WHERE d.date IS NULL
OPTION (MAXRECURSION 2000);
-- Expected: 0
```

---

### Check 9 — Monotonic Totals Check (Informational)
**What:** Confirm total_cases and total_deaths generally do not
decrease day over day per country.

**Pass condition:** Always PASS — informational only.
OWID sometimes revises historical data downward (valid).

**Action:** Log count of decreasing rows.
High count may indicate source data issue — investigate.

---

### Check 10 — Rejection Threshold Check (Critical)
**What:** Confirm unexpected rejections do not exceed 5% of total rows.
DQ-01 (aggregate rows) are excluded — they are expected.

**Pass condition:** Unexpected reject % < 5%.

| Unexpected rules | Threshold |
|-----------------|-----------|
| DQ-02 + DQ-03 + DQ-04 + DQ-05 + DQ-06 | > 5% → FAIL |

**Failure means:** Source file structure changed — column rename,
encoding issue, or format change. Check dq_rejected_rows.

---

### Check 11 — Soft Outlier Detection (Informational)
**What:** Flags statistically unusual values for human review.
Does not fail the package.

| Rule | Check | Typical cause |
|------|-------|--------------|
| OL-01 | new_cases > 1,000,000 for any country-day | Backlog correction dump |
| OL-02 | reproduction_rate > 15 | No epidemiological precedent — data error |
| OL-03 | people_vaccinated < people_fully_vaccinated | Logical impossibility |
| OL-04 | positive_rate > 1.0 | Source data issue |

---

## Pass / Fail Summary Template

Record after every load. All critical checks must PASS before
Power BI or Python connects.

| # | Check | Type | Result | Rows Flagged | Notes |
|---|-------|------|--------|-------------|-------|
| 1 | Row count reconciliation | Informational | | | |
| 2 | Null FK check | **Critical** | | | |
| 3 | Duplicate key check | **Critical** | | | |
| 4 | Referential integrity | **Critical** | | | |
| 5 | Aggregate reconciliation | Informational | | | |
| 6 | DQ reject audit | Informational | | | |
| 7 | Negative value check | **Critical** | | | |
| 8 | Date coverage check | **Critical** | | | |
| 9 | Monotonic totals check | Informational | | | |
| 10 | Rejection threshold check | **Critical** | | | |
| 11 | Soft outlier detection | Informational | | | |

**All 6 critical checks (2, 3, 4, 7, 8, 10) must PASS before proceeding.**
