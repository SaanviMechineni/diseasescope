"""Machine-learning layer for DiseaseScope.

A) K-Means state risk clustering (unsupervised)
B) Next-year incidence forecast (supervised regression, time-based split)
C) Isolation Forest anomaly detection

All randomness is fixed with RANDOM_STATE so results are reproducible.
Data sources: Dengue from published state-wise records; the other four diseases are
synthetic, modelled on regional patterns for demonstration.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from data import LAST_COMPLETE_YEAR, trend_slopes

RANDOM_STATE = 42

DISEASE_GROUP = {
    "Dengue": "vector-borne", "Malaria": "vector-borne",
    "Acute Diarrheal Disease": "water-borne",
    "Measles": "respiratory/vaccine-preventable", "H1N1 (Seasonal Influenza-A)": "respiratory/vaccine-preventable",
}

# ============================================================
# A) CLUSTERING
# ============================================================

def cluster_features(df):
    """One row per state: log1p mean incidence per disease (2019-2023) + average trend.

    log1p is used because incidence is heavily right-skewed; the trend feature is the
    mean across diseases of each state's slope in log1p incidence per year.
    """
    d = df[df["Year"] <= LAST_COMPLETE_YEAR]
    means = d.groupby(["State", "Disease"])["Incidence_per_100k"].mean().unstack()
    feats = np.log1p(means)
    feats.columns = [f"log_mean_{c}" for c in feats.columns]
    slopes = trend_slopes(df).groupby("State")["Log_Slope"].mean().rename("avg_trend")
    feats = feats.join(slopes)
    region = d.groupby("State")["Region"].first()
    return feats, region


def _name_cluster(z, diseases):
    """Readable name from a cluster centroid in standardised units."""
    groups = {}
    for dis in diseases:
        groups.setdefault(DISEASE_GROUP.get(dis, "other"), []).append(z[f"log_mean_{dis}"])
    gmean = {g: float(np.mean(v)) for g, v in groups.items()}
    top, top_val = max(gmean.items(), key=lambda kv: kv[1])
    if all(v < -0.3 for v in gmean.values()):
        name = "Low overall burden"
    elif all(v > 0.4 for v in gmean.values()):
        name = "High burden across all diseases"
    elif top_val > 0.4:
        name = f"High {top} burden"
    else:
        name = "Moderate mixed burden"
    if z["avg_trend"] > 0.5:
        name += " · rising"
    elif z["avg_trend"] < -0.5:
        name += " · falling"
    return name


def run_clustering(df, k=None, k_range=range(2, 9)):
    """Standardise features, choose k by silhouette score (unless k is given), fit K-Means and PCA."""
    feats, region = cluster_features(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(feats)
    scores = []
    for kk in k_range:
        labels = KMeans(n_clusters=kk, n_init=20, random_state=RANDOM_STATE).fit_predict(X)
        scores.append({"k": kk, "silhouette": silhouette_score(X, labels)})
    scores = pd.DataFrame(scores)
    best_k = int(scores.loc[scores["silhouette"].idxmax(), "k"])
    used_k = k or best_k
    km = KMeans(n_clusters=used_k, n_init=20, random_state=RANDOM_STATE).fit(X)

    diseases = [c.replace("log_mean_", "") for c in feats.columns if c.startswith("log_mean_")]
    centroids = pd.DataFrame(km.cluster_centers_, columns=feats.columns)
    names, seen = {}, {}
    for i, row in centroids.iterrows():
        n = _name_cluster(row, diseases)
        seen[n] = seen.get(n, 0) + 1
        names[i] = n if seen[n] == 1 else f"{n} ({seen[n]})"

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    P = pca.fit_transform(X)
    out = feats.copy()
    out["Cluster_ID"] = km.labels_
    out["Cluster"] = out["Cluster_ID"].map(names)
    out["Region"] = region
    out["PC1"], out["PC2"] = P[:, 0], P[:, 1]
    out = out.reset_index().rename(columns={"index": "State"})

    profile = out.groupby("Cluster")[[f"log_mean_{d}" for d in diseases]].mean()
    profile = np.expm1(profile)
    profile.columns = diseases
    profile["States"] = out.groupby("Cluster").size()
    profile["Avg trend %/yr"] = (np.exp(out.groupby("Cluster")["avg_trend"].mean()) - 1) * 100
    return {"assignments": out, "silhouette": scores, "k": used_k, "best_k": best_k, "profile": profile.reset_index(),
            "pca_var": pca.explained_variance_ratio_, "centroids_z": centroids.rename(index=names)}

# ============================================================
# B) FORECASTING
# ============================================================

def build_panel(df):
    """Lag-feature table: one row per (disease, state, target year).

    Features: lag1 & lag2 = log1p incidence in the previous 1 and 2 years,
    lag_diff = lag1 - lag2 (recent momentum), log population, disease, region.
    Target: log1p incidence in the target year (models are trained in log space
    because of skew; metrics are reported back on the original per-100k scale).
    """
    d = df.sort_values(["Disease", "State", "Year"]).copy()
    d["y"] = np.log1p(d["Incidence_per_100k"])
    g = d.groupby(["Disease", "State"])["y"]
    d["lag1"] = g.shift(1)
    d["lag2"] = g.shift(2)
    d["lag_diff"] = d["lag1"] - d["lag2"]
    d["log_pop"] = np.log(d["Population_Approx"])
    return d


def _design(panel, columns=None):
    X = panel[["lag1", "lag2", "lag_diff", "log_pop"]].copy()
    X = X.join(pd.get_dummies(panel["Disease"], prefix="dis", dtype=float))
    X = X.join(pd.get_dummies(panel["Region"], prefix="reg", dtype=float))
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X


FEATURE_GROUPS = {"Last year's incidence (lag 1)": ["lag1"], "Incidence 2 years ago (lag 2)": ["lag2"],
                  "Recent momentum (lag1 − lag2)": ["lag_diff"], "Population": ["log_pop"],
                  "Disease": "dis_", "Region": "reg_"}


def _models():
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=400, min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=3, random_state=RANDOM_STATE),
    }


def _metrics(y_true, y_pred):
    return {"MAE": mean_absolute_error(y_true, y_pred),
            "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "R²": r2_score(y_true, y_pred)}


def grouped_permutation_importance(model, X, y_true, n_repeats=10):
    """Increase in test MAE (per 100k) when a feature group is shuffled.

    One-hot columns of the same variable (e.g. all disease dummies) are shuffled
    together so 'Disease' is scored as one feature.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    base = mean_absolute_error(y_true, np.expm1(model.predict(X)))
    rows = []
    for name, cols in FEATURE_GROUPS.items():
        cols = [c for c in X.columns if c.startswith(cols)] if isinstance(cols, str) else cols
        incs = []
        for _ in range(n_repeats):
            Xp = X.copy()
            idx = rng.permutation(len(Xp))
            Xp[cols] = Xp[cols].values[idx]
            incs.append(mean_absolute_error(y_true, np.expm1(model.predict(Xp))) - base)
        rows.append({"Feature": name, "MAE increase": float(np.mean(incs)), "Std": float(np.std(incs))})
    return pd.DataFrame(rows).sort_values("MAE increase", ascending=False)


