# DiseaseScope: notes for the project report

Course: Exploratory Data Analysis and Visualisation. All numbers below were produced by the code in this folder (random seed 42), so re-running gives the same results.

---

## 1. Architecture overview

DiseaseScope is a Streamlit web app split into small modules.

| File | Responsibility |
|---|---|
| `app.py` | Page layout, navigation (12 pages), caching, wiring of all modules |
| `data.py` | Loading the Excel sheet, preprocessing/imputation, weighted vs unweighted aggregation, IQR anomaly rule, priority indices, trend slopes |
| `maps.py` | India choropleth: local-first GeoJSON loading, merging state pieces, name matching |
| `ml.py` | Machine learning: K-Means clustering, next-year forecasting, Isolation Forest |
| `advisory.py` | Plain-language public-health content, seasonal calendar, official source links |
| `report.py` | Downloadable state report (PDF + HTML) drawn with matplotlib |
| `theme.py` | Colour palette, Plotly template, page CSS, UI helpers (KPI cards, "Explain this chart") |
| `.streamlit/config.toml` | Base light theme |
| `analysis.py` | Stand-alone EDA script (Q1–Q5) that writes CSV/PNG outputs into `data/` |
| `data/india_states.geojson` | Saved copy of the state boundaries, so the map works offline |

**Data flow:**
1. The Excel file goes through `data.preprocess()` to produce a cleaned DataFrame. This is cached with `st.cache_data`.
2. The cleaned data is aggregated (using the weighting chosen in the sidebar) and drawn with Plotly through a single shared template.
3. The ML models in `ml.py` are trained once and cached with `st.cache_resource`.
4. Results are shown on the ML Insights, My State and Resource Priority pages, and in the PDF/HTML report.

**Pages:**
- Overview
- My State
- Disease Explorer
- Regional Trends
- State Explorer
- Compare Diseases
- Anomaly Radar
- Intelligence Lab
- ML Insights
- Resource Priority
- Public Health Advisory
- Data Quality

---

## 2. Dataset description

**Source and shape:**
- **File:** `data/india_5_diseases_enriched.xlsx`, sheet "All Diseases (combined)".
- **Rows:** 1,080 = 5 diseases × 36 states/UTs × 6 years (2019–2024).
- **Diseases:** Dengue, Malaria, Acute Diarrheal Disease (ADD), Measles, H1N1 (Seasonal Influenza-A).

