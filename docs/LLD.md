# Low Level Design (LLD) — COVID-19 Data Platform

## SSIS Control Flow — Overall Sequence

```
┌──────────────────────────────────────────────────────┐
│  PACKAGE 1 — Staging Load                            │
│                                                      │
│  Step 1: Execute SQL — TRUNCATE stg_covid_raw        │
│  Step 2: Data Flow — CSV → stg_covid_raw (VARCHAR)   │
│  Step 3: Execute SQL — Run staging validation        │
│           7 checks — FAIL blocks Package 2           │
└──────────────────────────┬───────────────────────────┘
                           │ All checks PASS
                           ▼
┌──────────────────────────────────────────────────────┐
│  PACKAGE 2 — Warehouse Build                         │
│                                                      │
│  Step 1: Generate run_id (NEWID())                   │
│  Step 2: Read etl_metadata → Object variable         │
│  Step 3: ForEach Loop — iterate metadata rows        │
│          ├─ Log RUNNING to etl_execution_log         │
│          ├─ Execute SQL from sql_statement           │
│          └─ Log DONE / FAILED + rows + time          │
│                                                      │
│  Execution order (from etl_metadata.step_order):    │
│    1. dim_date (generated)                           │
│    2. dim_location (from staging)                    │
│    3. fact_covid_daily (from staging)                │
│    4. ml_covid_features (from staging + lag calc)    │
│    5–8. Validation steps                             │
│                                                      │
│  Step 4: Execute SQL — EXEC usp_verify_etl_load      │
└──────────────────────────────────────────────────────┘
```

---

## Individual Data Flow Diagrams

### Flow 1 — dim_date

```
  GENERATE                TRANSFORM                    LOAD
  ─────────────────────────────────────────────────────────
  ┌──────────────┐
  │ Script Task  │  Generates date series
  │              │  2020-01-01 → today
  │ (no CSV)     │  using recursive loop
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  year        = YEAR(date)
  │ Derived      │  month       = MONTH(date)
  │ Column       │  month_name  = DATENAME(month, date)
  │              │  quarter     = 'Q'+CAST(DATEPART(quarter,date) AS VARCHAR)
  │              │  week_number = DATEPART(iso_week, date)
  │              │  day_of_week = DATENAME(weekday, date)
  │              │  is_weekend  = CASE WHEN DATEPART(weekday,date)
  │              │                IN (1,7) THEN 1 ELSE 0 END
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ OLE DB Dest  │──────────────────────────▶ dbo.dim_date
  │ Truncate +   │  ~1,688 rows
  │ full reload  │
  └──────────────┘
```

---

### Flow 2 — dim_location

```
  EXTRACT              TRANSFORM                        LOAD
  ─────────────────────────────────────────────────────────
  ┌──────────────┐
  │ OLE DB       │  SELECT * FROM stg_covid_raw
  │ Source       │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  continent IS NULL?
  │ Conditional  │──── YES ──────────────────▶ dq_rejected_rows
  │ Split DQ-01  │  (World, Asia, High income   reason: DQ-01
  └──────┬───────┘   aggregate rows)
         │ NO — real country row
         ▼
  ┌──────────────┐
  │ Sort +       │  Deduplicate on location
  │ Aggregate    │  Keep one row per country
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  population: string → BIGINT
  │ Data         │  population_density, median_age,
  │ Conversion   │  gdp_per_capita, life_expectancy,
  │              │  aged_65_older, aged_70_older,
  │              │  diabetes_prevalence, extreme_poverty,
  │              │  handwashing_facilities, female_smokers,
  │              │  male_smokers, hospital_beds_per_thousand,
  │              │  cardiovasc_death_rate,
  │              │  human_development_index: string → FLOAT
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ OLE DB Dest  │──────────────────────────▶ dbo.dim_location
  │ Truncate +   │  ~195 rows
  │ full reload  │
  └──────────────┘
```

---

### Flow 3 — fact_covid_daily

