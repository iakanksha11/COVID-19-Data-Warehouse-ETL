# Low Level Design — COVID-19 Data Warehouse

## How the two SSIS packages work together

```
  Package 1 — Staging Load          Package 2 — Warehouse Build
  ──────────────────────────         ──────────────────────────────
  Read covid_ecdc.csv                Read etl_metadata table
  Load ALL columns as VARCHAR   →    Execute steps in step_order
  into stg_covid_raw                 dim_date → dim_location → fact
                                     Log every step to etl_execution_log
         │                                      │
         ▼                                      ▼
  Run staging validation         Post-load: EXEC usp_verify_etl_load
  (SSMS — manual gate)           PASS → done   FAIL → package fails
         │
         ▼
  Only run Package 2 if
  all validations pass
```

---

## Metadata Control Tables

These two tables replace hardcoded SSIS logic. Package 2 reads them at runtime.

### etl_metadata
Defines what needs to happen. One row per step per table. Change config here,
not in the SSIS package.

```sql
CREATE TABLE dbo.etl_metadata (
    metadata_id      INT           IDENTITY(1,1) PRIMARY KEY,
    package_name     VARCHAR(50),   -- 'WAREHOUSE_BUILD'
    table_name       VARCHAR(100),  -- 'dim_location', 'fact_covid_daily'
    step_order       INT,           -- execution sequence
    step_type        VARCHAR(50),   -- 'TRUNCATE', 'INSERT', 'VALIDATE'
    step_description VARCHAR(500),
    sql_file         VARCHAR(200),  -- path to .sql file to execute
    is_active        BIT DEFAULT 1  -- set 0 to skip without deleting
);
```

Rows loaded at project setup:

| step_order | table_name | step_type | step_description |
|------------|------------|-----------|-----------------|
| 1 | dim_date | GENERATE | Truncate and regenerate all dates 2020-01-01 → today |
| 2 | dim_location | TRUNCATE | Truncate dim_location |
| 3 | dim_location | INSERT | Load countries from stg_covid_raw (deduplicated) |
| 4 | fact_covid_daily | TRUNCATE | Truncate fact_covid_daily |
| 5 | fact_covid_daily | INSERT | Load fact rows — lookup location_id and date_id |
| 6 | fact_covid_daily | VALIDATE | EXEC usp_verify_etl_load |

### etl_execution_log
Records what actually happened. One row per step per run. Never overwritten.

```sql
CREATE TABLE dbo.etl_execution_log (
    log_id        INT           IDENTITY(1,1) PRIMARY KEY,
    run_id        VARCHAR(50),   -- NEWID() at package start — ties all steps together
    metadata_id   INT,           -- FK → etl_metadata
    table_name    VARCHAR(100),
    step_type     VARCHAR(50),
    status        VARCHAR(20),   -- RUNNING / DONE / FAILED / SKIPPED
    start_time    DATETIME,
    end_time      DATETIME,
    rows_affected INT,
    error_message VARCHAR(MAX)
);
```

---

## Package 1 — Staging Load (SSIS Data Flow)

**Purpose:** Get the raw CSV into SQL Server as fast as possible.
No type casting. No transformation. No rejection logic yet.

```
  Flat File Source              OLE DB Destination
  covid_ecdc.csv          →     dbo.stg_covid_raw
  All 40 columns                All columns as VARCHAR(500)
  Exclude: Number of Records    Except: Number of Records, Waterfall
           Waterfall            (never loaded — BI artifacts)
```

**Staging table — why all VARCHAR:**
If SSIS tries to load `new_cases = ""` into a FLOAT column, the row fails.
Load everything as string first. Validate in SSMS. Then cast in Package 2.
One failed type conversion should not kill the entire load.

