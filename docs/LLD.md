# Low Level Design — COVID-19 Data Warehouse

## How the two SSIS packages work together

```
  Package 1 — Staging Load          Package 2 — Warehouse Build
  ──────────────────────────         ──────────────────────────────
  Read owid-covid-data.csv           Read etl_metadata table
  Load ALL 67 cols as VARCHAR   →    Execute steps in step_order
  into stg_covid_raw                 dim_date → dim_location → fact
                                     Log every step to etl_execution_log
         │                                      │
         ▼                                      ▼
  Run staging validation         Run test suite (etl_validation)
  (SSMS — 7 checks)              PASS → connect Power BI
  Gate before Package 2          FAIL → fix ETL, re-run
```

---

## Metadata Control Tables

### etl_metadata
Defines what needs to happen. One row per step. Package 2 reads this.

```sql
CREATE TABLE dbo.etl_metadata (
    job_id            INT           IDENTITY(1,1) PRIMARY KEY,
    step_order        INT           NOT NULL,
    step_type         VARCHAR(20)   NOT NULL,  -- DDL / TRUNCATE / INSERT / VALIDATE
    step_description  VARCHAR(500),
    source_table      VARCHAR(100),
    target_table      VARCHAR(100)  NOT NULL,
    load_type_flag    CHAR(1)       DEFAULT 'R', -- R = Full Refresh
    sql_statement     VARCHAR(MAX)  NOT NULL,
    is_active         BIT           DEFAULT 1,
    status            CHAR(1)       DEFAULT 'N', -- N=not run, Y=success, E=error
    restart_flag      CHAR(1)       DEFAULT 'N', -- Y=re-run on next execution
    query_id          VARCHAR(200),
    start_date        DATETIME,
    end_date          DATETIME,
    session_id        VARCHAR(100),
    no_of_rows        BIGINT        DEFAULT 0,
    etl_load_date     DATETIME,
    error_message     VARCHAR(MAX)
);
```

### etl_hist_metadata
Full audit trail. One row per step per run. Never overwritten.

```sql
CREATE TABLE dbo.etl_hist_metadata (
    hist_id       INT          IDENTITY(1,1) PRIMARY KEY,
    run_id        VARCHAR(50)  NOT NULL,
    job_id        INT          NOT NULL,
    start_date    DATETIME,
    end_date      DATETIME,
    status        CHAR(1)      NOT NULL,  -- Y=success, E=error
    query_id      VARCHAR(200),
    no_of_rows    BIGINT       DEFAULT 0,
    session_id    VARCHAR(100),
    error_message VARCHAR(MAX),
    etl_load_date DATETIME     DEFAULT GETDATE()
);
```

### etl_execution_log
Real-time step tracking per run.

```sql
CREATE TABLE dbo.etl_execution_log (
    log_id        INT          IDENTITY(1,1) PRIMARY KEY,
    run_id        VARCHAR(50)  NOT NULL,
    metadata_id   INT,
    table_name    VARCHAR(100),
    step_type     VARCHAR(50),
    status        VARCHAR(20)  DEFAULT 'RUNNING',
    start_time    DATETIME     DEFAULT GETDATE(),
    end_time      DATETIME,
    rows_affected INT          DEFAULT 0,
    error_message VARCHAR(MAX)
);
```

### etl_validation (test results)
Four-layer test results. One row per test per run.

```sql
CREATE TABLE dbo.etl_validation (
    validation_id      INT           IDENTITY(1,1) PRIMARY KEY,
    run_id             VARCHAR(50)   NOT NULL,
    table_name         VARCHAR(100)  NOT NULL,
    test_layer         VARCHAR(20)   NOT NULL, -- VOLUME/SCHEMA/ACCURACY/BUSINESS
    test_name          VARCHAR(200)  NOT NULL,
    source_count       BIGINT,
    destination_count  BIGINT,
    match_pct          DECIMAL(5,2),
    expected_value     VARCHAR(200),
    actual_value       VARCHAR(200),
    status             VARCHAR(10)   NOT NULL, -- PASS/FAIL/WARN
    severity           VARCHAR(10)   NOT NULL DEFAULT 'CRITICAL',
    message            VARCHAR(500),
    executed_at        DATETIME      DEFAULT GETDATE()
);
```