**Data sources:** Dengue from published state-wise records; Malaria, Acute Diarrheal Disease, Measles and H1N1 are synthetic, modelled on regional patterns for demonstration (see the workbook's "Notes - READ FIRST" sheet). In the app this note appears once, on the Data Quality page, and in each downloadable report; disease names elsewhere are shown without tags.

**Columns: 11 in total.**

7 numerical:
- Year
- Population_Approx
- Cases
- Deaths
- Incidence_per_100k
- Pct_Population_Affected
- Case_Fatality_Rate_pct

4 non-numerical:
- Disease
- State
- Region (North, South, East, West, Central, Northeast)
- Provisional (True/False)

**Derived columns (from the source notes):**
- Incidence = Cases / Population × 100,000
- Pct affected = Cases / Population × 100
- CFR = Deaths / Cases × 100

**Missing values in the raw file:**

| Column | Missing |
|---|---|
| Cases, Deaths, Incidence_per_100k, Pct_Population_Affected | 25 each (Dengue 1; Malaria, ADD, Measles, H1N1 6 each) |
| Case_Fatality_Rate_pct | 32 (the same 25, plus 7 rows with Cases = 0, where CFR is undefined) |
| All other columns | 0 |

**Other properties:**
- **Population** is approximate (rough 2021-era projections) and constant across years for each state.
- **2024** is flagged Provisional for all rows and is clearly a partial year. Population-weighted Dengue incidence is 2.3 per 100k in 2024, against 21.0 in 2023.
- **State list:** the dataset lists Dadra & Nagar Haveli and Daman & Diu separately, as before their 2020 merger. It has no separate Ladakh row.

---

## 3. Preprocessing steps

1. Read the combined sheet; strip column names and text values.
2. Coerce the 7 numeric columns with `pd.to_numeric(errors="coerce")`.
3. **Impute missing incidence (25 rows):**
   - Use linear interpolation across years *within the same state and disease*.
   - If a state had no values at all, fall back to the disease median.
   - *Why:* the earlier version filled every gap with one national median per disease. That ignores the up-to-100× differences between states, so a Lakshadweep gap and a UP gap would get the same value.
4. For imputed rows, re-derive the other columns from the filled incidence:
   - Cases = incidence × population / 100k
   - Pct affected = incidence / 1000
   - Deaths = Cases × that state-disease's median CFR
5. Recompute CFR where Cases > 0. It is left missing where Cases = 0, because division by zero is undefined. This accounts for the 7 remaining gaps.
6. Add an `Imputed` flag; imputed rows are excluded from anomaly detection.
7. **Analysis-time choices:**
   - "Latest complete year" = 2023.
   - Trends use 2019–2023 only.
   - 2024 is shaded as provisional on every time chart.
8. **Map preprocessing:**
   - The GeoJSON had 271 features for 37 state names, because states were split into pieces.
   - Plotly draws only the *first* feature per name. For UP, MP, Bihar, West Bengal and Karnataka that first piece is a sliver under 0.1% of the state's area, which is why those states looked blank.
   - Fix: pieces are merged into one MultiPolygon per state, and coordinates are rounded to 3 decimals (about 100 m).
   - Three names are mapped explicitly: Andaman & Nicobar Island(s), Dadara & Nagar Havelli, NCT of Delhi.
   - Result: all 36 dataset states match. Ladakh has no data.

---

## 4. Population weighting

Each chart that averages across states uses the sidebar switch, and its caption says which method it uses:

- **Population-weighted (default):** Σ(incidence × population) / Σ(population), i.e. total cases per 100k people.
- **Unweighted:** a simple mean of the state values. Lakshadweep (~70,000 people) counts as much as Uttar Pradesh (~23 crore).

2023 example:

| Disease | Weighted | Unweighted |
|---|---|---|
| ADD | 5.88 | 75.65 |
| Dengue | 20.99 | 69.05 |
| H1N1 | 1.10 | 22.19 |
| Malaria | 1.82 | 20.82 |
| Measles | 0.05 | 0.98 |

Unweighted averages overstate national incidence by 3–20×, because small UTs and north-eastern states have high per-person rates.

---

## 5. Statistical methods (non-ML)

### Anomaly Radar: IQR on log-residuals

**Steps:**
1. r = log1p(incidence) − median log1p(incidence) of the same state and disease.
2. For each disease, flag r > Q3 + 1.5·IQR as **High** and r < Q1 − 1.5·IQR as **Low**.

**Why:**
- On raw values the lower fence was negative for every disease, so no "Low" could ever be flagged.
- log1p alone, pooled across states, still flagged **0 Lows**, because differences between states dominate.
- Measuring each value against the state's own baseline asks "was this year unusual for this state?"

**Result:** 76 High and 72 Low out of 1,055 non-imputed observations. Excluding provisional 2024, it is 66 High and 56 Low out of 880.

### Intelligence Lab: one-year priority index

- **Formula:** Priority = 70% × (incidence / top state's incidence) + 30% × rise score.
- **Rise score:** the percentile rank of the year-over-year % rise among *rising* states. Falling states get 0.
- **Fixes made:**
  - The old index used the *absolute* % change, so a big drop raised priority.
  - Dividing by the maximum rise was also replaced with ranks, because % changes from tiny bases reach +3,000%.

### Resource Priority: high AND rising

- **High:** 2023 incidence above the population-weighted national level.
- **Rising:** a positive least-squares slope of log1p incidence over 2019–2023, reported as ≈ % per year.
- **Score:** 60% percentile rank of the level + 40% percentile rank of the trend, for rising states only.
- **Level options:** the level can be a rate (risk per person; favours small UTs) or total cases (people affected; favours big states).

---

## 6. Machine-learning methods

All are in `ml.py`. `random_state=42` is set everywhere, and models are cached with `st.cache_resource`. Results for the non-Dengue diseases come from modelled series and are for demonstration only (see the data-source note in Section 2).

### A) State risk clustering: K-Means (unsupervised)

**Why chosen:**
- It is simple and explainable: each cluster has a centroid that can be described in words.
- It suits the question "which states have a similar disease profile?" where there are no labels.

**Features (36 states × 6):**
- log1p of the mean incidence for each of the 5 diseases (2019–2023).
- Average trend: the mean across diseases of the slope of log1p incidence per year.
- All features are standardised with StandardScaler. The log is used because incidence is heavily right-skewed.

**Choosing k:** k = 2…8 was tested, with `n_init=20`. The silhouette scores were:

| k | Silhouette |
|---|---|
| 2 | **0.493** |
| 3 | 0.426 |
| 4 | 0.411 |
| 5 | 0.252 |
| 6 | 0.271 |
| 7 | 0.285 |
| 8 | 0.281 |

k = 2 is chosen. A slider lets viewers explore other values of k.

**Naming:** clusters are named automatically from their centroids by disease group (vector-borne, water-borne, respiratory/vaccine-preventable):
- **"High burden across all diseases"** (12 states)
- **"Low overall burden"** (24 states)

**Visualisation:** clusters are shown on the India map and on a 2-D PCA scatter. PC1 explains 69.6% of the variance and PC2 14.3%.

**Honest interpretation:**
- PC1 correlates with log population at r ≈ −0.95.
- The split is essentially small UTs and north-eastern states versus large states.
- This partly reflects how the non-Dengue series were modelled, so clusters are presented as exploratory, not as a risk rating.

### B) Next-year incidence forecast: supervised regression

**Why chosen:**
- It tests whether past incidence can predict the next year.
- It is compared against a naive baseline, which is the honest benchmark for short time series.

**Features (per state × disease × target year):**
- lag1 and lag2: log1p incidence one and two years earlier.
- lag_diff = lag1 − lag2: recent momentum.
- log population.
- One-hot disease and one-hot region.

The target is log1p incidence in the target year. Predictions are converted back to the per-100k scale for the metrics.

**Validation: time-based split, years never shuffled.**
- Train on target years 2021–2022 (360 rows; 2019–2020 are only usable as lags).
- Test on target year 2023 (180 rows).
- Provisional 2024 is never a target.

**Models:**
- Linear Regression
- Random Forest (400 trees, min_samples_leaf = 2)
- Gradient Boosting (300 trees, learning rate 0.05, depth 3)
- Naive baseline: next year = this year.

**Results on 2023 (all diseases):**

| Model | MAE | RMSE | R² |
|---|---|---|---|
| **Naive baseline** | **13.62** | **49.50** | **0.818** |
| Linear Regression | 15.06 | 53.45 | 0.788 |
| Gradient Boosting | 17.46 | 58.32 | 0.748 |
| Random Forest | 17.74 | 63.57 | 0.700 |

**Overall, no model beat the naive baseline.** The app states this on the page. With only two training years and noisy jumps between years, last year's value is the strongest predictor. The pooled R² is inflated by large differences between diseases, which is why MAE per disease is also reported:

| Disease | Baseline | Linear Regression | Random Forest | Gradient Boosting |
|---|---|---|---|---|
| ADD | 15.19 | 21.85 | 25.12 | 21.18 |
| Dengue (real) | 38.15 | 42.63 | 42.07 | 42.63 |
| H1N1 | 8.35 | **4.34** | 9.74 | 10.45 |
| Malaria | 5.45 | 5.89 | 11.11 | 12.08 |
| Measles | 0.96 | **0.58** | 0.64 | 0.95 |

Linear Regression beats the baseline for H1N1 and Measles (both modelled series). For Dengue the baseline is best.

**Feature importance (grouped permutation importance of the Random Forest on the test year, measured as the increase in MAE when a feature is shuffled):**

| Feature | MAE increase |
|---|---|
| lag1 | 17.2 |
| lag2 | 9.1 |
| disease | 1.2 |
| population | 0.6 |
| momentum | ≈ 0 |
| region | ≈ 0 |

**Final forecast:**
- The Random Forest is retrained on all complete target years (2021–2023).
- **2025 forecast:** uses 2024 (provisional) and 2023 as inputs.
- **Point forecast and range:** forecast = median of the 400 Random Forest trees' predictions, range = 10th–90th percentile. The median is used (not the forest's mean, `rf.predict`) so the forecast always lies inside its own range.
- **Warning:** because 2024 is a partial year, 2025 forecasts are biased low. The mean Dengue forecast is 31.1, against a 2023 actual of 69.0 (unweighted means of states).
- **Alternative:** the app offers "2023 → forecast 2024" using complete years only, which gives a mean Dengue forecast of 65.1.

### C) ML anomaly detection: Isolation Forest

**Why chosen:**
- It is an unsupervised, multivariate outlier detector that needs no labels or distribution assumptions.
- It complements the single-variable IQR rule.

**Features (standardised separately for each disease):**
- log1p incidence
- CFR (0 when there are no cases)
- Year-over-year change in log1p incidence (0 in the first year)

**Settings:** 300 trees and contamination = 5% per disease (adjustable from 2% to 10% in the app). Imputed rows are excluded.

**Comparison with IQR (2019–2023, 880 observations):**

| IQR \ Isolation Forest | Anomaly | Normal |
|---|---|---|
| High | 12 | 54 |
| Low | 5 | 51 |
| Normal | 29 | 729 |

**Agreement is low by design.** The IQR rule asks "unusual for this state?", while the Isolation Forest asks "unusual combination of level, fatality and change?". For example, the Isolation Forest also catches unusually high case-fatality rates.

---

## 7. Features for society

1. **Public Health Advisory:**
   - Per-disease cards on how it spreads, common symptoms, prevention and when to see a doctor.
   - Wording follows the WHO fact sheets (checked 25 Oct 2026). Links go only to WHO, MoHFW and NCVBDC.
   - No helpline numbers or statistics are invented.
   - A clear "not medical advice" notice.
   - **Seasonal risk calendar:** labelled as *indicative* general patterns. It is not computed from this dataset, which only has yearly data.
2. **My State:** a one-screen summary showing:
   - risk cluster
   - diseases rising (2019–2023)
   - forecast with range
   - prevention tips for the rising diseases
3. **Downloadable state report:**
   - Formats: a 2-page PDF and a self-contained HTML file, built with matplotlib (no extra packages, works offline).
   - Contents: key numbers, charts, prevention tips, data caveats and the disclaimer.
4. **Resource Priority:** states where incidence is high AND rising, framed as "where awareness/prevention could help most", with the method shown on the page.
5. **"Explain this chart"** expanders under every main chart.

---

## 8. Visual design

**Light health theme:**

| Role | Colour |
|---|---|
| Primary deep teal | #0F4C5C |
| Secondary teal | #2A9D8F |
| Coral (alerts/high values only) | #E76F51 |
| Amber (warnings) | #F4A261 |
| Background tint | #E9F3F2 |
| Text | #1F2933 |
| Cards | white |

**Colour use:**
- One Plotly template (`plotly_white+diseasescope`) is used for every chart.
- **Categorical colours** (diseases and regions have fixed colours): #2A9D8F, #4A6FD0, #C2852A, #9A5BB5, #5E8C2E, #C24C7A. These passed a colour-vision-deficiency check: worst adjacent ΔE 8.4 under deuteranopia, and 18.7 under normal vision.
- **Maps and heatmaps** use a single-hue sequential teal scale. The map uses a log colour scale, because a few UTs are 10× higher than all other states.
- Heatmaps across diseases are row-normalised, because diseases differ by up to 100× in size.

---

## 9. Limitations

- **Synthetic data:** four of the five diseases are synthetic. Patterns, clusters and forecasts for them describe the generator, not real epidemiology.
- **Approximate, constant population:** incidence rates are only as good as these rough estimates. Population growth over 2019–2024 is ignored.
- **Only 6 years:** after creating two lags, only 2 training years remain, which is too little for ML to beat a naive forecast.
- **Provisional 2024:** this is a partial year. It is excluded from trends, evaluation and anomaly comparisons, and flagged wherever it is shown.
- **Annual granularity:** seasonality cannot be studied. The seasonal calendar is general guidance, not a data finding.
- **Reporting artefacts:** for example, the 2020 dips likely reflect COVID-19 disruption of surveillance.
- **Administrative boundaries:** the dataset follows pre-2020 boundaries. Ladakh is not separated, and Dadra & Nagar Haveli and Daman & Diu are separate.
- **Small-UT instability:** rates for areas with tiny populations swing wildly. This is why population weighting and rank-based scores were added.

## 10. Future scope

- Replace the synthetic diseases with real IDSP/NCVBDC state-level data, and add monthly data to study seasonality.
- Use year-specific population projections, and district-level data.
- Add climate covariates (rainfall, temperature, humidity) for vector-borne forecasting.
- Use proper time-series models (e.g. hierarchical or Bayesian models that pool across states) and rolling-origin cross-validation once more years exist.
- Calibrate the forecast intervals (e.g. with conformal prediction) instead of relying on the spread of the Random Forest trees.
- Add Hindi and regional-language versions of the advisory pages for wider public reach.

---

## 11. How to run and test

```
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\streamlit.exe run app.py
```
The app opens at http://localhost:8501. See the testing checklist in the final hand-over message.