```sql
CREATE TABLE dbo.stg_covid_raw (
    location                         VARCHAR(500),
    continent                        VARCHAR(500),
    date                             VARCHAR(500),
    iso_code                         VARCHAR(500),
    tests_units                      VARCHAR(500),
    aged_65_older                    VARCHAR(500),
    aged_70_older                    VARCHAR(500),
    cardiovasc_death_rate            VARCHAR(500),
    deathp100k                       VARCHAR(500),
    diabetes_prevalence              VARCHAR(500),
    extreme_poverty                  VARCHAR(500),
    female_smokers                   VARCHAR(500),
    gdp_per_capita                   VARCHAR(500),
    handwashing_facilities           VARCHAR(500),
    hospital_beds_per_thousand       VARCHAR(500),
    life_expectancy                  VARCHAR(500),
    male_smokers                     VARCHAR(500),
    median_age                       VARCHAR(500),
    mortality_rate                   VARCHAR(500),
    new_cases                        VARCHAR(500),
    new_cases_per_million            VARCHAR(500),
    new_deaths                       VARCHAR(500),
    new_deaths_per_million           VARCHAR(500),
    new_tests                        VARCHAR(500),
    new_tests_per_thousand           VARCHAR(500),
    new_tests_smoothed               VARCHAR(500),
    new_tests_smoothed_per_thousand  VARCHAR(500),
    population                       VARCHAR(500),
    population_density               VARCHAR(500),
    positive_rate                    VARCHAR(500),
    stringency_index                 VARCHAR(500),
    tests_per_case                   VARCHAR(500),
    total_cases                      VARCHAR(500),
    total_cases_per_million          VARCHAR(500),
    total_deaths                     VARCHAR(500),
    total_deaths_per_million         VARCHAR(500),
    total_tests                      VARCHAR(500),
    total_tests_per_thousand         VARCHAR(500),
    load_timestamp                   DATETIME DEFAULT GETDATE()
);
```

---

## Staging Validation Gate (SSMS — run before Package 2)

All checks must pass before running Package 2. These are queries run manually
in SSMS. If any FAIL — stop, investigate, fix, re-run Package 1.

```sql
-- V-01: Row count — staging has data
SELECT 'V-01 row_count' AS check_name,
       COUNT(*) AS value,
       CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-02: No null location
SELECT 'V-02 null_location' AS check_name,
       SUM(CASE WHEN location IS NULL OR location = '' THEN 1 ELSE 0 END) AS violations,
       CASE WHEN SUM(CASE WHEN location IS NULL OR location = '' THEN 1 ELSE 0 END) = 0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-03: No null date
SELECT 'V-03 null_date' AS check_name,
       SUM(CASE WHEN date IS NULL OR date = '' THEN 1 ELSE 0 END) AS violations,
       CASE WHEN SUM(CASE WHEN date IS NULL OR date = '' THEN 1 ELSE 0 END) = 0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-04: Date format is parseable
SELECT 'V-04 date_format' AS check_name,
       SUM(CASE WHEN TRY_CONVERT(DATE, date, 120) IS NULL THEN 1 ELSE 0 END) AS violations,
       CASE WHEN SUM(CASE WHEN TRY_CONVERT(DATE, date, 120) IS NULL THEN 1 ELSE 0 END) = 0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-05: No duplicate location + date
SELECT 'V-05 duplicates' AS check_name,
       COUNT(*) - COUNT(DISTINCT location + '|' + date) AS violations,
       CASE WHEN COUNT(*) - COUNT(DISTINCT location + '|' + date) = 0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-06: positive_rate in range (0-1) — WARN not fail
SELECT 'V-06 positive_rate_range' AS check_name,
       SUM(CASE WHEN TRY_CAST(positive_rate AS FLOAT) > 1 THEN 1 ELSE 0 END) AS violations,
       'WARN' AS result
FROM dbo.stg_covid_raw;

-- V-07: Negative new_cases — WARN not fail (OWID corrections)
SELECT 'V-07 negative_cases' AS check_name,
       SUM(CASE WHEN TRY_CAST(new_cases AS FLOAT) < 0 THEN 1 ELSE 0 END) AS violations,
       'WARN' AS result
FROM dbo.stg_covid_raw;
```

