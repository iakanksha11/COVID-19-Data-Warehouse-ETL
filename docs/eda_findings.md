# EDA Findings — owid-covid-data.csv

**Run date:** June 2026
**Dataset:** Our World in Data — COVID-19 Complete Dataset
**File:** owid-covid-data.csv

---

## File Profile

| Attribute | Value |
|-----------|-------|
| Rows | 429,435 |
| Columns | 67 |
| File size | 93.83 MB |
| Date range | 2020-01-01 → 2024-08-14 |
| Unique locations | 255 |
| True countries | ~195 (remainder are continents + income groups) |

> **Important:** 255 locations includes aggregate rows — World, Asia, Africa, High income, etc.
> These have `continent IS NULL` and must be filtered out in SSIS before loading dimensions and facts.
> Estimated ~26,600 rows to be routed to `dq_rejected_rows` with reason code DQ-01.

---

## Key Discovery — 67 Columns, Not 40

The original project design assumed 40 columns (ECDC extract).
The full OWID dataset has 67 columns across five domains.
Schema design must account for all domains.

---

## Column Inventory — All 67 Columns

### Identity (4 columns — 0% null — ✅ clean)

| Column | Type | Notes |
|--------|------|-------|
| iso_code | object | 255 unique — includes OWID_ prefixed aggregate codes |
| continent | object | 6.2% null — NULL = aggregate row (World, Asia, etc.) |
| location | object | 255 unique — country name or aggregate label |
| date | datetime64 | 1,688 unique dates — 2020-01-01 to 2024-08-14 |

### COVID Cases (6 columns — ~4-5% null — 🟡 low)

| Column | Null % | Min | Max | Notes |
|--------|--------|-----|-----|-------|
| total_cases | 4.1% | 0 | 775,866,783 | Cumulative |
| new_cases | 4.5% | 0 | 44,236,227 | Daily — can be negative (OWID corrections) |
| new_cases_smoothed | 4.8% | 0 | 6,319,461 | 7-day avg — OWID pre-computed |
| total_cases_per_million | 4.1% | 0 | 763,598.6 | OWID pre-computed |
| new_cases_per_million | 4.5% | 0 | 241,758.23 | OWID pre-computed |
| new_cases_smoothed_per_million | 4.8% | 0 | 34,536.89 | OWID pre-computed |

### COVID Deaths (6 columns — ~4-5% null — 🟡 low)

| Column | Null % | Min | Max | Notes |
|--------|--------|-----|-----|-------|
| total_deaths | 4.1% | 0 | 7,057,132 | Cumulative |
| new_deaths | 4.4% | 0 | 103,719 | Daily — can be negative (corrections) |
| new_deaths_smoothed | 4.7% | 0 | 14,817 | 7-day avg — OWID pre-computed |
| total_deaths_per_million | 4.1% | 0 | 6,601.11 | OWID pre-computed |
| new_deaths_per_million | 4.4% | 0 | 893.66 | OWID pre-computed |
| new_deaths_smoothed_per_million | 4.7% | 0 | 127.66 | OWID pre-computed |

### Transmission (1 column — 57% null — 🟠 medium)

| Column | Null % | Min | Max | Notes |
|--------|--------|-----|-----|-------|
| reproduction_rate | 57.0% | -0.07 | 5.87 | **Anomaly: min = -0.07 (should be > 0)** |

### Hospitalisation (6 columns — 90-97% null — 🔴 high)

| Column | Null % | Notes |
|--------|--------|-------|
| icu_patients | 90.9% | Sparse — only ~40 countries report |
| icu_patients_per_million | 90.9% | OWID pre-computed |
| hosp_patients | 90.5% | Sparse — only ~40 countries report |
| hosp_patients_per_million | 90.5% | OWID pre-computed |
| weekly_icu_admissions | 97.4% | Very sparse — ~15 countries |
| weekly_hosp_admissions | 94.3% | Sparse |
| weekly_icu_admissions_per_million | 97.4% | OWID pre-computed |
| weekly_hosp_admissions_per_million | 94.3% | OWID pre-computed |

### Testing (7 columns — 75-82% null — 🔴 high)

| Column | Null % | Notes |
|--------|--------|-------|
| total_tests | 81.5% | Sparse — testing data gaps in 2020 |
| new_tests | 82.4% | Sparse |
| total_tests_per_thousand | 81.5% | OWID pre-computed |
| new_tests_per_thousand | 82.4% | OWID pre-computed |
| new_tests_smoothed | 75.8% | 7-day avg |
| new_tests_smoothed_per_thousand | 75.8% | OWID pre-computed |
| positive_rate | 77.7% | Range: 0.0–1.0 ✅ no violations |
| tests_per_case | 78.0% | Max: 1,023,631.9 — outliers exist |
| tests_units | 75.1% | 4 unique values: tests performed / samples tested / units unclear |

### Vaccinations (13 columns — 54-87% null — 🔴 high)

| Column | Null % | Notes |
|--------|--------|-------|
| total_vaccinations | 80.1% | Data starts ~Dec 2020 |
| people_vaccinated | 81.1% | |
| people_fully_vaccinated | 81.8% | |
| total_boosters | 87.5% | Data starts ~late 2021 |
| new_vaccinations | 83.5% | |
| new_vaccinations_smoothed | 54.6% | 7-day avg |
| total_vaccinations_per_hundred | 80.1% | |
| people_vaccinated_per_hundred | 81.1% | |
| people_fully_vaccinated_per_hundred | 81.8% | |
| total_boosters_per_hundred | 87.5% | |
| new_vaccinations_smoothed_per_million | 54.6% | |
| new_people_vaccinated_smoothed | 55.2% | |
| new_people_vaccinated_smoothed_per_hundred | 55.2% | |

