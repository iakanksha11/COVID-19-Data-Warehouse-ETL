# COVID-19 Data Warehouse Project

**Owner:** Ak
**Dataset:** ECDC / Our World in Data — COVID-19 Worldwide
**Staging:** SQL Server
**Warehouse:** Snowflake
**ETL:** SSIS (Visual Studio)
**Reporting:** Power BI, SSRS

---

## Business Problem

> "I am a **WHO health policy advisor**.
> The business problem I am trying to solve is:
> **which country-level factors (economic, demographic, healthcare capacity) most strongly
> correlate with COVID-19 mortality outcomes?**
> I will know I succeeded when I can answer:
> which countries were highest risk, why, and what early indicators predicted poor outcomes
> — directly from the warehouse."

---

## End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  CSV (OWID)  →  SSIS  →  SQL Server  →  Snowflake  →  Power BI    │
│                                                    →  SSRS          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Stage by Stage

```
Stage 1          Stage 2          Stage 3          Stage 4
CSV File    →    SSIS         →   SQL Server   →   Snowflake
(source)         (ETL tool)       (staging DB)     (warehouse)
                 Visual Studio    raw tables        dim + fact tables
                 data flows       minimal           star schema
                 transformations  transformation    optimised for query
                                  just load it      Power BI connects here
```

---

## Tool Stack

| Tool | Purpose | Where in pipeline |
|------|---------|-------------------|
| CSV files (OWID) | Source raw data | Stage 1 |
| SSIS (Visual Studio) | ETL — extract, transform, load | Stage 2 |
| SQL Server | Staging database — raw copy of CSV | Stage 3 |
| SSMS | Write + manage SQL (staging + validation) | Stage 3 |
| Snowflake | Production warehouse — star schema | Stage 4 |
| Power BI | Interactive dashboards + visual reporting | Stage 5 |
| SSRS | Paginated / scheduled reports | Stage 5 |

---

## What Each Tool Does

### CSV files (OWID)
Raw source data. 40 columns. One row per country per date.
Downloaded from Our World in Data (ECDC enriched dataset).
This is the starting point — untouched, unmodified.

### SSIS (SQL Server Integration Services)
Visual ETL tool inside Visual Studio.
Drag-and-drop pipeline builder — no code needed for basic flows.

What SSIS does in this project:
- Reads the CSV flat file
- Maps columns to SQL Server staging table
- Handles data type conversions
- Handles null values and error rows
- Loads data into SQL Server staging

SSIS concepts you need to know:
- **Control Flow** — the overall pipeline logic (sequence, conditions, loops)
- **Data Flow Task** — the actual data movement (source → transform → destination)
- **Flat File Source** — reads the CSV
- **OLE DB Destination** — writes to SQL Server
- **Derived Column** — adds/modifies columns during load
- **Conditional Split** — routes bad rows to error output

### SQL Server (Staging)
Receives raw data from SSIS. Minimal transformation.
Goal: get the CSV into a queryable database as fast as possible.
Then use SQL to profile, clean, and validate before pushing to Snowflake.

Staging tables in SQL Server:
- `stg_covid_raw` — exact copy of CSV, all columns as VARCHAR first
- `stg_covid_typed` — re-typed after validation (dates as DATE, numbers as FLOAT)

### SSMS (SQL Server Management Studio)
IDE for writing and running SQL against SQL Server.
Used for:
- Profiling staging data (EDA queries)
- Writing validation checks
- Writing transformation SQL
- Debugging SSIS loads

### SQL Server → Snowflake
After staging is clean and validated in SQL Server,
push the data to Snowflake for the production warehouse.

Options for this move:
- **Snowflake ODBC connector** — query SQL Server directly from Snowflake
- **Export to CSV → PUT → COPY INTO** — dump from SQL Server, load to Snowflake
- **SSIS Snowflake connector** — extend the SSIS pipeline to write to Snowflake directly

Recommended: export clean staging tables to CSV → PUT to Snowflake stage → COPY INTO.

### Snowflake (Warehouse)
Production analytical warehouse. Star schema lives here.
This is where the business questions get answered.