---

## Package 2 — Warehouse Build (Metadata-Driven)

**Control flow inside Package 2:**

```
  Execute SQL Task
  Generate run_id = CAST(NEWID() AS VARCHAR(50))
  Store in SSIS variable: @run_id
         │
         ▼
  Execute SQL Task
  SELECT metadata_id, table_name, step_type, sql_file
  FROM etl_metadata
  WHERE is_active = 1
  ORDER BY step_order
  → Result stored in Object variable: @metadata_recordset
         │
         ▼
  ForEach Loop Container
  (ADO enumerator over @metadata_recordset)
         │
         ├─ Map variables: @metadata_id, @table_name, @step_type, @sql_file
         │
         ├─ Execute SQL Task: INSERT etl_execution_log
         │  (run_id, metadata_id, status = 'RUNNING', start_time = GETDATE())
         │
         ├─ Execute SQL Task: Run the SQL from @sql_file
         │  (Expression: "EXEC sp_executesql N'" + @sql_file_content + "'")
         │
         └─ Execute SQL Task: UPDATE etl_execution_log
            SET status = 'DONE', end_time = GETDATE(), rows_affected = @@ROWCOUNT
            On failure path → status = 'FAILED', error_message = @ErrorDescription
```

---

## Warehouse Table Definitions (SQL Server)

### dim_location
```sql
CREATE TABLE dbo.dim_location (
    location_id                  INT          IDENTITY(1,1) PRIMARY KEY,
    country                      VARCHAR(100) NOT NULL,
    code                         VARCHAR(10),
    continent                    VARCHAR(50),
    population                   BIGINT,
    population_density           FLOAT,
    median_age                   FLOAT,
    aged_65_older                FLOAT,
    aged_70_older                FLOAT,
    gdp_per_capita               FLOAT,
    extreme_poverty              FLOAT,
    handwashing_facilities       FLOAT,
    female_smokers               FLOAT,
    male_smokers                 FLOAT,
    hospital_beds_per_thousand   FLOAT,
    life_expectancy              FLOAT,
    diabetes_prevalence          FLOAT,
    cardiovasc_death_rate        FLOAT,
    load_timestamp               DATETIME DEFAULT GETDATE()
);
```

### dim_date
```sql
CREATE TABLE dbo.dim_date (
    date_id       INT         IDENTITY(1,1) PRIMARY KEY,
    date          DATE        NOT NULL UNIQUE,
    year          SMALLINT,
    month         TINYINT,
    month_name    VARCHAR(20),
    quarter       CHAR(2),
    week_number   TINYINT,
    day_of_week   VARCHAR(20),
    is_weekend    BIT
);
```

### fact_covid_daily
```sql
CREATE TABLE dbo.fact_covid_daily (
    fact_id                          INT      IDENTITY(1,1) PRIMARY KEY,
    record_year                      SMALLINT NOT NULL,
    location_id                      INT      NOT NULL,
    date_id                          INT      NOT NULL,
    new_cases                        FLOAT,
    total_cases                      FLOAT,
    new_cases_per_million            FLOAT,
    total_cases_per_million          FLOAT,
    new_deaths                       FLOAT,
    total_deaths                     FLOAT,
    new_deaths_per_million           FLOAT,
    total_deaths_per_million         FLOAT,
    new_tests                        FLOAT,
    total_tests                      FLOAT,
    new_tests_per_thousand           FLOAT,
    total_tests_per_thousand         FLOAT,
    new_tests_smoothed               FLOAT,
    new_tests_smoothed_per_thousand  FLOAT,
    positive_rate                    FLOAT,
    tests_per_case                   FLOAT,
    stringency_index                 FLOAT,
    deathp100k                       FLOAT,
    mortality_rate                   FLOAT,
    load_timestamp                   DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_location  FOREIGN KEY (location_id) REFERENCES dbo.dim_location(location_id),
    CONSTRAINT fk_date      FOREIGN KEY (date_id)     REFERENCES dbo.dim_date(date_id),
    CONSTRAINT uq_loc_date  UNIQUE (location_id, date_id)
);
```