---

## Package 1 — Staging Load

**Goal:** Get the CSV into SQL Server as fast as possible.
No type casting. No transformation. No rejection logic yet.

```
Flat File Source              OLE DB Destination
owid-covid-data.csv    →      dbo.stg_covid_raw
All 67 columns                All columns as VARCHAR(500)
```

### Staging table
```sql
CREATE TABLE dbo.stg_covid_raw (
    iso_code                                  VARCHAR(500),
    continent                                 VARCHAR(500),
    location                                  VARCHAR(500),
    date                                      VARCHAR(500),
    total_cases                               VARCHAR(500),
    new_cases                                 VARCHAR(500),
    new_cases_smoothed                        VARCHAR(500),
    total_deaths                              VARCHAR(500),
    new_deaths                                VARCHAR(500),
    new_deaths_smoothed                       VARCHAR(500),
    total_cases_per_million                   VARCHAR(500),
    new_cases_per_million                     VARCHAR(500),
    new_cases_smoothed_per_million            VARCHAR(500),
    total_deaths_per_million                  VARCHAR(500),
    new_deaths_per_million                    VARCHAR(500),
    new_deaths_smoothed_per_million           VARCHAR(500),
    reproduction_rate                         VARCHAR(500),
    icu_patients                              VARCHAR(500),
    icu_patients_per_million                  VARCHAR(500),
    hosp_patients                             VARCHAR(500),
    hosp_patients_per_million                 VARCHAR(500),
    weekly_icu_admissions                     VARCHAR(500),
    weekly_icu_admissions_per_million         VARCHAR(500),
    weekly_hosp_admissions                    VARCHAR(500),
    weekly_hosp_admissions_per_million        VARCHAR(500),
    total_tests                               VARCHAR(500),
    new_tests                                 VARCHAR(500),
    total_tests_per_thousand                  VARCHAR(500),
    new_tests_per_thousand                    VARCHAR(500),
    new_tests_smoothed                        VARCHAR(500),
    new_tests_smoothed_per_thousand           VARCHAR(500),
    positive_rate                             VARCHAR(500),
    tests_per_case                            VARCHAR(500),
    tests_units                               VARCHAR(500),
    total_vaccinations                        VARCHAR(500),
    people_vaccinated                         VARCHAR(500),
    people_fully_vaccinated                   VARCHAR(500),
    total_boosters                            VARCHAR(500),
    new_vaccinations                          VARCHAR(500),
    new_vaccinations_smoothed                 VARCHAR(500),
    total_vaccinations_per_hundred            VARCHAR(500),
    people_vaccinated_per_hundred             VARCHAR(500),
    people_fully_vaccinated_per_hundred       VARCHAR(500),
    total_boosters_per_hundred                VARCHAR(500),
    new_vaccinations_smoothed_per_million     VARCHAR(500),
    new_people_vaccinated_smoothed            VARCHAR(500),
    new_people_vaccinated_smoothed_per_hundred VARCHAR(500),
    stringency_index                          VARCHAR(500),
    population_density                        VARCHAR(500),
    median_age                                VARCHAR(500),
    aged_65_older                             VARCHAR(500),
    aged_70_older                             VARCHAR(500),
    gdp_per_capita                            VARCHAR(500),
    extreme_poverty                           VARCHAR(500),
    cardiovasc_death_rate                     VARCHAR(500),
    diabetes_prevalence                       VARCHAR(500),
    female_smokers                            VARCHAR(500),
    male_smokers                              VARCHAR(500),
    handwashing_facilities                    VARCHAR(500),
    hospital_beds_per_thousand                VARCHAR(500),
    life_expectancy                           VARCHAR(500),
    human_development_index                   VARCHAR(500),
    population                                VARCHAR(500),
    excess_mortality_cumulative_absolute      VARCHAR(500),
    excess_mortality_cumulative               VARCHAR(500),
    excess_mortality                          VARCHAR(500),
    excess_mortality_cumulative_per_million   VARCHAR(500),
    load_timestamp                            DATETIME DEFAULT GETDATE()
);
```