```
  EXTRACT              TRANSFORM                        LOAD
  ─────────────────────────────────────────────────────────
  ┌──────────────┐
  │ OLE DB       │  SELECT * FROM stg_covid_raw
  │ Source       │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  record_year = YEAR(TRY_CONVERT(DATE, date))
  │ Derived      │
  │ Column       │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Conditional  │── DQ-01: continent IS NULL ──────▶ ┌─────────────────┐
  │ Split        │── DQ-02: date IS NULL ────────────▶ │ dq_rejected_rows│
  │ (DQ filter)  │── DQ-03: date > today ────────────▶ │ + reason code   │
  │              │── DQ-04: location IS NULL ────────▶ │ + source values │
  └──────┬───────┘                                     └─────────────────┘
         │ All DQ checks passed
         ▼
  ┌──────────────┐  date: string → DATE
  │ Data         │  All 52 numeric columns: string → FLOAT
  │ Conversion   │  population: string → BIGINT
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐                            ┌─────────────────────┐
  │ Lookup       │── no match ──────────────▶ │ dq_rejected_rows    │
  │ location_id  │  join: location =           │ reason: DQ-05       │
  │              │  dim_location.country       │ (country not found) │
  └──────┬───────┘                            └─────────────────────┘
         │ match found
         ▼
  ┌──────────────┐                            ┌─────────────────────┐
  │ Lookup       │── no match ──────────────▶ │ dq_rejected_rows    │
  │ date_id      │  join: date =               │ reason: DQ-06       │
  │              │  dim_date.date              │ (date not found)    │
  └──────┬───────┘                            └─────────────────────┘
         │ match found
         ▼
  ┌──────────────┐
  │ OLE DB Dest  │──────────────────────────▶ dbo.fact_covid_daily
  │ INSERT       │  ~400k rows
  │ (pre-trunc)  │
  └──────────────┘
```

---

### Flow 4 — ml_covid_features

```
  EXTRACT              TRANSFORM                        LOAD
  ─────────────────────────────────────────────────────────
  ┌──────────────┐
  │ OLE DB       │  SELECT f.*, d.*
  │ Source       │  FROM fact_covid_daily f
  │              │  JOIN dim_location d ON f.location_id = d.location_id
  └──────┬───────┘  (reads from already-loaded fact table)
         │
         ▼
  ┌──────────────┐  new_cases_lag_7   = LAG(new_cases, 7)  OVER (PARTITION BY location ORDER BY date)
  │ Derived      │  new_cases_lag_14  = LAG(new_cases, 14) OVER (...)
  │ Column       │  new_cases_lag_28  = LAG(new_cases, 28) OVER (...)
  │ (lag calcs)  │  rolling_7d_avg    = AVG(new_cases) OVER (... ROWS 6 PRECEDING)
  │              │  rolling_14d_avg   = AVG(new_cases) OVER (... ROWS 13 PRECEDING)
  └──────┬───────┘  (computed via SQL in INSERT step, not SSIS Derived Column)
         │
         ▼
  ┌──────────────┐
  │ OLE DB Dest  │──────────────────────────▶ dbo.ml_covid_features
  │ INSERT       │  ~400k rows, wide flat table
  │ (pre-trunc)  │  all features in one row, no JOINs needed
  └──────────────┘
```

---

## DQ Filter Rules

| Code | Rule | Where applied | Action |
|------|------|--------------|--------|
| DQ-01 | continent IS NULL — aggregate rows | dim_location + fact flow | Reject — expected, not an error |
| DQ-02 | date IS NULL | fact flow | Reject — data error |
| DQ-03 | date > GETDATE() | fact flow | Reject — future date |
| DQ-04 | location IS NULL | fact flow | Reject — data error |
| DQ-05 | location not found in dim_location | fact flow lookup | Reject — FK miss |
| DQ-06 | date not found in dim_date | fact flow lookup | Reject — FK miss |

**Negative new_cases:** Not rejected. OWID uses negative values for historical
corrections. Load as-is. Flag count in post-load verification.

---

## SQL Server Table Definitions

