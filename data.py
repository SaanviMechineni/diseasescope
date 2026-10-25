"""Data loading, preprocessing and shared analytical helpers for DiseaseScope."""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "india_5_diseases_enriched.xlsx"
SHEET = "All Diseases (combined)"

NUMERIC_COLS = ["Year", "Population_Approx", "Cases", "Deaths", "Incidence_per_100k",
                "Pct_Population_Affected", "Case_Fatality_Rate_pct"]
LAST_COMPLETE_YEAR = 2023   # 2024 is provisional (partial-year) in the source

# The one data-source note shown in the app (Data Quality page), the reports and REPORT_NOTES.md.
DATA_SOURCE_NOTE = ("Data sources: Dengue from published state-wise records; Malaria, Acute Diarrheal Disease, "
                    "Measles and H1N1 are synthetic, modelled on regional patterns for demonstration.")

WEIGHTED = "Population-weighted"
UNWEIGHTED = "Unweighted (simple state average)"


def load_raw():
    """Read the combined sheet exactly as stored (no cleaning)."""
    x = pd.read_excel(DATA_FILE, sheet_name=SHEET)
    x.columns = [str(c).strip() for c in x.columns]
    return x


def preprocess(raw):
    """Clean the raw sheet and impute missing incidence.

    Steps (also documented in REPORT_NOTES.md):
    1. Coerce numeric columns; strip text columns.
    2. Impute missing Incidence_per_100k by linear interpolation across years
       within the same disease and state; any remaining gap uses the disease median.
    3. Re-derive Cases, Pct_Population_Affected and Deaths for imputed rows from
       the imputed incidence (Deaths via that state-disease's median CFR).
    4. Recompute CFR where Cases > 0; CFR stays missing when Cases = 0 (undefined).
    5. Flag imputed rows (Imputed=True) so analyses can exclude them.
    Disease values stay as plain names (e.g. "Dengue") for display and filtering.
    """
    x = raw.copy()
    for c in ["Disease", "State", "Region"]:
        x[c] = x[c].astype(str).str.strip()
    for c in NUMERIC_COLS:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x["Year"] = x["Year"].astype(int)
    x["Provisional"] = x["Provisional"].astype(bool)
    x = x.sort_values(["Disease", "State", "Year"]).reset_index(drop=True)

    x["Imputed"] = x["Incidence_per_100k"].isna()
    x["Incidence_per_100k"] = (x.groupby(["Disease", "State"])["Incidence_per_100k"]
                               .transform(lambda s: s.interpolate(limit_direction="both")))
    x["Incidence_per_100k"] = (x.groupby("Disease")["Incidence_per_100k"]
                               .transform(lambda s: s.fillna(s.median())))

    cfr_med = x.groupby(["Disease", "State"])["Case_Fatality_Rate_pct"].transform("median").fillna(0)
    imp = x["Imputed"]
    x.loc[imp, "Cases"] = (x.loc[imp, "Incidence_per_100k"] * x.loc[imp, "Population_Approx"] / 1e5).round()
    x.loc[imp, "Pct_Population_Affected"] = x.loc[imp, "Incidence_per_100k"] / 1000
    x.loc[imp, "Deaths"] = (x.loc[imp, "Cases"] * cfr_med[imp] / 100).round()
    x["Case_Fatality_Rate_pct"] = np.where(x["Cases"] > 0, x["Deaths"] / x["Cases"] * 100, np.nan)
    return x


def weighted_incidence(g):
    """Population-weighted incidence of a group = total cases per 100k total population."""
    return float((g["Incidence_per_100k"] * g["Population_Approx"]).sum() / g["Population_Approx"].sum())


def agg_incidence(data, by, method):
    """Aggregate Incidence_per_100k over states for each group in `by`.

    Population-weighted: sum(incidence x population) / sum(population), i.e. what
    India (or the region) experienced as a whole. Unweighted: plain mean of state
    values, where Lakshadweep (~70k people) counts as much as Uttar Pradesh (~23 cr).
    """
    if method == WEIGHTED:
        out = data.groupby(by).apply(weighted_incidence, include_groups=False)
    else:
        out = data.groupby(by)["Incidence_per_100k"].mean()
    return out.rename("Incidence_per_100k").reset_index()


def method_note(method):
    return ("Population-weighted average (big states count more)" if method == WEIGHTED
            else "Unweighted average (every state/UT counts equally)")


def pct_change(first, last):
    """Percentage change; NaN when the starting value is 0 or missing."""
    if first is None or pd.isna(first) or first == 0 or pd.isna(last):
        return np.nan
    return (last - first) / first * 100