### dq_rejected_rows
```sql
CREATE TABLE dbo.dq_rejected_rows (
    reject_id      INT           IDENTITY(1,1) PRIMARY KEY,
    reject_reason  VARCHAR(20),  -- DQ-01 through DQ-06
    raw_location   VARCHAR(500),
    raw_date       VARCHAR(500),
    raw_continent  VARCHAR(500),
    full_row       VARCHAR(MAX),
    load_timestamp DATETIME DEFAULT GETDATE()
);
```

---

## DQ Rules Applied in Package 2 Data Flows

| Code | Rule | Applied in | Action |
|------|------|-----------|--------|
| DQ-01 | `continent IS NULL` — aggregate rows (World, Asia, etc.) | dim_location + fact flows | Route to dq_rejected_rows — expected, not an error |
| DQ-02 | `date IS NULL` | fact flow | Route to dq_rejected_rows |
| DQ-03 | `date > GETDATE()` — future dates | fact flow | Route to dq_rejected_rows |
| DQ-04 | `location IS NULL` | fact flow | Route to dq_rejected_rows |
| DQ-05 | location not found in dim_location — lookup miss | fact flow | Route to dq_rejected_rows |
| DQ-06 | date not found in dim_date — lookup miss | fact flow | Route to dq_rejected_rows |

**Negative new_cases:** Not rejected. OWID uses negative values to publish corrections
to historical data. Loading them as-is ensures cumulative totals stay accurate.
The post-load procedure flags the count as a warning.

---

## Post-Load Verification (usp_verify_etl_load)

Called as the final step in Package 2 via Execute SQL Task.
Any RAISE ERROR causes the SSIS package to fail and alerts the operator.

| Check | Type | Condition |
|-------|------|-----------|
| fact_covid_daily has rows | FAIL | COUNT(*) = 0 |
| dim_location has rows | FAIL | COUNT(*) = 0 |
| dim_date has rows | FAIL | COUNT(*) = 0 |
| No orphan location_id | FAIL | FK mismatch exists |
| No orphan date_id | FAIL | FK mismatch exists |
| No null FK in fact table | FAIL | location_id or date_id IS NULL |
| positive_rate > 1.0 | WARN | COUNT — logged, not failed |
| Unexpected reject rate > 5% | FAIL | DQ-02 to DQ-06 rejects ÷ total rows |
| Negative new_cases | WARN | COUNT — logged, not failed |

---

## Snowflake Migration (Phase 5)

Same star schema rebuilt in Snowflake. No schema redesign needed.

```
  SQL Server                       Snowflake
  ──────────────                   ──────────────────────
  Export dim_location   →  PUT  →  COPY INTO dim_location
  Export dim_date       →  PUT  →  COPY INTO dim_date
  Export fact_covid_daily → PUT → COPY INTO fact_covid_daily
```

Snowflake objects created:
- `DATABASE: COVID_DWH`
- `SCHEMA: ANALYTICS`
- `WAREHOUSE: COMPUTE_WH (X-SMALL, auto-suspend 60s)`
- `STAGE: COVID_STAGE`
- `FILE FORMAT: CSV_FORMAT`

Power BI connects to Snowflake (not SQL Server) for production reporting.

---

## Field Lineage — Where Every Column Comes From

### dim_location