### stg_covid_raw
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
    new_cases                                  FLOAT,
    total_cases                                FLOAT,
    new_cases_smoothed                         FLOAT,
    new_cases_per_million                      FLOAT,
    total_cases_per_million                    FLOAT,
    new_cases_smoothed_per_million             FLOAT,
    new_deaths                                 FLOAT,
    total_deaths                               FLOAT,
    new_deaths_smoothed                        FLOAT,
    new_deaths_per_million                     FLOAT,
    total_deaths_per_million                   FLOAT,
    new_deaths_smoothed_per_million            FLOAT,
    reproduction_rate                          FLOAT,
    icu_patients                               FLOAT,
    icu_patients_per_million                   FLOAT,
    hosp_patients                              FLOAT,
    hosp_patients_per_million                  FLOAT,
    weekly_icu_admissions                      FLOAT,
    weekly_icu_admissions_per_million          FLOAT,
    weekly_hosp_admissions                     FLOAT,
    weekly_hosp_admissions_per_million         FLOAT,
    new_tests                                  FLOAT,
    total_tests                                FLOAT,
    new_tests_per_thousand                     FLOAT,
    total_tests_per_thousand                   FLOAT,
    new_tests_smoothed                         FLOAT,
    new_tests_smoothed_per_thousand            FLOAT,
    positive_rate                              FLOAT,
    tests_per_case                             FLOAT,
    tests_units                                VARCHAR(100),
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
    stringency_index                           FLOAT,
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
    source_file    VARCHAR(200),
    raw_location   VARCHAR(500),
    raw_date       VARCHAR(500),
    raw_continent  VARCHAR(500),
    full_row       VARCHAR(MAX),
    load_timestamp DATETIME DEFAULT GETDATE()
);
```

### etl_metadata
```sql
CREATE TABLE dbo.etl_metadata (
    job_id            INT           IDENTITY(1,1) PRIMARY KEY,
    step_order        INT           NOT NULL,
    step_type         VARCHAR(20)   NOT NULL,
    step_description  VARCHAR(500),
    source_table      VARCHAR(100),
    target_table      VARCHAR(100)  NOT NULL,
    load_type_flag    CHAR(1)       DEFAULT 'R',
    sql_statement     VARCHAR(MAX)  NOT NULL,
    is_active         BIT           DEFAULT 1,
    status            CHAR(1)       DEFAULT 'N',
    restart_flag      CHAR(1)       DEFAULT 'N',
    query_id          VARCHAR(200),
    start_date        DATETIME,
    end_date          DATETIME,
    session_id        VARCHAR(100),
    no_of_rows        BIGINT        DEFAULT 0,
    etl_load_date     DATETIME,
    error_message     VARCHAR(MAX)
);
```

### etl_execution_log
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

### etl_hist_metadata
```sql
CREATE TABLE dbo.etl_hist_metadata (
    hist_id       INT          IDENTITY(1,1) PRIMARY KEY,
    run_id        VARCHAR(50)  NOT NULL,
    job_id        INT          NOT NULL,
    start_date    DATETIME,
    end_date      DATETIME,
    status        CHAR(1)      NOT NULL,
    query_id      VARCHAR(200),
    no_of_rows    BIGINT       DEFAULT 0,
    session_id    VARCHAR(100),
    error_message VARCHAR(MAX),
    etl_load_date DATETIME     DEFAULT GETDATE()
);
```

### etl_validation
```sql
CREATE TABLE dbo.etl_validation (
    validation_id      INT           IDENTITY(1,1) PRIMARY KEY,
    run_id             VARCHAR(50)   NOT NULL,
    table_name         VARCHAR(100)  NOT NULL,
    test_layer         VARCHAR(20)   NOT NULL,
    test_name          VARCHAR(200)  NOT NULL,
    source_count       BIGINT,
    destination_count  BIGINT,
    match_pct          DECIMAL(5,2),
    expected_value     VARCHAR(200),
    actual_value       VARCHAR(200),
    status             VARCHAR(10)   NOT NULL,
    severity           VARCHAR(10)   NOT NULL DEFAULT 'CRITICAL',
    message            VARCHAR(500),
    executed_at        DATETIME      DEFAULT GETDATE()
);
```

---

## etl_metadata Rows — Initial Population

| step_order | target_table | step_type | description |
|------------|-------------|-----------|-------------|
| 1 | dim_date | INSERT | Truncate + generate dates 2020-01-01 to today |
| 2 | dim_location | INSERT | Truncate + load countries from staging (deduplicated) |
| 3 | fact_covid_daily | INSERT | Truncate + load facts with FK lookups |
| 4 | ml_covid_features | INSERT | Truncate + load wide flat table with lag features |
| 5 | dim_location | VALIDATE | Row count vs staging distinct countries |
| 6 | fact_covid_daily | VALIDATE | Row count vs staging (allow 5% DQ-01 rejects) |
| 7 | fact_covid_daily | VALIDATE | SUM(new_cases) staging vs fact |
| 8 | fact_covid_daily | VALIDATE | Business rules — rates, dates, duplicates |

---

## Load Strategy and Idempotency

| Table | Mode | Idempotent | Notes |
|-------|------|-----------|-------|
| stg_covid_raw | Truncate + full reload | Yes | Package 1 truncates before load |
| dim_date | Truncate + regenerate | Yes | Fresh every run — 2020-01-01 to today |
| dim_location | Truncate + reload | Yes | Deduplicated from staging |
| fact_covid_daily | Truncate + reload | Yes | Full reload — OWID corrections applied |
| ml_covid_features | Truncate + reload | Yes | Rebuilt from fact + lag calculation |

---

## Field Lineage — dim_location

| Source Column | SSIS Transform | Target Column |
|--------------|---------------|--------------|
| location | Pass-through | country |
| iso_code | Pass-through | code |
| continent | Pass-through — DQ-01 removes nulls | continent |
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

## Field Lineage — dim_date

| Source | Transform | Target Column |
|--------|-----------|--------------|
| Script Task | Generated 2020-01-01 → today | date |
| Derived | YEAR(date) | year |
| Derived | MONTH(date) | month |
| Derived | DATENAME(month, date) | month_name |
| Derived | 'Q'+CAST(DATEPART(quarter,date) AS VARCHAR) | quarter |
| Derived | DATEPART(iso_week, date) | week_number |
| Derived | DATENAME(weekday, date) | day_of_week |
| Derived | CASE WHEN DATEPART(weekday,date) IN (1,7) THEN 1 ELSE 0 END | is_weekend |
| — | IDENTITY | date_id |
