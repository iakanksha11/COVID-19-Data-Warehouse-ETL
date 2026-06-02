# Schema Design Rationale — COVID-19 Data Platform

This document bridges business requirements and the physical schema.
Every table and column is justified by at least one business question.
Designed following the Kimball dimensional modelling method.

> Business questions: docs/requirements.md
> Physical schema: docs/lld.md

---

## Step 1 — Declare the Grain

The grain is the most important decision in dimensional modelling.
It defines what one row in the fact table represents.

**Declared grain: one country × one day**

This is the finest level of detail in the source data.
All roll-ups (weekly, monthly, continental) are computed at query time
using SQL aggregations — never pre-aggregated in the warehouse.

---

## Step 2 — Map Requirements to Grain, Dimensions, and Facts

| Category | Business Question | Dimensions Needed | Facts / Metrics |
|----------|-----------------|------------------|----------------|
| Descriptive | Which country had the most total deaths? | dim_location (country) | total_deaths |
| Descriptive | What was the peak daily new cases? | dim_location, dim_date | new_cases |
| Descriptive | Which continent had highest total cases? | dim_location (continent) | total_cases |
| Diagnostic | Did hospital beds correlate with lower mortality? | dim_location (hospital_beds) | new_deaths, total_deaths |
| Diagnostic | Did higher GDP reduce death rates? | dim_location (gdp_per_capita) | total_deaths |
| Diagnostic | Did stringency slow case growth? | dim_location, dim_date | new_cases, stringency_index |
| Trend | How did cases trend month by month? | dim_date (month, year) | new_cases |
| Trend | When did vaccination rates accelerate? | dim_location, dim_date | people_vaccinated_per_hundred |
| Trend | Did deaths flatten after vaccination? | dim_date | new_deaths_smoothed, people_fully_vaccinated |
| Comparative | Top 10 countries by deaths per million? | dim_location (country) | total_deaths_per_million |
| Comparative | Europe vs Asia positivity rate over time? | dim_location (continent), dim_date | positive_rate |
| Correlation | Median age vs mortality rate? | dim_location (median_age) | total_deaths, total_cases |
| Correlation | Poverty vs deaths per million? | dim_location (extreme_poverty) | total_deaths_per_million |
| Anomaly | Countries with high cases, low deaths? | dim_location (country) | total_cases, total_deaths |
| Anomaly | Countries with negative new_cases? | dim_location, dim_date | new_cases |
| Prediction | Predict new_cases next 7 days | ml_covid_features (lag cols) | new_cases |
| Prediction | Cluster countries by trajectory | ml_covid_features | all case/death metrics |

---

## Step 3 — Derive Dimensions from Requirements

| Dimension | Required by | Columns justified |
|-----------|------------|------------------|
| dim_location | All categories | country (all questions), continent (comparative, descriptive), population (per-million calcs), gdp_per_capita (diagnostic), median_age (correlation), hospital_beds (diagnostic), HDI (correlation) |
| dim_date | Trend, comparative | date (all), month/year (trend lines), quarter (aggregations), week_number (weekly roll-ups), is_weekend (pattern analysis) |

---

## Step 4 — Why One Fact Table (not three)

Your teammate's project has three fact tables (cases, vaccination, hospitalisation).
We use one. Here is why:

Our source is a single CSV file. All 67 columns share the same grain
(country × day) and come from the same OWID extract.
Splitting into three fact tables would add JOIN complexity
without simplifying the ETL.

The hospitalisation data being 90% null is handled in the fact table
by allowing NULLs — not by creating a separate sparse fact table.
Power BI and Python both handle sparse columns correctly.

The ML feature table (ml_covid_features) is a separate wide table
because it serves a fundamentally different consumer with different
structural needs — not because it has a different grain.

---

## Step 5 — Column Justification by Domain

### Cases (6 columns)
| Column | Justifies | Required by |
|--------|----------|------------|
| new_cases | Peak daily cases, trend analysis | D-02, T-01 |
| total_cases | Country comparison, continental totals | D-01, D-03, C-03 |
| new_cases_smoothed | Smooth trend lines (7-day avg) | T-01 |
| new_cases_per_million | Density comparison across countries | C-01, C-02 |
| total_cases_per_million | Normalised country comparison | C-03 |
| new_cases_smoothed_per_million | Normalised smooth trend | T-01 |

