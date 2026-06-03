# Business Requirements — COVID-19 Data Platform

## Purpose and Audience

**Project goal:** Build a data platform that serves two teams with one pipeline.
**End consumers:** Data analysts and data scientists.
**Design principle:** Clean, validated, structured data that answers known
questions and enables machine learning — without manual preparation work
every time someone needs to analyse something.

**Data compliance:** This platform processes country-level aggregate data
published by Our World in Data under Creative Commons BY 4.0.
No individual-level or personal data is stored at any stage.
GDPR does not apply — there are no data subjects, no PII,
and no processing of personal information.

---

## Business Problem

**Problem 1 — Reporting gap:**
Analysts have no clean, structured platform to answer questions about
COVID-19 trends. Raw CSV from OWID is not queryable by business users.
No warehouse = no reporting = decisions made without data.

**Problem 2 — Prediction gap:**
Data scientists have no feature-ready dataset to train ML models on.
Raw CSV has no lagged features, inconsistent date series, and mixed
types. Raw data is not ML-ready. No prediction = reactive response
instead of proactive outbreak management.

**Problem statement:**
> COVID-19 data exists but is not structured for either reporting or
> prediction — causing slow, uninformed decisions about outbreak response.

---

## Scope

| Attribute | Value |
|-----------|-------|
| Geographic scope | Global — all countries (195 after filtering aggregates) |
| Time period | 2020-01-01 to present |
| Granularity | Daily — country × day |
| Roll-ups | Weekly, monthly, quarterly — computed at query time |
| Slice by | Country, continent, date, month, quarter, year |

---

## Data Sources

| Source | Data | Format | Delivery |
|--------|------|--------|---------|
| ECDC / OWID | Cases, deaths, testing, hospitalisation, vaccination, policy | CSV | Manual download / scheduled |
| OWID enriched | Country demographics — population, GDP, median age, HDI | CSV (same file) | Same file |

---

## Functional Requirements

### FR-01 — Data Ingestion
- Load COVID-19 data from source CSV into SQL Server staging
- All columns loaded as VARCHAR first — no transformation at ingest stage
- Support full reload when source publishes corrections
- Capture load timestamp on every staging row

### FR-02 — Data Quality
- Filter aggregate rows (World, Asia, continents) — route to reject table
- Flag but retain negative new_cases — these are OWID historical corrections
- Validate row counts, column types, and value ranges after every load
- Capture all rejected rows with reason code and source values
- No row is ever silently dropped

### FR-03 — Reporting Layer (Data Analysts)
- Star schema optimised for Power BI queries
- Grain: one row = one country + one date
- Support all question categories below
- Time-based slicing: daily, weekly, monthly, quarterly
- Refresh on demand without schema changes

### FR-04 — ML Feature Layer (Data Scientists)
- Wide flat table — all features in one row, no JOINs required
- Consistent date series per country — no gaps
- Pre-computed lag features: 7-day, 14-day, 28-day
- Demographic attributes joined per country
- Clean numeric types throughout

### FR-05 — Audit and Traceability
- Every ETL run logged — start time, end time, rows loaded, status
- Every test result stored with run ID — full history preserved
- Failed steps can be re-run without restarting from scratch (restart_flag)
- Every rejected row traceable to its source and rejection reason

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| ETL completion time | < 10 minutes for full reload |
| Data freshness | Within 24 hours of source update |
| Re-runability | Safe to re-run without creating duplicates |
| Test coverage | All critical tests passing before data available to consumers |
| Reject tracking | Every rejected row captured with reason code |

---

## Reporting Requirements (Data Analysts)

### R1 — Descriptive: What happened?

| # | Business Question | Tables |
|---|-----------------|--------|
| D-01 | Which country had the most total deaths? | fact + dim_location |
| D-02 | What was the peak single-day new cases globally? | fact + dim_date |
| D-03 | Which continent had the highest total cases? | fact + dim_location |
| D-04 | How many countries reported data in this dataset? | dim_location |
| D-05 | What was the global total test count? | fact |
| D-06 | Which country had the highest single-day death count? | fact + dim_location |
| D-07 | What was the peak global vaccination rate per day? | fact + dim_date |

### R2 — Diagnostic: Why did it happen?

| # | Business Question | Tables |
|---|-----------------|--------|
| DG-01 | Did countries with more hospital beds have lower mortality? | fact + dim_location |
| DG-02 | Did higher GDP per capita correlate with lower death rates? | fact + dim_location |
| DG-03 | Did higher stringency index slow case growth? | fact + dim_location + dim_date |
| DG-04 | Did better handwashing facilities reduce transmission rates? | fact + dim_location |
| DG-05 | Did older median age populations have higher mortality? | fact + dim_location |
| DG-06 | Did higher diabetes prevalence correlate with higher death rates? | fact + dim_location |
| DG-07 | Did higher testing rates lead to earlier case detection? | fact + dim_location |

### R3 — Trend: How did it change over time?