---

## Staging Validation Gate (SSMS — run before Package 2)

All checks must pass before running Package 2.

```sql
-- V-01: Has data
SELECT 'V-01 row_count' AS check_name,
       COUNT(*) AS value,
       CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-02: No null location
SELECT 'V-02 null_location' AS check_name,
       SUM(CASE WHEN location IS NULL OR location='' THEN 1 ELSE 0 END) AS violations,
       CASE WHEN SUM(CASE WHEN location IS NULL OR location='' THEN 1 ELSE 0 END)=0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-03: No null date
SELECT 'V-03 null_date' AS check_name,
       SUM(CASE WHEN date IS NULL OR date='' THEN 1 ELSE 0 END) AS violations,
       CASE WHEN SUM(CASE WHEN date IS NULL OR date='' THEN 1 ELSE 0 END)=0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-04: Date format valid
SELECT 'V-04 date_format' AS check_name,
       SUM(CASE WHEN TRY_CONVERT(DATE,date,120) IS NULL THEN 1 ELSE 0 END) AS violations,
       CASE WHEN SUM(CASE WHEN TRY_CONVERT(DATE,date,120) IS NULL THEN 1 ELSE 0 END)=0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-05: No duplicates
SELECT 'V-05 duplicates' AS check_name,
       COUNT(*) - COUNT(DISTINCT location+'|'+date) AS violations,
       CASE WHEN COUNT(*) - COUNT(DISTINCT location+'|'+date)=0
            THEN 'PASS' ELSE 'FAIL' END AS result
FROM dbo.stg_covid_raw;

-- V-06: positive_rate range (WARN only)
SELECT 'V-06 positive_rate' AS check_name,
       SUM(CASE WHEN TRY_CAST(positive_rate AS FLOAT)>1 THEN 1 ELSE 0 END) AS violations,
       'WARN' AS result
FROM dbo.stg_covid_raw;

-- V-07: Negative new_cases (WARN only — OWID corrections)
SELECT 'V-07 negative_cases' AS check_name,
       SUM(CASE WHEN TRY_CAST(new_cases AS FLOAT)<0 THEN 1 ELSE 0 END) AS violations,
       'WARN' AS result
FROM dbo.stg_covid_raw;
```

---

## Package 2 — Warehouse Build (Metadata-Driven)

```
Generate run_id (NEWID())
         │
         ▼
Read etl_metadata WHERE is_active=1 AND (status='N' OR restart_flag='Y')
ORDER BY step_order
         │
         ▼
ForEach Loop — iterate each metadata row
  │
  ├─ INSERT etl_execution_log (status=RUNNING, start_time)
  ├─ Execute SQL from sql_statement
  ├─ UPDATE etl_execution_log (status=DONE, rows_affected, end_time)
  └─ On failure: UPDATE etl_execution_log (status=FAILED)
                 UPDATE etl_metadata (status='E', restart_flag='Y')
```

---