Objects created in Snowflake:
- `dim_country` — one row per country, all static attributes
- `dim_date` — one row per date, date hierarchy
- `fact_covid_daily` — one row per country per date, all measures

### Power BI
Connects directly to Snowflake.
Builds interactive dashboards for business users.
Drags dim_country and dim_date as slicers/filters.
Plots fact measures (cases, deaths, positivity rate).

### SSRS (SQL Server Reporting Services)
Paginated, scheduled, printable reports.
Used when you need: weekly summary emails, PDF reports, fixed-format outputs.
Complements Power BI (Power BI = explore, SSRS = distribute).

---

## Dataset

| Attribute | Value |
|-----------|-------|
| Source | Our World in Data (ECDC enriched) |
| File | covid_ecdc.csv |
| Format | CSV, comma-delimited |
| Columns | 40 |
| Granularity | One row = one country on one date |

### Column Categories

**Geography**
`location`, `continent`, `iso_code`

**Time**
`date`

**COVID Case Metrics** *(fact table)*
`new_cases`, `new_cases_per_million`, `total_cases`, `total_cases_per_million`

**COVID Death Metrics** *(fact table)*
`new_deaths`, `new_deaths_per_million`, `total_deaths`, `total_deaths_per_million`,
`Deathp100K`, `Mortality Rate`

**Testing Metrics** *(fact table)*
`new_tests`, `new_tests_per_thousand`, `new_tests_smoothed`,
`new_tests_smoothed_per_thousand`, `total_tests`, `total_tests_per_thousand`,
`tests_units`, `positive_rate`, `tests_per_case`

**Healthcare / Health Indicators** *(dim_country)*
`hospital_beds_per_thousand`, `cardiovasc_death_rate`,
`life_expectancy`, `diabetes_prevalence`

**Demographics** *(dim_country)*
`population`, `population_density`, `median_age`, `aged_65_older`, `aged_70_older`

**Economic / Social** *(dim_country)*
`gdp_per_capita`, `extreme_poverty`, `handwashing_facilities`,
`female_smokers`, `male_smokers`

**Policy** *(fact table — changes daily)*
`stringency_index`

**Drop — BI tool artifacts**
`Number of Records`, `Waterfall`

---

## Warehouse Design (Snowflake — Star Schema)

```
              dim_date
                 │
dim_country ─── FACT_COVID_DAILY
```

### fact_covid_daily
| Column | Type | Notes |
|--------|------|-------|
| date_key | INT | FK → dim_date |
| country_key | INT | FK → dim_country |
| new_cases | FLOAT | |
| new_deaths | FLOAT | |
| new_tests | FLOAT | |
| total_cases | FLOAT | |
| total_deaths | FLOAT | |
| total_tests | FLOAT | |
| positive_rate | FLOAT | 0.0 to 1.0 |
| stringency_index | FLOAT | 0 to 100 |
| new_cases_per_million | FLOAT | |
| new_deaths_per_million | FLOAT | |
| mortality_rate | FLOAT | derived |
| deaths_per_100k | FLOAT | derived |

### dim_country
| Column | Type | Notes |
|--------|------|-------|
| country_key | INT | PK |
| location | VARCHAR | |
| continent | VARCHAR | |
| iso_code | VARCHAR | |
| population | FLOAT | |
| population_density | FLOAT | |
| median_age | FLOAT | |
| aged_65_older | FLOAT | |
| aged_70_older | FLOAT | |
| gdp_per_capita | FLOAT | |
| extreme_poverty | FLOAT | |
| handwashing_facilities | FLOAT | |
| female_smokers | FLOAT | |
| male_smokers | FLOAT | |
| hospital_beds_per_thousand | FLOAT | |
| life_expectancy | FLOAT | |
| diabetes_prevalence | FLOAT | |
| cardiovasc_death_rate | FLOAT | |

