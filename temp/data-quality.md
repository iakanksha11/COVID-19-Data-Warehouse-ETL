# Data Quality — COVID-19 Data Platform

## Overview

Data quality is enforced at three points:

```
Staging load (Package 1)    Warehouse build (Package 2)    Post-load tests
        │                            │                           │
VARCHAR-first                   DQ-01 to DQ-06            4-layer test suite
No rejection                    Conditional Split           etl_validation table
Everything in                   Route bad rows to           PASS/FAIL/WARN
                                dq_rejected_rows            per check
```

---

## DQ Rule Taxonomy

| Rule ID | Name | Type | Where applied | Action |
|---------|------|------|--------------|--------|
| DQ-CAST | Type cast failure | Hard | Package 2 — Data Conversion | Row fails → package fails if uncaught |
| DQ-01 | Aggregate row filter | Expected | Package 2 — dim_location + fact flow | Route to dq_rejected_rows |
| DQ-02 | Null date | Hard | Package 2 — fact flow | Route to dq_rejected_rows |
| DQ-03 | Future date | Hard | Package 2 — fact flow | Route to dq_rejected_rows |
| DQ-04 | Null location | Hard | Package 2 — fact flow | Route to dq_rejected_rows |
| DQ-05 | Location lookup miss | Hard | Package 2 — fact flow | Route to dq_rejected_rows |
| DQ-06 | Date lookup miss | Hard | Package 2 — fact flow | Route to dq_rejected_rows |
| DQ-07 | Negative new_cases | Soft | Post-load verification | Flag count — do not reject |
| DQ-08 | positive_rate > 1.0 | Soft | Post-load verification | Flag count — do not reject |
| DQ-09 | stringency_index > 100 | Hard | Post-load verification | Flag — investigate |
| DQ-10 | Rejection rate > threshold | Hard | Post-load verification | Fail package if > 5% unexpected |

---

## Rule Details

### DQ-01 — Aggregate Row Filter
**What:** Rows where continent IS NULL are aggregate locations:
World, Asia, Africa, Europe, North America, South America,
Oceania, High income, Low income, Upper middle income, Lower middle income.

**Why expected:** OWID includes continental and income-group aggregates
as rows in the same file as country data. They have iso_codes prefixed
with `OWID_` (e.g., OWID_AFR, OWID_HIC).

**Volume:** ~26,000 rows (~6% of total) routed to dq_rejected_rows.

**Action:** Route to dq_rejected_rows with reason DQ-01.
These are excluded from dim_location and fact_covid_daily.
This is not an error — it is by design.

---

### DQ-02 — Null Date
**What:** Rows where date column is NULL or empty string.

**Expected count:** 0. Any row without a date cannot be placed
in the time dimension and cannot be used for trend analysis.

**Action:** Route to dq_rejected_rows with reason DQ-02.

---

### DQ-03 — Future Date
**What:** Rows where date > GETDATE().

**Expected count:** 0. OWID does not publish future dates.
Any future date indicates a parsing error or source data issue.

**Action:** Route to dq_rejected_rows with reason DQ-03.

---

### DQ-04 — Null Location
**What:** Rows where location is NULL or empty string.

**Expected count:** 0. Every row must have a country name
to be joinable to dim_location.

**Action:** Route to dq_rejected_rows with reason DQ-04.

---

### DQ-05 — Location Lookup Miss
**What:** Rows where location value does not match any country
in dim_location after it has been loaded.

**Expected count:** 0 after DQ-01 removes aggregates.
A miss here means dim_location was not loaded correctly,
or a country name changed between OWID updates.

**Action:** Route to dq_rejected_rows with reason DQ-05.
Investigate country name mismatch if count > 0.

---

### DQ-06 — Date Lookup Miss
**What:** Rows where date value does not match any date
in dim_date after it has been loaded.

**Expected count:** 0. dim_date covers 2020-01-01 to today.
A miss here means dim_date generation failed or missed a date.

**Action:** Route to dq_rejected_rows with reason DQ-06.
Re-run dim_date generation if count > 0.