### Policy (1 column — 54% null — 🟠 medium)

| Column | Null % | Min | Max | Notes |
|--------|--------|-----|-----|-------|
| stringency_index | 54.3% | 0.0 | 100.0 | ✅ within valid range |

### Demographics — Static per Country (10 columns — dim_location)

| Column | Null % | Flag | Notes |
|--------|--------|------|-------|
| population | 0.0% | ✅ clean | int64 — load as BIGINT |
| population_density | 16.1% | 🟡 low | |
| median_age | 22.1% | 🟠 medium | |
| aged_65_older | 24.7% | 🟠 medium | % of population |
| aged_70_older | 22.8% | 🟠 medium | % of population |
| gdp_per_capita | 23.6% | 🟠 medium | USD |
| extreme_poverty | 50.6% | 🟠 medium | % below poverty line |
| cardiovasc_death_rate | 23.4% | 🟠 medium | |
| diabetes_prevalence | 19.4% | 🟡 low | |
| female_smokers | 42.4% | 🟠 medium | |
| male_smokers | 43.2% | 🟠 medium | |
| handwashing_facilities | 62.3% | 🔴 high | Sparse |
| hospital_beds_per_thousand | 32.3% | 🟠 medium | |
| life_expectancy | 9.1% | 🟡 low | |
| human_development_index | 25.7% | 🟠 medium | New — not in original design |

### Excess Mortality (4 columns — 96.9% null — 🔴 high)

| Column | Null % | Notes |
|--------|--------|-------|
| excess_mortality_cumulative_absolute | 96.9% | Very sparse — ~15 countries |
| excess_mortality_cumulative | 96.9% | Min: -44.23 (negative = fewer deaths than expected) |
| excess_mortality | 96.9% | |
| excess_mortality_cumulative_per_million | 96.9% | |

---

## Data Quality Findings

### ✅ No Issues
- `location`, `iso_code`, `date`, `population` — 0% null, no anomalies
- `positive_rate` — stays within 0.0–1.0 range
- `stringency_index` — stays within 0.0–100.0 range

### ⚠️ Warnings (load with caution)
- `new_cases` and `new_deaths` — can be negative. These are OWID historical corrections.
  Decision: **load as-is, flag in post-load verification. Do NOT reject.**
- `reproduction_rate` — min = -0.07. Theoretically impossible but rare.
  Decision: **load as-is, flag in business rule test.**
- `tests_per_case` — max = 1,023,631.9. Extreme outlier.
  Decision: **load as-is, document as known data quality issue.**
- `continent` — 6.2% null. These are aggregate rows, not missing data.
  Decision: **route to dq_rejected_rows with DQ-01. Expected, not an error.**

### ❌ Columns to exclude from load
None in this dataset. Unlike the old CSV, there are no Tableau artifact columns
(`Number of Records`, `Waterfall`). All 67 columns are real OWID data.

---

## Static vs Dynamic Classification

### dim_location — 15 columns (one row per country, loaded once)
population, population_density, median_age, aged_65_older, aged_70_older,
gdp_per_capita, extreme_poverty, cardiovasc_death_rate, diabetes_prevalence,
female_smokers, male_smokers, handwashing_facilities, hospital_beds_per_thousand,
life_expectancy, human_development_index

### fact_covid_daily — 52 columns (one row per country per date)
All remaining columns — cases, deaths, testing, vaccination, hospitalisation,
transmission, policy, excess mortality

---

## Schema Impact — Changes from Original Design

| Item | Original design | Actual (67 cols) |
|------|----------------|-----------------|
| Total columns | 40 | 67 |
| Fact columns | ~20 | ~52 |
| Dim columns | ~18 | 15 |
| Vaccination data | Not in design | 13 new columns |
| Hospitalisation | Partial | 8 columns, 90-97% null |
| Excess mortality | Not in design | 4 new columns, 97% null |
| human_development_index | Not in design | 1 new column |
| Artifact columns to drop | 2 (Waterfall, No. of Records) | 0 |

**Decision:** Single fact table `fact_covid_daily` absorbs all 52 daily columns.
Vaccination and hospitalisation are too sparse for separate fact tables at this scale.
If vaccination analysis becomes the focus, extract to `fact_vaccination` later.

---

## Duplicate Check

**To verify:** run after staging load:
```sql
SELECT location, date, COUNT(*) AS cnt
FROM stg_covid_raw
GROUP BY location, date
HAVING COUNT(*) > 1;
```
Expected: 0 duplicates (OWID guarantees one row per location per date).

---

## Phase 1 Sign-off

| Check | Result |
|-------|--------|
| Row count profiled | ✅ 429,435 rows |
| Column count confirmed | ✅ 67 columns |
| Date range confirmed | ✅ 2020-01-01 → 2024-08-14 |
| Unique locations confirmed | ✅ 255 (incl. aggregates) |
| Null % per column | ✅ Documented above |
| Data type audit | ✅ All numeric as float64, population as int64 |
| Anomalies identified | ✅ Negative cases/deaths, negative reproduction_rate |
| Static vs dynamic split | ✅ 15 dim columns, 52 fact columns |
| Columns to drop | ✅ None |
| DQ-01 filter confirmed | ✅ continent IS NULL = aggregate rows |
| Schema updated for 67 cols | ✅ Documented above |