### dim_date
| Column | Type | Notes |
|--------|------|-------|
| date_key | INT | PK |
| full_date | DATE | |
| year | INT | |
| month | INT | |
| quarter | INT | |
| week_number | INT | |
| day_of_week | INT | |
| month_name | VARCHAR | |
| is_weekend | BOOLEAN | |

---

## Project Phases

### Phase 1 — EDA on Raw Data
**Tool:** Python + Pandas, SSMS
**Goal:** Understand data before touching it

Steps:
- [ ] Run profiling script (row count, nulls, date range, unique countries)
- [ ] Group all 40 columns into categories
- [ ] Identify artifact columns to drop (Waterfall, Number of Records)
- [ ] Check granularity — one row = one country + one date?
- [ ] Check for duplicates (same country + same date)
- [ ] Identify static vs daily-changing columns
- [ ] Document data quality issues found

**Deliverable:** data quality report + column inventory

---

### Phase 2 — Generate Business Questions (30-50+)
**Tool:** Brain + paper
**Goal:** Define what the warehouse must answer

Categories:
- Descriptive — "What happened?"
- Diagnostic — "Why did it happen?"
- Trend / Pattern — "How did it change over time?"
- Comparative — "How do countries/regions differ?"
- Correlation — "What factors relate to mortality?"
- Anomaly — "What doesn't fit the pattern?"

**Rule:** if a question can't be answered from your warehouse design → redesign.
**Deliverable:** questions.md with 30-50+ documented questions

---

### Phase 3 — Design Warehouse
**Tool:** SSMS (draw on paper first)
**Goal:** Star schema that answers every Phase 2 question

Steps:
- [ ] Define grain (one row = one country + one date)
- [ ] Identify fact columns (daily changing, measurable)
- [ ] Identify dimension columns (static descriptors)
- [ ] Draw star schema diagram
- [ ] Map each Phase 2 question to a query path
- [ ] Validate: every question answerable? If not → redesign
- [ ] Write CREATE TABLE DDL for SQL Server staging tables
- [ ] Write CREATE TABLE DDL for Snowflake dim + fact tables

**Deliverable:** schema diagram + DDL scripts

---

### Phase 4 — SSIS ETL Pipeline
**Tool:** SSIS (Visual Studio)
**Goal:** Load CSV into SQL Server staging

Steps:
- [ ] Install SQL Server Developer Edition (free)
- [ ] Install Visual Studio + SSIS extension
- [ ] Create new SSIS project
- [ ] Create Flat File Connection Manager (point to CSV)
- [ ] Create OLE DB Connection Manager (point to SQL Server)
- [ ] Create Data Flow Task:
  - Flat File Source → reads CSV
  - Data Conversion → fix data types
  - Derived Column → handle nulls, add load date
  - OLE DB Destination → write to stg_covid_raw
- [ ] Run package — verify row count matches CSV
- [ ] Add error output handling for rejected rows
- [ ] Document load metrics (rows loaded, rejected, time)

**Deliverable:** working SSIS package (.dtsx file)

---

### Phase 5 — SQL Server Validation (Staging)
**Tool:** SSMS
**Goal:** Validate staging before pushing to Snowflake

SQL checks to write:
- [ ] Row count = CSV row count
- [ ] No null primary key fields (location + date)
- [ ] No duplicate location + date combinations
- [ ] Date column format is valid
- [ ] No negative new_cases or new_deaths
- [ ] positive_rate between 0 and 1
- [ ] stringency_index between 0 and 100
- [ ] All continents are valid (not NULL or unknown)

**Deliverable:** validation SQL script + pass/fail results

---

### Phase 6 — Load SQL Server → Snowflake
**Tool:** Snowflake + SSMS
**Goal:** Move clean staged data into Snowflake warehouse

Steps:
- [ ] Export stg_covid_typed from SQL Server to CSV
- [ ] Create Snowflake database, schema, warehouse
- [ ] Create stage + file format in Snowflake
- [ ] PUT exported CSV to Snowflake stage
- [ ] COPY INTO Snowflake staging table
- [ ] INSERT...SELECT to build dim_country
- [ ] INSERT...SELECT to build dim_date
- [ ] INSERT...SELECT to build fact_covid_daily
- [ ] Verify row counts match SQL Server staging