## Warehouse Table Definitions

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
    human_development_index      FLOAT,
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
    fact_id                                    INT      IDENTITY(1,1) PRIMARY KEY,
    record_year                                SMALLINT NOT NULL,
    location_id                                INT      NOT NULL,
    date_id                                    INT      NOT NULL,
    -- Cases
    new_cases                                  FLOAT,
    total_cases                                FLOAT,
    new_cases_smoothed                         FLOAT,
    new_cases_per_million                      FLOAT,
    total_cases_per_million                    FLOAT,
    new_cases_smoothed_per_million             FLOAT,
    -- Deaths
    new_deaths                                 FLOAT,
    total_deaths                               FLOAT,
    new_deaths_smoothed                        FLOAT,
    new_deaths_per_million                     FLOAT,
    total_deaths_per_million                   FLOAT,
    new_deaths_smoothed_per_million            FLOAT,
    -- Transmission
    reproduction_rate                          FLOAT,
    -- Hospitalisation
    icu_patients                               FLOAT,
    icu_patients_per_million                   FLOAT,
    hosp_patients                              FLOAT,
    hosp_patients_per_million                  FLOAT,
    weekly_icu_admissions                      FLOAT,
    weekly_icu_admissions_per_million          FLOAT,
    weekly_hosp_admissions                     FLOAT,
    weekly_hosp_admissions_per_million         FLOAT,
    -- Testing
    new_tests                                  FLOAT,
    total_tests                                FLOAT,
    new_tests_per_thousand                     FLOAT,
    total_tests_per_thousand                   FLOAT,
    new_tests_smoothed                         FLOAT,
    new_tests_smoothed_per_thousand            FLOAT,
    positive_rate                              FLOAT,
    tests_per_case                             FLOAT,
    tests_units                                VARCHAR(100),
    -- Vaccinations
    total_vaccinations                         FLOAT,
    people_vaccinated                          FLOAT,
    people_fully_vaccinated                    FLOAT,
    total_boosters                             FLOAT,
    new_vaccinations                           FLOAT,
    new_vaccinations_smoothed                  FLOAT,
    total_vaccinations_per_hundred             FLOAT,
    people_vaccinated_per_hundred              FLOAT,
    people_fully_vaccinated_per_hundred        FLOAT,
    total_boosters_per_hundred                 FLOAT,
    new_vaccinations_smoothed_per_million      FLOAT,
    new_people_vaccinated_smoothed             FLOAT,
    new_people_vaccinated_smoothed_per_hundred FLOAT,
    -- Policy
    stringency_index                           FLOAT,
    -- Excess mortality
    excess_mortality_cumulative_absolute       FLOAT,
    excess_mortality_cumulative                FLOAT,
    excess_mortality                           FLOAT,
    excess_mortality_cumulative_per_million    FLOAT,
    load_timestamp                             DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_location FOREIGN KEY (location_id) REFERENCES dbo.dim_location(location_id),
    CONSTRAINT fk_date     FOREIGN KEY (date_id)     REFERENCES dbo.dim_date(date_id),
    CONSTRAINT uq_loc_date UNIQUE (location_id, date_id)
);
```

### dq_rejected_rows
```sql
CREATE TABLE dbo.dq_rejected_rows (
    reject_id      INT           IDENTITY(1,1) PRIMARY KEY,
    reject_reason  VARCHAR(20),
    raw_location   VARCHAR(500),
    raw_date       VARCHAR(500),
    raw_continent  VARCHAR(500),
    full_row       VARCHAR(MAX),
    load_timestamp DATETIME DEFAULT GETDATE()
);
```

---

## DQ Rules Applied in Package 2

| Code | Rule | Action |
|------|------|--------|
| DQ-01 | continent IS NULL — aggregate rows (World, Asia, etc.) | Route to dq_rejected_rows — expected |
| DQ-02 | date IS NULL | Route to dq_rejected_rows |
| DQ-03 | date > GETDATE() — future dates | Route to dq_rejected_rows |
| DQ-04 | location IS NULL | Route to dq_rejected_rows |
| DQ-05 | location not found in dim_location — lookup miss | Route to dq_rejected_rows |
| DQ-06 | date not found in dim_date — lookup miss | Route to dq_rejected_rows |

**Negative new_cases:** Not rejected. OWID corrections — load as-is.

---

## Post-Load Test Suite

Run after Package 2. Results go to etl_validation table.

```sql
-- VOLUME: dim_location count
INSERT INTO dbo.etl_validation (run_id,table_name,test_layer,test_name,
    source_count,destination_count,match_pct,status,severity,message)
SELECT @run_id,'dim_location','VOLUME','country count vs staging',
    (SELECT COUNT(DISTINCT location) FROM stg_covid_raw WHERE continent IS NOT NULL),
    (SELECT COUNT(*) FROM dim_location),
    CAST((SELECT COUNT(*) FROM dim_location)*100.0/
         NULLIF((SELECT COUNT(DISTINCT location) FROM stg_covid_raw WHERE continent IS NOT NULL),0) AS DECIMAL(5,2)),
    CASE WHEN (SELECT COUNT(*) FROM dim_location)=
              (SELECT COUNT(DISTINCT location) FROM stg_covid_raw WHERE continent IS NOT NULL)
         THEN 'PASS' ELSE 'FAIL' END,
    'CRITICAL','dim_location must match distinct countries in staging';

