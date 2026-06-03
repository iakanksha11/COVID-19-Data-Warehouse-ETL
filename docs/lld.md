# Low Level Design (LLD) — COVID-19 Data Platform

## SSIS Control Flow — Package 2

```
  Truncate dim_date          Truncate dim_location
        │                           │
        ▼                           ▼
  Data Flow 1               Data Flow 2
  Load dim_date             Load dim_location
  (Script Task)             (DQ filter + dedup + cast)
        │                           │
        └──────── AND ──────────────┘
                   │ (both must complete)
                   ▼
         Truncate fact_covid_daily
                   │
                   ▼
          Data Flow 3
          Load fact_covid_daily
          (DQ filters + lookups + cast)
                   │
                   ▼
          Execute SQL Task
          EXEC usp_verify_etl_load
```

---

## Data Flow 1 — dim_date

```
  Script Component (Source)
  C# generates dates 2020-01-01 → today
  Output columns:
    date         DT_DBDATE
    year         DT_I2
    month        DT_UI1
    month_name   DT_STR(20)
    quarter      DT_STR(2)
    week_number  DT_UI1
    day_of_week  DT_STR(20)
    is_weekend   DT_BOOL
         │
         ▼
  OLE DB Destination → dbo.dim_date
```

**C# logic inside Script Component:**
```csharp
DateTime startDate = new DateTime(2020, 1, 1);
DateTime endDate = DateTime.Today;

for (DateTime dt = startDate; dt <= endDate; dt = dt.AddDays(1))
{
    OutputBuffer.AddRow();
    OutputBuffer.date        = dt;
    OutputBuffer.year        = (short)dt.Year;
    OutputBuffer.month       = (byte)dt.Month;
    OutputBuffer.month_name  = dt.ToString("MMMM");
    OutputBuffer.quarter     = "Q" + ((dt.Month - 1) / 3 + 1).ToString();
    OutputBuffer.week_number = (byte)System.Globalization.ISOWeek.GetWeekOfYear(dt);
    OutputBuffer.day_of_week = dt.ToString("dddd");
    OutputBuffer.is_weekend  = (dt.DayOfWeek == DayOfWeek.Saturday ||
                                dt.DayOfWeek == DayOfWeek.Sunday);
}
```

---

## Data Flow 2 — dim_location

```
  OLE DB Source
  SELECT * FROM dbo.stg_covid_raw
         │
         ▼
  Conditional Split
  continent IS NULL OR continent = ''  → dq_rejected_rows (DQ-01)
  ELSE                                 → continue
         │
         ▼
  Sort
  Sort by: location ASC
  Enable: Remove rows with duplicate sort values
         │
         ▼
  Data Conversion
  population            string → DT_I8 (BIGINT)
  population_density    string → DT_R8 (FLOAT)
  median_age            string → DT_R8
  aged_65_older         string → DT_R8
  aged_70_older         string → DT_R8
  gdp_per_capita        string → DT_R8
  extreme_poverty       string → DT_R8
  handwashing_facilities string → DT_R8
  female_smokers        string → DT_R8
  male_smokers          string → DT_R8
  hospital_beds_per_thousand string → DT_R8
  life_expectancy       string → DT_R8
  diabetes_prevalence   string → DT_R8
  cardiovasc_death_rate string → DT_R8
  human_development_index string → DT_R8
         │
         ▼
  OLE DB Destination → dbo.dim_location
  Map _conv columns to target columns
```

---

## Data Flow 3 — fact_covid_daily

```
  OLE DB Source
  SELECT * FROM dbo.stg_covid_raw
         │
         ▼
  Derived Column
  record_year = (DT_I2)YEAR((DT_DBDATE)date)
         │
         ▼
  Conditional Split (DQ filters)
  continent IS NULL OR continent = ''   → dq_rejected_rows (DQ-01)
  ISNULL(date) OR date == ""            → dq_rejected_rows (DQ-02)
  location IS NULL OR location == ""    → dq_rejected_rows (DQ-04)
  ELSE                                  → continue
         │
         ▼
  Data Conversion
  date          string → DT_DBDATE
  All 52 numeric columns string → DT_R8 (FLOAT)
         │
         ▼
  Lookup — location_id
  Join: stg location = dim_location.country
  No match → dq_rejected_rows (DQ-05)
         │
         ▼
  Lookup — date_id
  Join: stg date = dim_date.date
  No match → dq_rejected_rows (DQ-06)
         │
         ▼
  OLE DB Destination → dbo.fact_covid_daily
```