def anomaly_iqr(data):
    """Flag unusual years relative to each state's own typical level.

    For each disease: r = log1p(incidence) - median log1p(incidence) of that state.
    Observations with r above Q3 + 1.5·IQR are 'High', below Q1 - 1.5·IQR 'Low'.
    The log removes skew; subtracting the state baseline stops large between-state
    differences from hiding unusually low years (with raw values the lower fence
    was negative, so no 'Low' could ever be flagged).
    """
    z = data[~data["Imputed"]].copy()
    z["Log_Inc"] = np.log1p(z["Incidence_per_100k"])
    z["Residual"] = z["Log_Inc"] - z.groupby(["Disease", "State"])["Log_Inc"].transform("median")
    out = []
    for _, g in z.groupby("Disease"):
        q1, q3 = g["Residual"].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        g = g.copy()
        g["IQR_Flag"] = np.where(g["Residual"] > hi, "High", np.where(g["Residual"] < lo, "Low", "Normal"))
        g["Lower_Fence"], g["Upper_Fence"] = lo, hi
        out.append(g)
    return pd.concat(out, ignore_index=True)


def yoy_table(data, disease, year):
    """State-level incidence for `year` with % change vs the previous year."""
    cur = data[(data["Disease"] == disease) & (data["Year"] == year)][["State", "Region", "Incidence_per_100k", "Population_Approx"]]
    prev = data[(data["Disease"] == disease) & (data["Year"] == year - 1)].set_index("State")["Incidence_per_100k"]
    t = cur.copy()
    t["Previous"] = t["State"].map(prev)
    t["YoY_%"] = (t["Incidence_per_100k"] - t["Previous"]) / t["Previous"].replace(0, np.nan) * 100
    return t


def priority_index(t):
    """Priority = 70% normalised incidence + 30% rise score (falls count as 0).

    Rise score = percentile rank of the % rise among rising states. Ranks are used
    instead of dividing by the maximum because % changes from tiny bases can reach
    +3000% and would otherwise squash every other state's rise to ~0.
    """
    t = t.copy()
    inc_norm = t["Incidence_per_100k"] / max(t["Incidence_per_100k"].max(), 1e-9)
    rise = t["YoY_%"].fillna(0)
    rise_norm = rise.where(rise > 0).rank(pct=True).fillna(0)
    t["Priority_Index"] = (0.7 * inc_norm + 0.3 * rise_norm) * 100
    return t.sort_values("Priority_Index", ascending=False)


def trend_slopes(data, start=2019, end=LAST_COMPLETE_YEAR):
    """Per state and disease: least-squares slope of log1p(incidence) per year.

    Reported as approximate % change per year: (exp(slope) - 1) x 100.
    Uses complete years only so the partial 2024 does not fake a decline.
    """
    d = data[(data["Year"] >= start) & (data["Year"] <= end)]
    rows = []
    for (dis, st), g in d.groupby(["Disease", "State"]):
        g = g.sort_values("Year")
        slope = np.polyfit(g["Year"], np.log1p(g["Incidence_per_100k"]), 1)[0]
        rows.append({"Disease": dis, "State": st, "Region": g["Region"].iloc[0],
                     "Log_Slope": slope, "Trend_%_per_year": (np.exp(slope) - 1) * 100})
    return pd.DataFrame(rows)


def resource_priority(data, disease, year=LAST_COMPLETE_YEAR, basis="rate"):
    """Rank states where incidence is high AND rising (for awareness/prevention effort).

    High = state's incidence in `year` above the population-weighted national level.
    Rising = positive 2019–2023 trend. Score (0-100) = 60% percentile rank of the level
    + 40% percentile rank of trend, computed only for states that are rising.
    basis="rate" ranks the level by incidence per 100k (risk per person);
    basis="cases" ranks it by absolute cases (total people affected).
    """
    cur = data[(data["Disease"] == disease) & (data["Year"] == year)]
    nat = weighted_incidence(cur)
    t = cur[["State", "Region", "Incidence_per_100k", "Cases", "Population_Approx"]].merge(
        trend_slopes(data[data["Disease"] == disease])[["State", "Trend_%_per_year"]], on="State")
    t["High"] = t["Incidence_per_100k"] > nat
    t["Rising"] = t["Trend_%_per_year"] > 0
    t["Quadrant"] = np.select(
        [t["High"] & t["Rising"], t["High"] & ~t["Rising"], ~t["High"] & t["Rising"]],
        ["High & rising", "High & stable/falling", "Low & rising"], "Low & stable/falling")
    level = t["Cases"] if basis == "cases" else t["Incidence_per_100k"]
    score = 60 * level.rank(pct=True) + 40 * t["Trend_%_per_year"].rank(pct=True)
    t["Priority_Score"] = np.where(t["Rising"], score, 0.0)
    t["National_Level"] = nat
    return t.sort_values(["Priority_Score", "Incidence_per_100k"], ascending=False)
