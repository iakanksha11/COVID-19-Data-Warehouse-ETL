# Business Requirements — COVID-19 Data Platform

## Business Problem

> COVID-19 data exists but is not structured for reporting —
> causing slow, uninformed decisions about outbreak response.

Analysts have no clean structured platform to answer questions
about COVID-19 trends. Raw CSV from OWID is not queryable.
No warehouse = no reporting = decisions made without data.

---

## Scope

| Attribute | Value |
|-----------|-------|
| Geographic scope | Global — ~195 countries after filtering aggregates |
| Time period | 2020-01-01 → 2024-08-14 |
| Granularity | Daily — country × day |
| Roll-ups | Weekly, monthly, quarterly — computed at query time |
| Source | Our World in Data (OWID) — owid-covid-data.csv |

---

## Functional Requirements

**FR-01 — Data Ingestion**
Load CSV into SQL Server staging. All 67 columns as VARCHAR.
Support full reload when OWID publishes corrections.

**FR-02 — Data Quality**
Filter aggregate rows (continent IS NULL) — route to dq_rejected_rows.
Flag but retain negative new_cases — OWID historical corrections.
Validate after every load. No row silently dropped.

**FR-03 — Reporting Layer**
Star schema optimised for SQL queries and BI tools.
Support slicing by country, continent, date, month, quarter.
Answer 38 business questions across 6 categories.

**FR-04 — Audit**
Every rejected row captured with reason code and source values.
Post-load verification runs after every ETL execution.

---

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| ETL completion | < 10 minutes for full reload |
| Re-runability | Safe to re-run — truncate before every load |
| Reject tracking | Every rejected row in dq_rejected_rows with reason code |
| Test coverage | All critical checks pass before reporting connects |

---

## Business Questions

### Descriptive — What happened?

| # | Question | Tables |
|---|----------|--------|
| D-01 | Which country had the most total deaths? | fact + dim_location |
| D-02 | What was the peak single-day new cases globally? | fact + dim_date |
| D-03 | Which continent had the highest total cases? | fact + dim_location |
| D-04 | How many countries reported data? | dim_location |
| D-05 | What was the global total test count? | fact |
| D-06 | Which country had the highest single-day death count? | fact + dim_location |
| D-07 | What was the peak global vaccination rate per day? | fact + dim_date |

### Diagnostic — Why did it happen?

| # | Question | Tables |
|---|----------|--------|
| DG-01 | Did countries with more hospital beds have lower mortality? | fact + dim_location |
| DG-02 | Did higher GDP correlate with lower death rates? | fact + dim_location |
| DG-03 | Did higher stringency index slow case growth? | fact + dim_location + dim_date |
| DG-04 | Did better handwashing reduce transmission? | fact + dim_location |
| DG-05 | Did older median age populations have higher mortality? | fact + dim_location |
| DG-06 | Did higher diabetes prevalence correlate with higher deaths? | fact + dim_location |
| DG-07 | Did higher testing rates lead to earlier detection? | fact + dim_location |

### Trend — How did it change?

| # | Question | Tables |
|---|----------|--------|
| T-01 | How did global new cases trend month by month 2020–2024? | fact + dim_date |
| T-02 | When did vaccination rates accelerate per continent? | fact + dim_location + dim_date |
| T-03 | Did reproduction rate drop after lockdowns? | fact + dim_date |
| T-04 | How did stringency change for top 5 affected countries? | fact + dim_location + dim_date |
| T-05 | Did total deaths flatten after vaccines rolled out? | fact + dim_date |
| T-06 | Which months had the highest new deaths globally? | fact + dim_date |

### Comparative — How do groups differ?

| # | Question | Tables |
|---|----------|--------|
| C-01 | High income vs low income countries — mortality difference? | fact + dim_location |
| C-02 | Europe vs Asia — positivity rate over time? | fact + dim_location + dim_date |
| C-03 | Top 10 countries by deaths per million? | fact + dim_location |
| C-04 | Top 10 countries with lowest mortality despite high cases? | fact + dim_location |
| C-05 | How did vaccination rollout differ between continents? | fact + dim_location + dim_date |
| C-06 | Stringency > 70 vs < 30 — case growth comparison? | fact + dim_location |

### Correlation — What relates to what?

| # | Question | Tables |
|---|----------|--------|
| CR-01 | Does median age correlate with mortality rate? | fact + dim_location |
| CR-02 | Does extreme poverty correlate with deaths per million? | fact + dim_location |
| CR-03 | Does handwashing access correlate with transmission? | fact + dim_location |
| CR-04 | Does GDP correlate with total tests per thousand? | fact + dim_location |
| CR-05 | Does cardiovascular death rate correlate with COVID mortality? | fact + dim_location |
| CR-06 | Does HDI correlate with vaccination rate? | fact + dim_location |

### Anomaly — What doesn't fit?

| # | Question | Tables |
|---|----------|--------|
| A-01 | Which countries had high cases but unusually low deaths? | fact + dim_location |
| A-02 | Which countries had death spikes with no case spike? | fact + dim_location + dim_date |
| A-03 | Any countries with positive rate > 50% for 30+ days? | fact + dim_location + dim_date |
| A-04 | Dates where new_cases is negative — which countries? | fact + dim_location |
| A-05 | Countries with zero tests for entire months? | fact + dim_location + dim_date |
| A-06 | Countries where total_deaths > total_cases (data error)? | fact |

---

## Report-to-Table Traceability

| Category | Tables | Key columns | ETL note |
|----------|--------|-------------|---------|
| Descriptive | fact + dim_location + dim_date | total_cases, total_deaths, new_cases | Cumulative cols are OWID pass-through |
| Diagnostic | fact + dim_location | hospital_beds, gdp_per_capita, stringency_index | Demographics in dim_location |
| Trend | fact + dim_date | new_cases_smoothed, reproduction_rate | Smoothed cols are OWID pre-computed |
| Comparative | fact + dim_location + dim_date | new_cases_per_million, total_deaths_per_million | Per-million cols are OWID pre-computed |
| Correlation | fact + dim_location | median_age, extreme_poverty, cardiovasc_death_rate | All demographic cols from dim_location |
| Anomaly | fact + dim_location + dim_date | new_cases, positive_rate, total_deaths | Negative new_cases loaded as-is |

---

## Out of Scope

- Age-stratified case / death data
- Individual-level patient data
- Real-time streaming
- ML prediction models
- WHO region groupings