| # | Business Question | Tables |
|---|-----------------|--------|
| T-01 | How did global new cases trend month by month through 2020–2024? | fact + dim_date |
| T-02 | When did vaccination rates start accelerating per continent? | fact + dim_location + dim_date |
| T-03 | Did reproduction rate drop after lockdowns were imposed? | fact + dim_date |
| T-04 | How did stringency index change for the top 5 affected countries? | fact + dim_location + dim_date |
| T-05 | Did total deaths flatten after vaccines rolled out? | fact + dim_date |
| T-06 | Which months had the highest new deaths globally? | fact + dim_date |

### R4 — Comparative: How do groups differ?

| # | Business Question | Tables |
|---|-----------------|--------|
| C-01 | High income vs low income countries — mortality rate difference? | fact + dim_location |
| C-02 | Europe vs Asia — positivity rate over time? | fact + dim_location + dim_date |
| C-03 | Which 10 countries had the highest deaths per million? | fact + dim_location |
| C-04 | Which 10 countries had the lowest mortality despite high cases? | fact + dim_location |
| C-05 | How did vaccination rollout speed differ between continents? | fact + dim_location + dim_date |
| C-06 | Countries with stringency > 70 vs < 30 — case growth comparison? | fact + dim_location |

### R5 — Correlation: What relates to what?

| # | Business Question | Tables |
|---|-----------------|--------|
| CR-01 | Does median age correlate with mortality rate? | fact + dim_location |
| CR-02 | Does extreme poverty correlate with deaths per million? | fact + dim_location |
| CR-03 | Does handwashing access correlate with transmission rate? | fact + dim_location |
| CR-04 | Does GDP per capita correlate with total tests per thousand? | fact + dim_location |
| CR-05 | Does cardiovascular death rate correlate with COVID mortality? | fact + dim_location |
| CR-06 | Does human development index correlate with vaccination rate? | fact + dim_location |

### R6 — Anomaly: What doesn't fit the pattern?

| # | Business Question | Tables |
|---|-----------------|--------|
| A-01 | Which countries had high cases but unusually low deaths? | fact + dim_location |
| A-02 | Which countries had death spikes with no corresponding case spike? | fact + dim_location + dim_date |
| A-03 | Any countries with positive rate above 50% sustained for 30+ days? | fact + dim_location + dim_date |
| A-04 | Are there dates where new_cases is negative? Which countries? | fact + dim_location |
| A-05 | Which countries had zero tests reported for entire months? | fact + dim_location + dim_date |
| A-06 | Are there countries where total_deaths > total_cases (data error)? | fact |

---

## Prediction Requirements (Data Scientists)

| # | Prediction Question | Feature columns needed |
|---|-------------------|----------------------|
| P-01 | Given last 14 days of cases — predict new_cases for next 7 days | new_cases_lag_7/14/28, rolling_avg |
| P-02 | Which country is most likely to see a surge in next 30 days? | reproduction_rate, stringency_index, lags |
| P-03 | Given vaccination rate + stringency — predict reproduction_rate | people_vaccinated_per_hundred, stringency_index |
| P-04 | What demographic factors most predict high mortality rate? | median_age, gdp_per_capita, hospital_beds, diabetes |
| P-05 | Given ICU occupancy — predict peak ICU load in 14 days | icu_patients, hosp_patients, new_cases_lag |
| P-06 | Which countries have similar outbreak trajectories? (clustering) | all case/death metrics |
| P-07 | At what vaccination % did new_deaths_smoothed begin declining? | people_vaccinated_per_hundred, new_deaths_smoothed |
| P-08 | Did lockdown timing measurably reduce deaths? (causal inference) | stringency_index, new_deaths, dates |

---

## Report-to-Table Traceability

| Report | Tables Required | Key columns | ETL decision |
|--------|---------------|-------------|-------------|
| R1 Descriptive | fact + dim_location + dim_date | total_cases, total_deaths, new_cases | Cumulative columns are OWID pass-through |
| R2 Diagnostic | fact + dim_location | hospital_beds, gdp_per_capita, stringency_index | Demographics in dim_location — joined at query time |
| R3 Trend | fact + dim_date | new_cases_smoothed, reproduction_rate, stringency_index | Smoothed columns are OWID pre-computed — pass-through |
| R4 Comparative | fact + dim_location + dim_date | new_cases_per_million, total_deaths_per_million | Per-million columns are OWID pre-computed — pass-through |
| R5 Correlation | fact + dim_location | median_age, extreme_poverty, cardiovasc_death_rate | All demographic cols from dim_location — never in fact |
| R6 Anomaly | fact + dim_location + dim_date | new_cases, positive_rate, total_deaths | Negative new_cases loaded as-is — OWID corrections |
| P predictions | ml_covid_features | all columns + lag features | Lag features computed during ETL — not in raw source |

---

## Out of Scope

- Age-stratified case / death data — not in OWID source file
- Individual-level patient data — not in scope, GDPR would apply
- Real-time streaming — batch load only
- Vaccination adverse events — not in source data
- WHO region groupings — using geographic continents from source