---

### DQ-07 — Negative new_cases (Soft)
**What:** Rows where new_cases < 0 or new_deaths < 0 in the loaded fact table.

**Why soft:** OWID publishes negative values as historical corrections.
When a country revises its historical case count downward,
OWID represents this as a negative daily value.
This is valid data — not a data error.

**Expected count:** Small — typically < 0.1% of rows.

**Action:** Load as-is. Flag count in post-load verification output.
Document the count and countries in the run log.

---

### DQ-08 — positive_rate > 1.0 (Soft)
**What:** Rows where positive_rate > 1.0 in the loaded fact table.

**Why soft:** positive_rate should be between 0 and 1 (0% to 100%).
Values above 1.0 are rare edge cases in the OWID data —
typically caused by denominator issues in testing data.

**Expected count:** Very small — < 0.01% of rows.

**Action:** Load as-is. Flag count in post-load verification.
Do not use these rows in positivity rate calculations without filtering.

---

### DQ-09 — stringency_index > 100 (Hard)
**What:** stringency_index should be between 0 and 100.
Values above 100 indicate a source data error.

**Expected count:** 0.

**Action:** Flag in post-load verification. Investigate source if > 0.

---

### DQ-10 — Rejection Rate Threshold (Hard)
**What:** Checks that unexpected rejections do not exceed 5% of total rows.
DQ-01 rejections are excluded — they are expected.

| Unexpected rejection rules | Threshold |
|---------------------------|-----------|
| DQ-02 + DQ-03 + DQ-04 + DQ-05 + DQ-06 | > 5% → FAIL |

**Why 5%:** OWID publishes consistent data. An unexpected rejection
rate above 5% indicates a structural change in the source file
(e.g., column rename, added columns, encoding change).

**Action:** If threshold exceeded — stop. Do not use data for
reporting until issue is investigated and resolved.

---

## dq_rejected_rows Table

Every rejected row is captured here with full context.

```sql
CREATE TABLE dbo.dq_rejected_rows (
    reject_id      INT           IDENTITY(1,1) PRIMARY KEY,
    reject_reason  VARCHAR(20),   -- DQ-01 through DQ-06
    source_file    VARCHAR(200),
    raw_location   VARCHAR(500),
    raw_date       VARCHAR(500),
    raw_continent  VARCHAR(500),
    full_row       VARCHAR(MAX),
    load_timestamp DATETIME DEFAULT GETDATE()
);
```

**How to investigate rejections after a run:**
```sql
-- Count by reason code
SELECT reject_reason, COUNT(*) AS rejected_count
FROM dbo.dq_rejected_rows
WHERE CAST(load_timestamp AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY reject_reason
ORDER BY rejected_count DESC;

-- Inspect specific DQ-05 misses (location lookup failures)
SELECT raw_location, COUNT(*) AS cnt
FROM dbo.dq_rejected_rows
WHERE reject_reason = 'DQ-05'
AND CAST(load_timestamp AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY raw_location
ORDER BY cnt DESC;
```

---

## Known Data Quality Issues in OWID Source

These are known characteristics of the source data.
They are documented here so anyone working with the warehouse
understands what they are and why they exist.

| Issue | Scope | Decision |
|-------|-------|---------|
| Negative new_cases / new_deaths | Small — OWID corrections | Load as-is — DQ-07 flags count |
| positive_rate > 1.0 | Very rare | Load as-is — DQ-08 flags count |
| Testing data 82% null | Global — sparse reporting | Load as-is — nulls expected |
| Hospitalisation data 90-97% null | Global — ~40 countries report | Load as-is — nulls expected |
| Excess mortality 97% null | Global — ~30 countries report | Load as-is — nulls expected |
| reproduction_rate min = -0.07 | Rare | Load as-is — flag as anomaly |
| tests_per_case max = 1,023,631 | Single outlier | Load as-is — document as known outlier |
| continent IS NULL rows (~6%) | Expected — aggregate rows | Route to dq_rejected_rows DQ-01 |
