# Business Questions — COVID-19 Data Warehouse

**Stakeholder:** TBD — pick one before Phase 3 schema design
**Target:** Minimum 30 questions across 6 categories
**Status:** Draft — 18 starter questions below, needs 12+ more

> **Rule:** Every question must be answerable from the warehouse.
> If a question cannot be answered → redesign the schema.
> The longer this list, the stronger the warehouse design.

---

## Stakeholder Role (choose one before proceeding)

- [ ] WHO health official — which countries need intervention and why?
- [ ] Government policy maker — did lockdowns and restrictions work?
- [ ] Hospital administrator — which demographics are highest risk?
- [ ] Researcher — what socioeconomic factors drove mortality outcomes?

---

## Category 1 — Descriptive
*"What happened?"*

| # | Question | Tables Needed | Status |
|---|----------|--------------|--------|
| D-01 | Which country had the most total deaths? | fact + dim_location | ⬜ |
| D-02 | What was the peak single-day new cases globally? | fact + dim_date | ⬜ |
| D-03 | Which continent had the highest total cases? | fact + dim_location | ⬜ |
| D-04 | How many countries reported data in this dataset? | dim_location | ⬜ |
| D-05 | What was the global total test count? | fact | ⬜ |
| D-06 | Which country had the highest single-day death count? | fact + dim_location | ⬜ |
| D-07 | What was the peak global vaccination rate per day? | fact + dim_date | ⬜ |

---

## Category 2 — Diagnostic
*"Why did it happen?"*

| # | Question | Tables Needed | Status |
|---|----------|--------------|--------|
| DG-01 | Did countries with more hospital beds per thousand have lower mortality rates? | fact + dim_location | ⬜ |
| DG-02 | Did higher GDP per capita correlate with lower death rates? | fact + dim_location | ⬜ |
| DG-03 | Did higher stringency index slow case growth? | fact + dim_location + dim_date | ⬜ |
| DG-04 | Did countries with better handwashing facilities have lower transmission rates? | fact + dim_location | ⬜ |
| DG-05 | Did older median age populations have higher mortality? | fact + dim_location | ⬜ |
| DG-06 | Did higher diabetes prevalence correlate with higher death rates? | fact + dim_location | ⬜ |
| DG-07 | Did countries with higher testing rates detect cases earlier? | fact + dim_location | ⬜ |

---

## Category 3 — Trend / Pattern
*"How did it change over time?"*

| # | Question | Tables Needed | Status |
|---|----------|--------------|--------|
| T-01 | How did global new cases trend month by month through 2020–2024? | fact + dim_date | ⬜ |
| T-02 | When did vaccination rates start accelerating per continent? | fact + dim_location + dim_date | ⬜ |
| T-03 | Did reproduction rate drop after lockdowns were imposed? | fact + dim_date | ⬜ |
| T-04 | How did stringency index change over time for top 5 affected countries? | fact + dim_location + dim_date | ⬜ |
| T-05 | Did total deaths flatten after vaccines rolled out? | fact + dim_date | ⬜ |
| T-06 | Which months had the highest new deaths globally? | fact + dim_date | ⬜ |

---

## Category 4 — Comparative
*"How do groups differ?"*

| # | Question | Tables Needed | Status |
|---|----------|--------------|--------|
| C-01 | High income vs low income countries — mortality rate difference? | fact + dim_location | ⬜ |
| C-02 | Europe vs Asia — positivity rate over time? | fact + dim_location + dim_date | ⬜ |
| C-03 | Which 10 countries had the highest deaths per million? | fact + dim_location | ⬜ |
| C-04 | Which 10 countries had the lowest mortality despite high case counts? | fact + dim_location | ⬜ |
| C-05 | How did vaccination rollout speed differ between continents? | fact + dim_location + dim_date | ⬜ |
| C-06 | Countries with stringency > 70 vs < 30 — case growth comparison? | fact + dim_location | ⬜ |

---

## Category 5 — Correlation
*"What factors relate to what?"*

| # | Question | Tables Needed | Status |
|---|----------|--------------|--------|
| CR-01 | Does median age correlate with mortality rate? | fact + dim_location | ⬜ |
| CR-02 | Does extreme poverty correlate with deaths per million? | fact + dim_location | ⬜ |
| CR-03 | Does handwashing access correlate with transmission rate? | fact + dim_location | ⬜ |
| CR-04 | Does GDP per capita correlate with total tests per thousand? | fact + dim_location | ⬜ |
| CR-05 | Does cardiovascular death rate correlate with COVID mortality? | fact + dim_location | ⬜ |
| CR-06 | Does human development index correlate with vaccination rate? | fact + dim_location | ⬜ |

---

## Category 6 — Anomaly
*"What doesn't fit the pattern?"*

| # | Question | Tables Needed | Status |
|---|----------|--------------|--------|
| A-01 | Which countries had high cases but unusually low deaths? | fact + dim_location | ⬜ |
| A-02 | Which countries had death spikes with no corresponding case spike? | fact + dim_location + dim_date | ⬜ |
| A-03 | Any countries with positive rate above 50% sustained for 30+ days? | fact + dim_location + dim_date | ⬜ |
| A-04 | Are there dates where new_cases is negative? Which countries? | fact + dim_location | ⬜ |
| A-05 | Which countries had 0 tests reported for entire months? | fact + dim_location + dim_date | ⬜ |
| A-06 | Are there countries where total_deaths > total_cases (data error)? | fact | ⬜ |

---

## Question Count

| Category | Count | Target | Status |
|----------|-------|--------|--------|
| Descriptive | 7 | 7 | ✅ |
| Diagnostic | 7 | 7 | ✅ |
| Trend / Pattern | 6 | 6 | ✅ |
| Comparative | 6 | 6 | ✅ |
| Correlation | 6 | 5 | ✅ |
| Anomaly | 6 | 5 | ✅ |
| **Total** | **38** | **30** | ✅ |

---

## Questions That Cannot Be Answered Yet

List any questions from above that the current schema cannot answer.
These require schema redesign before Phase 3 is locked.

| Question | Missing data | Fix needed |
|----------|-------------|-----------|
| *(fill in after schema review)* | | |

---

## Notes

- Negative new_cases are OWID corrections — not data errors
- reproduction_rate is 57% null — trend questions limited to countries that report it
- ICU and hospitalisation data is 90%+ null — only ~40 countries report
- Excess mortality is 97% null — very limited analysis possible
- Vaccination data starts December 2020 — pre-vaccination period has nulls