### Deaths (6 columns)
| Column | Justifies | Required by |
|--------|----------|------------|
| new_deaths | Peak deaths, trend | T-05 |
| total_deaths | Country ranking | D-01 |
| new_deaths_smoothed | Smooth trend (7-day avg) | T-05 |
| new_deaths_per_million | Normalised comparison | C-03 |
| total_deaths_per_million | Country ranking normalised | C-04 |
| new_deaths_smoothed_per_million | Normalised smooth | T-05 |

### Testing (7 columns)
| Column | Justifies | Required by |
|--------|----------|------------|
| new_tests | Testing volume trend | DG-07 |
| total_tests | Country testing capacity | D-05 |
| positive_rate | Under-reporting signal, quality check | A-03, CR-03 |
| tests_per_case | Inverse of positive rate | DG-07 |
| new_tests_smoothed | Smooth testing trend | DG-07 |
| new_tests_per_thousand / total_tests_per_thousand | Normalised testing | CR-04 |
| tests_units | Data quality context | Data quality |

### Vaccination (13 columns)
| Column | Justifies | Required by |
|--------|----------|------------|
| people_vaccinated_per_hundred | Vaccination coverage % | T-02, CR-06 |
| people_fully_vaccinated_per_hundred | Full coverage % | T-02 |
| total_boosters_per_hundred | Booster coverage | D-07 |
| new_vaccinations_smoothed | Rollout trend | T-02 |
| people_vaccinated / fully_vaccinated | Raw counts for model training | P-03, P-07 |
| Remaining vaccination cols | Completeness of picture | P-03 |

### Hospitalisation (8 columns)
| Column | Justifies | Required by |
|--------|----------|------------|
| icu_patients | ICU pressure | P-05 |
| hosp_patients | Hospital pressure | P-05 |
| icu_patients_per_million | Normalised ICU | C-03 |
| hosp_patients_per_million | Normalised hospital | C-03 |
| weekly_icu_admissions / hosp_admissions | Weekly admission rate | P-05 |
| Per million versions | Normalised admission rate | P-05 |

> Note: Hospitalisation is 90-97% null. Loaded as-is.
> Only ~40 countries report consistently.

### Policy (1 column)
| Column | Justifies | Required by |
|--------|----------|------------|
| stringency_index | Policy impact analysis | DG-03, T-04, C-06 |

### Excess Mortality (4 columns)
| Column | Justifies | Required by |
|--------|----------|------------|
| excess_mortality_cumulative_absolute | True death toll estimate | A-02 |
| excess_mortality_cumulative | % excess vs expected | A-02 |
| excess_mortality | Weekly excess | A-02 |
| excess_mortality_cumulative_per_million | Normalised excess | A-02 |

> Note: Excess mortality is 97% null. Only ~30 countries report.

---

## Step 6 — Why ML Feature Table is Separate

ml_covid_features is a separate table, not a view of the star schema.

| Need | Star schema | ML feature table |
|------|------------|-----------------|
| Query style | GROUP BY, filter, aggregate | Row-level, all features in one row |
| JOINs | Multiple JOINs available | Zero JOINs — everything flat |
| Lag features | Computed at query time | Pre-computed — faster for training |
| Demographics | In dim_location, need JOIN | Joined in — no extra step |
| Nulls | Acceptable — Power BI handles | Needs strategy — impute or flag |
| Date gaps | Acceptable | Must be filled for time series |

Pre-computing lags at ETL time rather than query time:
- Reduces model training time significantly
- Ensures consistent lag definitions across all models
- Prevents errors from incorrect window function usage in Python

---

## Design Decisions

| Decision | Reason |
|----------|--------|
| One fact table instead of three | Single source CSV — same grain for all columns |
| Sparse columns allowed in fact | 90-97% null for hospitalisation is acceptable — better than a separate sparse table |
| ML feature table separate from fact | Different structural needs for ML vs BI — not different grain |
| Lag features pre-computed in ETL | Consistent definitions, faster training, no Python window function errors |
| dim_date generated not sourced | Ensures no gaps in date dimension even if source has missing dates |
| Surrogate keys on all dimensions | Insulates facts from natural key changes — ISO codes can change |
| VARCHAR-first staging | Prevents package crash — type safety at transformation stage not ingestion |
| No pre-aggregation | Finest grain preserved — all rollups at query time — maximum flexibility |