def run_forecast(df, train_until=2022, test_year=2023, input_year=None):
    """Time-based evaluation, then retrain to forecast next year.

    Train: target years 2021..train_until (needs two lags, so 2019-2020 are inputs only).
    Test : target year test_year (never shuffled; the model never sees test-year values).
    The provisional 2024 is never a target; it is only an input for the 2025 forecast.
    input_year: latest year used as input (default: last year in data -> forecast 2025;
    pass 2023 to forecast 2024 from complete years only).
    """
    panel = build_panel(df).dropna(subset=["lag1", "lag2"])
    train = panel[panel["Year"] <= train_until]
    test = panel[panel["Year"] == test_year]
    X_tr, X_te = _design(train), None
    X_te = _design(test, X_tr.columns)
    y_te = test["Incidence_per_100k"].values

    preds = {"Naive baseline (next = this year)": np.expm1(test["lag1"].values)}
    fitted = {}
    for name, m in _models().items():
        m.fit(X_tr, train["y"])
        fitted[name] = m
        preds[name] = np.clip(np.expm1(m.predict(X_te)), 0, None)

    metrics = pd.DataFrame([{"Model": n, **_metrics(y_te, p)} for n, p in preds.items()])
    per_disease = []
    for n, p in preds.items():
        for dis in test["Disease"].unique():
            mask = (test["Disease"] == dis).values
            per_disease.append({"Model": n, "Disease": dis, "MAE": mean_absolute_error(y_te[mask], p[mask])})
    per_disease = pd.DataFrame(per_disease).pivot(index="Disease", columns="Model", values="MAE").reset_index()

    test_out = test[["Disease", "State", "Region", "Year", "Incidence_per_100k"]].copy()
    for n, p in preds.items():
        test_out[n] = p
    importance = grouped_permutation_importance(fitted["Random Forest"], X_te, y_te)

    # Retrain on every complete target year, then forecast the year after the last input year.
    full = panel[panel["Year"] <= LAST_COMPLETE_YEAR]
    X_full = _design(full)
    rf = _models()["Random Forest"].fit(X_full, full["y"])
    last = build_panel(df)
    last_year = int(input_year or df["Year"].max())
    nxt = last[last["Year"] == last_year].copy()
    nxt["lag2"], nxt["lag1"] = nxt["lag1"], nxt["y"]       # shift: inputs become (last_year, last_year-1)
    nxt["lag_diff"] = nxt["lag1"] - nxt["lag2"]
    X_next = _design(nxt, X_full.columns)
    trees = np.stack([t.predict(X_next.values) for t in rf.estimators_])
    fc = nxt[["Disease", "State", "Region"]].copy()
    fc["Forecast_Year"] = last_year + 1
    fc["Last_Value"] = nxt["Incidence_per_100k"].values
    fc["Last_Complete_Value"] = df[df["Year"] == LAST_COMPLETE_YEAR].set_index(["Disease", "State"]).loc[
        list(zip(fc["Disease"], fc["State"])), "Incidence_per_100k"].values
    # Median of the trees (not rf.predict, which is the mean) so the point forecast
    # always lies inside its own P10-P90 range.
    fc["Forecast"] = np.clip(np.expm1(np.percentile(trees, 50, axis=0)), 0, None)
    fc["Low_P10"] = np.clip(np.expm1(np.percentile(trees, 10, axis=0)), 0, None)
    fc["High_P90"] = np.clip(np.expm1(np.percentile(trees, 90, axis=0)), 0, None)

    best = metrics.sort_values("MAE").iloc[0]["Model"]
    return {"metrics": metrics, "per_disease": per_disease, "test": test_out, "importance": importance,
            "forecast": fc.reset_index(drop=True), "best_model": best,
            "n_train": len(train), "n_test": len(test), "train_years": sorted(train["Year"].unique())}

# ============================================================
# C) ISOLATION FOREST
# ============================================================

def run_isolation_forest(anom, contamination=0.05):
    """Isolation Forest per disease on three standardised features.

    anom: output of data.anomaly_iqr (non-imputed rows, with Log_Inc).
    Features: log1p incidence, case fatality rate (0 when there are no cases),
    year-over-year change in log1p incidence (0 for the first year).
    contamination=0.05 means about 5% of observations per disease are flagged.
    """
    z = anom.sort_values(["Disease", "State", "Year"]).copy()
    z["CFR"] = z["Case_Fatality_Rate_pct"].fillna(0)
    z["YoY_log"] = z.groupby(["Disease", "State"])["Log_Inc"].diff().fillna(0)
    out = []
    for _, g in z.groupby("Disease"):
        X = StandardScaler().fit_transform(g[["Log_Inc", "CFR", "YoY_log"]])
        iso = IsolationForest(n_estimators=300, contamination=contamination, random_state=RANDOM_STATE)
        g = g.copy()
        g["IF_Flag"] = np.where(iso.fit_predict(X) == -1, "Anomaly", "Normal")
        g["IF_Score"] = -iso.score_samples(X)   # higher = more unusual
        out.append(g)
    return pd.concat(out, ignore_index=True)