-- ACCURACY: SUM new_cases
INSERT INTO dbo.etl_validation (run_id,table_name,test_layer,test_name,
    source_count,destination_count,match_pct,status,severity,message)
SELECT @run_id,'fact_covid_daily','ACCURACY','SUM new_cases staging vs fact',
    CAST(SUM(TRY_CAST(new_cases AS FLOAT)) AS BIGINT),
    (SELECT CAST(SUM(new_cases) AS BIGINT) FROM fact_covid_daily),
    100.00,
    CASE WHEN ABS(ISNULL(SUM(TRY_CAST(new_cases AS FLOAT)),0)-
                  ISNULL((SELECT SUM(new_cases) FROM fact_covid_daily),0))<1
         THEN 'PASS' ELSE 'FAIL' END,
    'HIGH','SUM new_cases must match between staging and fact'
FROM stg_covid_raw WHERE continent IS NOT NULL;

-- BUSINESS: positive_rate range
INSERT INTO dbo.etl_validation (run_id,table_name,test_layer,test_name,
    source_count,destination_count,match_pct,status,severity,message)
SELECT @run_id,'fact_covid_daily','BUSINESS','positive_rate between 0 and 1',
    0,COUNT(*),NULL,
    CASE WHEN COUNT(*)=0 THEN 'PASS' ELSE 'FAIL' END,
    'HIGH','positive_rate must be between 0 and 1'
FROM fact_covid_daily WHERE positive_rate>1.0;
```

---

## Load Strategy

| Table | Mode | Idempotent | Notes |
|-------|------|-----------|-------|
| dim_date | Truncate + regenerate | Yes | Fresh every run — 2020-01-01 to today |
| dim_location | Truncate + reload | Yes | Deduplicated from staging |
| fact_covid_daily | Truncate + reload | Yes | Full reload — OWID corrections applied |

---

## Future Phase — Snowflake Migration

When project is complete and working end-to-end in SQL Server:

```
Export dim_location, dim_date, fact_covid_daily → CSV
PUT to Snowflake stage
COPY INTO Snowflake tables (same schema)
Rerun test suite against Snowflake
Reconnect Power BI to Snowflake
```

This is a separate phase. Not in current scope.

---

## Field Lineage Summary

### dim_location (15 columns from staging)

| Source Column | Transform | Target Column |
|--------------|-----------|--------------|
| location | Pass-through | country |
| iso_code | Pass-through | code |
| continent | Pass-through (DQ-01 removes nulls) | continent |
| population | string → BIGINT | population |
| population_density | string → FLOAT | population_density |
| median_age | string → FLOAT | median_age |
| aged_65_older | string → FLOAT | aged_65_older |
| aged_70_older | string → FLOAT | aged_70_older |
| gdp_per_capita | string → FLOAT | gdp_per_capita |
| extreme_poverty | string → FLOAT | extreme_poverty |
| handwashing_facilities | string → FLOAT | handwashing_facilities |
| female_smokers | string → FLOAT | female_smokers |
| male_smokers | string → FLOAT | male_smokers |
| hospital_beds_per_thousand | string → FLOAT | hospital_beds_per_thousand |
| life_expectancy | string → FLOAT | life_expectancy |
| diabetes_prevalence | string → FLOAT | diabetes_prevalence |
| cardiovasc_death_rate | string → FLOAT | cardiovasc_death_rate |
| human_development_index | string → FLOAT | human_development_index |
| — | IDENTITY | location_id |

### dim_date (generated — no source column)

| Source | Transform | Target Column |
|--------|-----------|--------------|
| Script Task | Generate 2020-01-01 to today | date |
| Derived | YEAR(date) | year |
| Derived | MONTH(date) | month |
| Derived | DATENAME(month,date) | month_name |
| Derived | 'Q'+CAST(DATEPART(quarter,date) AS VARCHAR) | quarter |
| Derived | DATEPART(iso_week,date) | week_number |
| Derived | DATENAME(weekday,date) | day_of_week |
| Derived | CASE WHEN DATEPART(weekday,date) IN (1,7) THEN 1 ELSE 0 END | is_weekend |
| — | IDENTITY | date_id |