---

## DQ Rules

| Code | Rule | Applied in | Action |
|------|------|-----------|--------|
| DQ-01 | continent IS NULL | Flow 2 + Flow 3 | Route to dq_rejected_rows — aggregate rows, expected |
| DQ-02 | date IS NULL | Flow 3 | Route to dq_rejected_rows |
| DQ-03 | date > today | Flow 3 | Route to dq_rejected_rows |
| DQ-04 | location IS NULL | Flow 3 | Route to dq_rejected_rows |
| DQ-05 | location not in dim_location | Flow 3 Lookup | Route to dq_rejected_rows |
| DQ-06 | date not in dim_date | Flow 3 Lookup | Route to dq_rejected_rows |

**Negative new_cases:** Not rejected. OWID historical corrections. Load as-is.

---

## SQL Server Table Definitions

### stg_covid_raw
All 67 source columns as VARCHAR(500) + load_timestamp.
Full DDL in `sql/01_create_staging.sql`.

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
    fact_id         INT      IDENTITY(1,1) PRIMARY KEY,
    record_year     SMALLINT NOT NULL,
    location_id     INT      NOT NULL,
    date_id         INT      NOT NULL,
    -- 52 FLOAT columns across cases/deaths/testing/vaccination/hospitalisation/policy
    -- Full DDL in sql/04_create_fact.sql
    load_timestamp  DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_location FOREIGN KEY (location_id)
        REFERENCES dbo.dim_location(location_id),
    CONSTRAINT fk_date FOREIGN KEY (date_id)
        REFERENCES dbo.dim_date(date_id),
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

### etl_validation
```sql
CREATE TABLE dbo.etl_validation (
    validation_id      INT           IDENTITY(1,1) PRIMARY KEY,
    run_id             VARCHAR(50),
    table_name         VARCHAR(100),
    test_layer         VARCHAR(20),   -- VOLUME / SCHEMA / ACCURACY / BUSINESS
    test_name          VARCHAR(200),
    source_count       BIGINT,
    destination_count  BIGINT,
    match_pct          DECIMAL(5,2),
    status             VARCHAR(10),   -- PASS / FAIL / WARN
    severity           VARCHAR(10),   -- CRITICAL / HIGH / LOW
    message            VARCHAR(500),
    executed_at        DATETIME DEFAULT GETDATE()
);
```

---

## Load Strategy

| Table | Mode | Notes |
|-------|------|-------|
| stg_covid_raw | Truncate + reload | Package 1 truncates before load |
| dim_date | Truncate + regenerate | Fresh every run — 2020-01-01 to today |
| dim_location | Truncate + reload | Deduplicated from staging |
| fact_covid_daily | Truncate + reload | Full reload — OWID corrections applied |

---

## Field Lineage — dim_location

| Source Column | Transform | Target Column |
|--------------|-----------|--------------|
| location | Pass-through | country |
| iso_code | Pass-through | code |
| continent | DQ-01 removes nulls | continent |
| population | string → BIGINT | population |
| population_density through human_development_index | string → FLOAT | same name |
| — | IDENTITY | location_id |

## Field Lineage — dim_date

| Source | Transform | Target |
|--------|-----------|--------|
| Script Task | Generated 2020-01-01 → today | date |
| Derived | YEAR(date) | year |
| Derived | MONTH(date) | month |
| Derived | dt.ToString("MMMM") | month_name |
| Derived | "Q" + quarter number | quarter |
| Derived | ISOWeek.GetWeekOfYear(dt) | week_number |
| Derived | dt.ToString("dddd") | day_of_week |
| Derived | Saturday or Sunday check | is_weekend |
| — | IDENTITY | date_id |