| Source Column | Transform in SSIS | Target Column | Notes |
|--------------|-------------------|--------------|-------|
| `location` | Pass-through | `country` | |
| `iso_code` | Pass-through | `code` | |
| `continent` | Pass-through | `continent` | DQ-01 removes null rows before this |
| `population` | string → BIGINT | `population` | |
| `population_density` | string → FLOAT | `population_density` | |
| `median_age` | string → FLOAT | `median_age` | |
| `aged_65_older` | string → FLOAT | `aged_65_older` | |
| `aged_70_older` | string → FLOAT | `aged_70_older` | |
| `gdp_per_capita` | string → FLOAT | `gdp_per_capita` | |
| `extreme_poverty` | string → FLOAT | `extreme_poverty` | ~45% null |
| `handwashing_facilities` | string → FLOAT | `handwashing_facilities` | ~35% null |
| `female_smokers` | string → FLOAT | `female_smokers` | |
| `male_smokers` | string → FLOAT | `male_smokers` | |
| `hospital_beds_per_thousand` | string → FLOAT | `hospital_beds_per_thousand` | |
| `life_expectancy` | string → FLOAT | `life_expectancy` | |
| `diabetes_prevalence` | string → FLOAT | `diabetes_prevalence` | |
| `cardiovasc_death_rate` | string → FLOAT | `cardiovasc_death_rate` | |
| — | IDENTITY | `location_id` | Auto-generated surrogate key |

### dim_date

| Source | Transform | Target Column | Notes |
|--------|-----------|--------------|-------|
| Script Task — generated | None | `date` | 2020-01-01 → today |
| Derived from date | YEAR(date) | `year` | |
| Derived from date | MONTH(date) | `month` | |
| Derived from date | DATENAME(month, date) | `month_name` | e.g. March |
| Derived from date | 'Q' + CAST(DATEPART(quarter,date) AS VARCHAR) | `quarter` | e.g. Q1 |
| Derived from date | DATEPART(iso_week, date) | `week_number` | |
| Derived from date | DATENAME(weekday, date) | `day_of_week` | e.g. Monday |
| Derived from date | CASE WHEN DATEPART(weekday,date) IN (1,7) THEN 1 ELSE 0 END | `is_weekend` | |
| — | IDENTITY | `date_id` | Auto-generated surrogate key |

### fact_covid_daily

| Source Column | Transform | Target Column | Notes |
|--------------|-----------|--------------|-------|
| `date` | string → DATE, then YEAR() | `record_year` | Partition key |
| Lookup → dim_location | Match on location name | `location_id` | FK |
| Lookup → dim_date | Match on date value | `date_id` | FK |
| `new_cases` | string → FLOAT | `new_cases` | Negative = OWID correction |
| `total_cases` | string → FLOAT | `total_cases` | |
| `new_cases_per_million` | string → FLOAT | `new_cases_per_million` | Pre-computed |
| `total_cases_per_million` | string → FLOAT | `total_cases_per_million` | Pre-computed |
| `new_deaths` | string → FLOAT | `new_deaths` | Negative = OWID correction |
| `total_deaths` | string → FLOAT | `total_deaths` | |
| `new_deaths_per_million` | string → FLOAT | `new_deaths_per_million` | Pre-computed |
| `total_deaths_per_million` | string → FLOAT | `total_deaths_per_million` | Pre-computed |
| `new_tests` | string → FLOAT | `new_tests` | ~50% null |
| `total_tests` | string → FLOAT | `total_tests` | |
| `new_tests_per_thousand` | string → FLOAT | `new_tests_per_thousand` | Pre-computed |
| `total_tests_per_thousand` | string → FLOAT | `total_tests_per_thousand` | Pre-computed |
| `new_tests_smoothed` | string → FLOAT | `new_tests_smoothed` | 7-day avg, pre-computed |
| `new_tests_smoothed_per_thousand` | string → FLOAT | `new_tests_smoothed_per_thousand` | Pre-computed |
| `positive_rate` | string → FLOAT | `positive_rate` | ~82% null — warn if > 1.0 |
| `tests_per_case` | string → FLOAT | `tests_per_case` | Nullable |
| `stringency_index` | string → FLOAT | `stringency_index` | 0–100 |
| `Deathp100K` | string → FLOAT | `deathp100k` | Pre-computed |
| `Mortality Rate` | string → FLOAT | `mortality_rate` | Pre-computed |
| `Number of Records` | Excluded | — | BI artifact |
| `Waterfall` | Excluded | — | BI artifact |