**Deliverable:** populated Snowflake warehouse

---

### Phase 7 — Snowflake Validation
**Tool:** SSMS / Snowflake UI
**Goal:** Confirm warehouse matches source and answers questions

Checks:
- [ ] fact_covid_daily row count = SQL Server staging count
- [ ] All dim_country keys exist in fact table (referential integrity)
- [ ] All dim_date keys exist in fact table
- [ ] No nulls in fact table keys
- [ ] Aggregated totals match source (SUM new_cases = known totals)
- [ ] Each Phase 2 question returns a valid result (not empty/error)

**Deliverable:** test report (pass/fail per check)

---

### Phase 8 — Reporting
**Tool:** Power BI + SSRS
**Goal:** Answer every Phase 2 business question visually

Power BI:
- [ ] Connect Power BI to Snowflake
- [ ] Import dim_country, dim_date, fact_covid_daily
- [ ] Build relationships (star schema auto-detected)
- [ ] Create visuals for each question category
- [ ] Add slicers: continent, country, date range
- [ ] Publish dashboard

SSRS:
- [ ] Connect SSRS to Snowflake
- [ ] Create paginated report — weekly country summary
- [ ] Create PDF export for management reporting

**Deliverable:** Power BI dashboard + SSRS report

---

## Folder Structure

```
covid-dwh/
│
├── raw_data/
│   └── covid_ecdc.csv
│
├── ssis/
│   └── covid_etl.dtsx              SSIS package
│
├── sql/
│   ├── sqlserver/
│   │   ├── 01_create_staging.sql   Create staging tables in SQL Server
│   │   ├── 02_validate_staging.sql Validation checks in SQL Server
│   │   └── 03_export_clean.sql     Export clean data
│   │
│   └── snowflake/
│       ├── 01_setup.sql            Database, schema, warehouse, stage
│       ├── 02_create_dims.sql      dim_country, dim_date DDL
│       ├── 03_create_facts.sql     fact_covid_daily DDL
│       ├── 04_load_dims.sql        INSERT into dimensions
│       ├── 05_load_facts.sql       INSERT into fact table
│       ├── 06_validate.sql         All validation checks
│       └── 07_questions.sql        SQL for every Phase 2 question
│
├── src/
│   ├── profiler.py                 EDA on raw CSV (Phase 1)
│   └── reporter.py                 Generate HTML test report
│
├── powerbi/
│   └── covid_dashboard.pbix        Power BI file
│
├── ssrs/
│   └── weekly_summary.rdl          SSRS report definition
│
├── docs/
│   ├── planning.md                 Task tracker
│   ├── questions.md                Phase 2 question list
│   └── schema.md                   Warehouse schema docs
│
├── reports/                        Generated reports (gitignored)
├── .env.example                    Credentials template
└── README.md
```

---

## Decision Log

| Decision | Choice | Reason |
|----------|--------|--------|
| ETL tool | SSIS | Manager requirement, enterprise standard |
| Staging DB | SQL Server | Pairs with SSIS natively |
| Warehouse | Snowflake | Cloud-native analytics, existing expertise |
| Reporting | Power BI + SSRS | Power BI = interactive, SSRS = scheduled/paginated |
| Schema | Star schema | Simple queries, fast, BI tool compatible |
| Model | Kimball dimensional | Analytics-first, business-question-driven |
| EDA timing | Before ETL | Understand quality issues before building pipeline |

---

## Progress

| Phase | Status |
|-------|--------|
| 1 — EDA on raw data | 🔄 In Progress |
| 2 — Generate questions | ⬜ Not Started |
| 3 — Design warehouse | ⬜ Not Started |
| 4 — SSIS ETL pipeline | ⬜ Not Started |
| 5 — SQL Server validation | ⬜ Not Started |
| 6 — Load to Snowflake | ⬜ Not Started |
| 7 — Snowflake validation | ⬜ Not Started |
| 8 — Power BI + SSRS reporting | ⬜ Not Started |
