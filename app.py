"""DiseaseScope — India disease incidence analytics (Streamlit).

Run with:  streamlit run app.py
Modules: theme.py (look), data.py (cleaning & stats), maps.py (India map),
ml.py (machine learning), advisory.py (health awareness text), report.py (state report).
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data as D
import ml
from advisory import ADVICE, DISCLAIMER, MONTHS, SEASON_NOTE, SEASONAL, SOURCES
from maps import india_map, load_geojson
from report import build_html, build_pdf, state_summary
from theme import (ALERT, CATEGORICAL, DISEASE_COLORS, MUTED, PRIMARY, REGION_COLORS, SECONDARY, SEQUENTIAL,
                   WARNING, badge, chart, header, inject_css, insight, kpi, section, style)

st.set_page_config(page_title="DiseaseScope", page_icon="🩺", layout="wide", initial_sidebar_state="expanded")
inject_css()

# ============================================================
# DATA & CACHED MODELS
# ============================================================

@st.cache_data
def load():
    raw = D.load_raw()
    return raw, D.preprocess(raw)


raw, df = load()
DISEASES = [d for d in DISEASE_COLORS if d in set(df["Disease"])]
REGIONS = sorted(df["Region"].unique())
STATES = sorted(df["State"].unique())
YEARS = sorted(df["Year"].unique())
LC = D.LAST_COMPLETE_YEAR
SHORT = {d: d.replace(" (Seasonal Influenza-A)", "") for d in DISEASES}


@st.cache_resource(show_spinner="Loading India boundaries…")
def geo_cached():
    return load_geojson()


@st.cache_resource(show_spinner="Clustering states…")
def clusters_cached(k=None):
    return ml.run_clustering(load()[1], k=k)


@st.cache_resource(show_spinner="Training forecast models (first run only)…")
def forecast_cached(input_year=None):
    return ml.run_forecast(load()[1], input_year=input_year)


@st.cache_resource(show_spinner="Running Isolation Forest…")
def iforest_cached(contamination=0.05):
    return ml.run_isolation_forest(D.anomaly_iqr(load()[1]), contamination)


@st.cache_data
def slopes_cached():
    return D.trend_slopes(load()[1])


def mark_provisional(fig):
    fig.add_vrect(x0=LC + .5, x1=max(YEARS) + .5, fillcolor=WARNING, opacity=.13, line_width=0,
                  annotation_text="2024 provisional", annotation_position="top left",
                  annotation_font=dict(size=11, color=MUTED))
    return fig


def line_style(fig):
    fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
    fig.update_xaxes(dtick=1, title="")
    return fig


def hbar(frame, x, y, title_x, height=420, text_fmt=".1f", color=SECONDARY, log=False):
    """Horizontal bar chart in one colour (length already encodes the value), with room for labels."""
    f = px.bar(frame, x=x, y=y, orientation="h", text=x, log_x=log)
    f.update_traces(marker_color=color, texttemplate=f"%{{text:{text_fmt}}}", textposition="outside", cliponaxis=False)
    style(f, height)
    f.update_yaxes(title="", categoryorder="total ascending")
    f.update_xaxes(title=title_x)
    vmax = float(frame[x].max()) if len(frame) else 1
    if log:
        vmin = float(frame[x][frame[x] > 0].min()) if (frame[x] > 0).any() else .01
        f.update_xaxes(range=[np.log10(vmin) - .3, np.log10(vmax) + .35])
    else:
        f.update_xaxes(range=[0, vmax * 1.18])
    return f


def row_normalised_heatmap(mat, height=380):
    """Heatmap coloured by share of each row's maximum, labelled with actual values.

    Diseases differ by up to 100x in scale, so one shared colour scale would show only
    the largest disease; row-normalising lets you compare WITHIN each disease.
    """
    z = mat.div(mat.max(axis=1), axis=0)
    f = go.Figure(go.Heatmap(z=z.values, x=[str(c) for c in mat.columns], y=[SHORT.get(i, i) for i in mat.index],
                             text=mat.round(1).values, texttemplate="%{text}", colorscale=SEQUENTIAL,
                             colorbar=dict(title="Share of<br>row max"),
                             hovertemplate="%{y} · %{x}<br>Incidence %{text} per 100k<extra></extra>"))
    style(f, height)
    return f

# ============================================================
# SIDEBAR
# ============================================================

PAGES = ["🏠 Overview", "🧭 My State", "🦠 Disease Explorer", "📈 Regional Trends", "🗺️ State Explorer",
         "🔎 Compare Diseases", "🚨 Anomaly Radar", "🧠 Intelligence Lab", "🤖 ML Insights",
         "🎯 Resource Priority", "🩺 Public Health Advisory", "🧹 Data Quality"]

with st.sidebar:
    st.markdown('<div class="sidebar-brand">🩺 DiseaseScope</div><div class="sidebar-sub">India · Disease Incidence Analytics</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="side-label">Explore</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, label_visibility="collapsed")
    st.markdown('<div class="side-label">Averaging across states</div>', unsafe_allow_html=True)
    METHOD = st.radio("Averaging method", [D.WEIGHTED, D.UNWEIGHTED], label_visibility="collapsed",
                      help="Population-weighted = what the population experienced as a whole. "
                           "Unweighted = every state/UT counts equally (Lakshadweep ≈ Uttar Pradesh).")
    st.markdown("---")
    st.caption(f"{min(YEARS)}–{max(YEARS)} · {len(DISEASES)} diseases · {len(STATES)} states/UTs · {len(df):,} records")
    st.caption("Incidence = cases per 100,000 people. 2024 is provisional (partial year).")

# ============================================================
# OVERVIEW
# ============================================================

def page_overview():
    st.markdown("""<div class="hero"><div class="eyebrow">India · Disease incidence 2019–2024</div>
    <h1>See where disease is rising, and where prevention can help.</h1>
    <p>Six years of state-level records for five diseases, explored through trends, maps, anomaly checks,
    machine-learning forecasts and plain-language health guidance.</p></div>""", unsafe_allow_html=True)
    c = st.columns(4)
    with c[0]: kpi("RECORDS", f"{len(df):,}", "disease × state × year", "📊")
    with c[1]: kpi("DISEASES", len(DISEASES), "tracked conditions", "🦠")
    with c[2]: kpi("STATES / UTs", len(STATES), "36 areas", "🗺️")
    with c[3]: kpi("YEARS", f"{min(YEARS)}–{max(YEARS)}", "2024 provisional", "📅")

    complete = df[df["Year"] <= LC]
    dm = D.agg_incidence(complete, ["Disease"], METHOD).sort_values("Incidence_per_100k", ascending=False)
    ym = D.agg_incidence(df, ["Disease", "Year"], METHOD)
    dengue = ym[ym["Disease"] == "Dengue"].set_index("Year")["Incidence_per_100k"]
    rm = D.agg_incidence(complete[complete["Disease"] == "Dengue"], ["Region"], METHOD).sort_values("Incidence_per_100k", ascending=False)

    section("⚡ At a glance", D.method_note(METHOD) + f" · complete years 2019–{LC}")
    s = st.columns(4)
    sig = [("HIGHEST INCIDENCE DISEASE", dm.iloc[0]["Disease"], f"{dm.iloc[0]['Incidence_per_100k']:.2f} per 100k"),
           ("DENGUE · LEADING REGION", rm.iloc[0]["Region"], f"{rm.iloc[0]['Incidence_per_100k']:.2f} per 100k"),
           (f"DENGUE IN {LC}", f"{dengue[LC]:.2f}", "per 100k · last complete year"),
           (f"DENGUE 2019 → {LC}", f"{D.pct_change(dengue[2019], dengue[LC]):+.1f}%", "change in incidence")]
    for col, (a, b, cx) in zip(s, sig):
        with col: st.markdown(f'<div class="signal"><div class="signal-title">{a}</div><div class="signal-value">{b}</div>'
                              f'<div class="signal-text">{cx}</div></div>', unsafe_allow_html=True)

    l, r = st.columns([1, 1.25], gap="large")
    with l:
        section("Disease landscape", f"Average incidence 2019–{LC} · {D.method_note(METHOD)}")
        chart(hbar(dm.assign(Disease=dm["Disease"].map(SHORT)), "Incidence_per_100k", "Disease", "Incidence per 100k", 400, ".2f"),
              "Each bar is one disease's average yearly incidence (cases per 100,000 people) over 2019–2023. "
              "Switch the averaging method in the sidebar to see how much small UTs change the picture.")
    with r:
        section("National pulse", f"Incidence by year (log scale) · {D.method_note(METHOD)}")
        f = px.line(ym, x="Year", y="Incidence_per_100k", color="Disease", markers=True, color_discrete_map=DISEASE_COLORS, log_y=True)
        line_style(mark_provisional(f))
        f.update_yaxes(title="Incidence per 100k (log)")
        chart(f, "One line per disease across years. The y-axis is logarithmic so small diseases (Measles) and large ones "
                 "(ADD, Dengue) fit on one chart; equal vertical steps mean equal % change. The shaded 2024 is a partial year.", 400)

    section("🗺️ India map", "Hover a state to see its value. Darker teal = higher (log colour scale).")
    m1, m2, m3 = st.columns([1.3, 1, 1])
    with m1: md = st.selectbox("Disease", DISEASES, key="ov_d")
    with m2: my = st.selectbox("Year", YEARS, index=YEARS.index(LC), key="ov_y")
    with m3: mm = st.selectbox("Map metric", ["Incidence_per_100k", "Cases", "Deaths"], key="ov_m",
                               format_func=lambda c: c.replace("_", " ").replace("per 100k", "per 100k"))
    frame = df[(df["Disease"] == md) & (df["Year"] == my)][["State", "Region", mm]]
    try:
        geo, src = geo_cached()
        fig, unmatched, no_data = india_map(geo, frame, mm, mm.replace("_", " "), hover={"Region": True, mm: ":,.2f"})
        chart(fig, f"Each state is shaded by {mm.replace('_', ' ')} for {md} in {my}. The colour scale is logarithmic so that a few "
                   "very high UTs do not wash out every other state. Per-100k incidence compares risk per person; "
                   "Cases shows absolute burden, which naturally favours populous states.")
        st.caption(f"Boundaries: {src}. Unmatched dataset states: {', '.join(unmatched) or 'none'}. "
                   f"Map areas without data: {', '.join(no_data) or 'none'} (Ladakh is included in J&K in this dataset).")
    except Exception as e:  # noqa: BLE001
        st.warning(f"The India map could not load ({e}). Other features remain available.")

    top = frame.sort_values(mm, ascending=False).head(12)
    section(f"🔥 Top 12 states · {SHORT[md]} · {my}")
    h1, h2 = st.columns([1.2, 1], gap="large")
    with h1:
        chart(hbar(top, mm, "State", mm.replace("_", " "), 460, ",.1f", ALERT),
              "The 12 highest-ranked states for the map selection above. Coral is used here because these are the highest values.")
    with h2:
        st.dataframe(top.round(2), hide_index=True, height=440)

# ============================================================
# DISEASE EXPLORER
# ============================================================

def page_disease():
    header("Disease Explorer", "Deep-dive into one disease.")
    a, b, c = st.columns([1.3, 1, 1])
    with a: disease = st.selectbox("Disease", DISEASES, key="dx_d")
    with b: region = st.selectbox("Region", ["All Regions"] + REGIONS, key="dx_r")
    with c: year = st.selectbox("Year", YEARS, index=YEARS.index(LC), key="dx_y")
    data = df[df["Disease"] == disease]
    if region != "All Regions":
        data = data[data["Region"] == region]
    yd = data[data["Year"] == year]
    k1, k2, k3 = st.columns(3)
    with k1: kpi("INCIDENCE", f"{D.agg_incidence(yd.assign(k=1), ['k'], METHOD)['Incidence_per_100k'].iloc[0]:.2f}",
                 f"per 100k · {year} · {'weighted' if METHOD == D.WEIGHTED else 'unweighted'}", "📈")
    with k2: kpi("CASES", f"{yd['Cases'].sum():,.0f}", str(year), "🧾")
    with k3: kpi("DEATHS", f"{yd['Deaths'].sum():,.0f}", str(year), "⚕️")

    trend = D.agg_incidence(data, ["Year"], METHOD)
    t = trend.set_index("Year")["Incidence_per_100k"]
    section("📈 Trajectory", D.method_note(METHOD))
    f = px.line(trend, x="Year", y="Incidence_per_100k", markers=True)
    f.update_traces(line_color=DISEASE_COLORS[disease])
    line_style(mark_provisional(f))
    f.update_yaxes(title="Incidence per 100k")
    chart(f, f"Yearly {disease} incidence for {region.lower()}. Dips in 2020 may reflect COVID-19 disruption of reporting; "
             "the shaded 2024 is incomplete and should not be read as a real fall.", 400)
    x1, x2, x3 = st.columns(3)
    x1.metric("2019", f"{t[2019]:.2f}")
    x2.metric(str(LC), f"{t[LC]:.2f}")
    x3.metric(f"2019 → {LC}", f"{D.pct_change(t[2019], t[LC]):+.1f}%")

    rank = yd[["State", "Region", "Incidence_per_100k", "Cases"]].sort_values("Incidence_per_100k", ascending=False)
    l, r = st.columns([1.25, 1], gap="large")
    with l:
        section(f"State ranking · {year}")
        chart(hbar(rank.head(15), "Incidence_per_100k", "State", "Incidence per 100k", 500),
              "The 15 states with the highest incidence (per person risk) in the chosen year and region.")
    with r:
        section("Top states table")
        st.dataframe(rank.head(15).round(2), hide_index=True, height=470)
    if not rank.empty:
        insight("✦ INSIGHT", f"In <b>{year}</b>, <b>{rank.iloc[0]['State']}</b> had the highest {disease} incidence in this scope "
                f"at <b>{rank.iloc[0]['Incidence_per_100k']:.2f}</b> per 100,000.")

# ============================================================
# REGIONAL TRENDS
# ============================================================

def page_regional():
    header("Regional Trends", "Compare regional trajectories and concentration.")
    a, b = st.columns(2)
    with a: disease = st.selectbox("Disease", DISEASES, key="rg_d")
    with b: regions = st.multiselect("Regions", REGIONS, default=REGIONS, key="rg_r")
    data = df[(df["Disease"] == disease) & (df["Region"].isin(regions or REGIONS))]
    trend = D.agg_incidence(data, ["Region", "Year"], METHOD)
    section("📈 Regional trajectories", D.method_note(METHOD) + " within each region")
    f = px.line(trend, x="Year",y="Incidence_per_100k", color="Region", markers=True, color_discrete_map=REGION_COLORS)
    line_style(mark_provisional(f))
    f.update_yaxes(title="Incidence per 100k")
    chart(f, "One line per region. With population weighting, a region's line reflects its big states; unweighted, "
             "small UTs and north-eastern states can pull a region's average up sharply.", 480)

    comp = data[data["Year"] <= LC]
    summ = D.agg_incidence(comp, ["Region"], METHOD).merge(
        comp.groupby("Region").agg(Total_Cases=("Cases", "sum"), Total_Deaths=("Deaths", "sum")).reset_index())
    l, r = st.columns(2, gap="large")
    with l:
        section("Regional ranking", f"2019–{LC}")
        chart(hbar(summ, "Incidence_per_100k", "Region", "Incidence per 100k", 400),
              "Average incidence per region over the complete years (2019–2023).")
    with r:
        section("Regional summary")
        st.dataframe(summ.sort_values("Incidence_per_100k", ascending=False).round(2), hide_index=True, height=360)
    section("🧬 Disease × region fingerprint", f"2019–{LC} · colour = share of each disease's highest region")
    heat = D.agg_incidence(df[df["Year"] <= LC], ["Disease", "Region"], METHOD).pivot(index="Disease", columns="Region", values="Incidence_per_100k")
    chart(row_normalised_heatmap(heat.reindex(DISEASES)),
          "Each row is a disease; the darkest cell is the region where that disease is highest. Numbers are actual incidence per 100k. "
          "Colours are scaled per row because diseases differ by up to 100× in size.")

# ============================================================
# STATE EXPLORER
# ============================================================

def page_state():
    header("State Explorer", "A full profile for one state or union territory.")
    state = st.selectbox("State / UT", STATES, index=STATES.index("Telangana"), key="se_s")
    data = df[df["State"] == state]
    yd = data[data["Year"] == LC]
    k = st.columns(4)
    with k[0]: kpi("REGION", data["Region"].iloc[0], "dataset classification", "📍")
    with k[1]: kpi("POPULATION", f"{data['Population_Approx'].iloc[0] / 1e5:,.1f} lakh", "approximate, constant", "👥")
    with k[2]: kpi(f"CASES {LC}", f"{yd['Cases'].sum():,.0f}", "all 5 diseases", "🧾")
    with k[3]: kpi(f"DEATHS {LC}", f"{yd['Deaths'].sum():,.0f}", "all 5 diseases", "⚕️")
    l, r = st.columns(2, gap="large")
    prof = data[data["Year"] <= LC].groupby("Disease")["Incidence_per_100k"].mean().reset_index()
    with l:
        section("Disease profile", f"Average incidence 2019–{LC}")
        f = hbar(prof.assign(Disease=prof["Disease"].map(SHORT)), "Incidence_per_100k", "Disease", "Incidence per 100k (log)", 420, ".2f", log=True)
        chart(f, "How much of each disease this state recorded per 100,000 people, averaged over complete years. Log axis.")
    with r:
        section("State trajectory", "Log scale")
        f = px.line(data, x="Year", y="Incidence_per_100k", color="Disease", markers=True, color_discrete_map=DISEASE_COLORS, log_y=True)
        line_style(mark_provisional(f))
        f.update_layout(legend=dict(orientation="h", y=-.2))
        f.update_yaxes(title="Incidence per 100k (log)")
        chart(f, "Each line is one disease in this state over time. The log scale shows % changes fairly for small and large diseases.", 420)
    section("State records")
    cols = ["Disease", "Year", "Cases", "Deaths", "Incidence_per_100k", "Case_Fatality_Rate_pct", "Provisional", "Imputed"]
    st.dataframe(data[cols].sort_values(["Year", "Disease"]).round(2), hide_index=True, height=420)

# ============================================================
# COMPARE DISEASES
# ============================================================

def page_compare():
    header("Compare Diseases", "Put several diseases on one canvas.")
    sel = st.multiselect("Diseases", DISEASES, default=DISEASES[:3], key="cp")
    if not sel:
        st.info("Select at least one disease.")
        return
    log = st.toggle("Logarithmic y-axis", value=True)
    comp = D.agg_incidence(df[df["Disease"].isin(sel)], ["Disease", "Year"], METHOD)
    section("📊 Incidence comparison", D.method_note(METHOD))
    f = px.line(comp, x="Year", y="Incidence_per_100k", color="Disease", markers=True, color_discrete_map=DISEASE_COLORS, log_y=log)
    line_style(mark_provisional(f))
    f.update_yaxes(title="Incidence per 100k" + (" (log)" if log else ""))
    chart(f, "Each line is a disease's national incidence per year. Use the log axis to compare growth rates; "
             "turn it off to compare absolute size.", 480)
    pv = comp.pivot(index="Disease", columns="Year", values="Incidence_per_100k")
    cols = st.columns(len(sel))
    for col, d in zip(cols, sel):
        with col:
            st.markdown(f'<div class="signal"><div class="signal-title">{SHORT[d].upper()}</div>'
                        f'<div class="signal-value">{pv.loc[d, LC]:.2f}</div><div class="signal-text">{LC} incidence / 100k<br>'
                        f'2019→{LC} {badge(D.pct_change(pv.loc[d, 2019], pv.loc[d, LC]))}</div></div>', unsafe_allow_html=True)
    snap = df[(df["Disease"].isin(sel)) & (df["Year"] == LC)].groupby("Disease").agg(
        Total_Cases=("Cases", "sum"), Total_Deaths=("Deaths", "sum")).reset_index()
    snap = snap.merge(pv[LC].rename("Incidence_per_100k").reset_index())
    snap["CFR_%"] = snap["Total_Deaths"] / snap["Total_Cases"] * 100
    section(f"{LC} snapshot")
    st.dataframe(snap.round(2), hide_index=True)
    section("Disease × year fingerprint", "Colour = share of each disease's peak year")
    chart(row_normalised_heatmap(pv.reindex([d for d in DISEASES if d in sel]), 320),
          "Darkest cell = each disease's worst year. Numbers are actual incidence per 100k.")

# ============================================================
# ANOMALY RADAR
# ============================================================

def page_anomaly():
    header("Anomaly Radar", "Flag years that were unusually high or low for a state — with a transparent IQR rule.")
    excl = st.checkbox("Exclude provisional 2024 (partial-year values look artificially low)", value=True)
    ad = D.anomaly_iqr(df)
    if excl:
        ad = ad[~ad["Provisional"]]
    unusual = ad[ad["IQR_Flag"] != "Normal"]
    k = st.columns(3)
    with k[0]: kpi("UNUSUAL", f"{len(unusual):,}", f"of {len(ad):,} observations", "🚨")
    with k[1]: kpi("HIGH", f"{(ad['IQR_Flag'] == 'High').sum():,}", "above upper fence", "🔺")
    with k[2]: kpi("LOW", f"{(ad['IQR_Flag'] == 'Low').sum():,}", "below lower fence", "🔻")
    flag_colors = {"High": ALERT, "Low": PRIMARY, "Normal": "#C9D6D4"}
    section("Where the flags fall", "Each dot = one state-year; position = distance from that state's usual level (log scale)")
    f = px.strip(ad.assign(Disease=ad["Disease"].map(SHORT)), x="Disease", y="Residual", color="IQR_Flag",
                 color_discrete_map=flag_colors, hover_data=["State", "Year", "Incidence_per_100k"], stripmode="overlay")
    f.update_traces(marker=dict(size=8, line=dict(width=1, color="white")))
    f.update_yaxes(title="log1p(incidence) − state median")
    f.update_xaxes(title="")
    chart(f, "Zero means a typical year for that state. Dots far above zero (coral) were unusually high years; far below "
             "(dark teal) unusually low. Fences are Q1 − 1.5·IQR and Q3 + 1.5·IQR, computed per disease.", 440)
    filt = st.selectbox("Disease filter", ["All Diseases"] + DISEASES, key="an_f")
    show = unusual if filt == "All Diseases" else unusual[unusual["Disease"] == filt]
    cols = ["Disease", "State", "Year", "Incidence_per_100k", "Residual", "IQR_Flag", "Provisional"]
    section("Flagged observations")
    st.dataframe(show[cols].sort_values("Residual", ascending=False).round(3), hide_index=True, height=420)
    insight("✦ METHOD", "1) Take log1p(incidence) to remove skew. 2) Subtract the median of the same state and disease, so each "
            "value is measured against that state's normal level. 3) For each disease, flag residuals above Q3 + 1.5·IQR as "
            "<b>High</b> and below Q1 − 1.5·IQR as <b>Low</b>. Imputed rows are excluded. On raw values the lower fence was "
            "negative, so a 'Low' could never be found. This is a statistical flag, not a diagnosis.")

# ============================================================
# INTELLIGENCE LAB
# ============================================================

def page_lab():
    header("Intelligence Lab", "A one-year priority board: where incidence is high and rising since last year.")
    a, b = st.columns(2)
    with a: disease = st.selectbox("Focus disease", DISEASES, key="lb_d")
    with b: year = st.selectbox("Focus year", YEARS[1:], index=YEARS[1:].index(LC), key="lb_y")
    t = D.priority_index(D.yoy_table(df, disease, year))
    cur = df[(df["Disease"] == disease) & (df["Year"] == year)]
    nat = D.agg_incidence(cur.assign(k=1), ["k"], METHOD)["Incidence_per_100k"].iloc[0]
    top, fastest = t.iloc[0], t.sort_values("YoY_%", ascending=False).iloc[0]
    reg = D.agg_incidence(cur, ["Region"], METHOD).sort_values("Incidence_per_100k", ascending=False)
    c = st.columns(4)
    with c[0]: kpi("NATIONAL LEVEL", f"{nat:.2f}", f"per 100k · {'weighted' if METHOD == D.WEIGHTED else 'unweighted'}", "◎")
    with c[1]: kpi("TOP PRIORITY", top["State"], f"index {top['Priority_Index']:.1f}/100", "🎯")
    with c[2]: kpi("FASTEST RISE", fastest["State"], f"{fastest['YoY_%']:+.1f}% vs {year - 1}", "⚡")
    with c[3]: kpi("LEADING REGION", reg.iloc[0]["Region"], f"{reg.iloc[0]['Incidence_per_100k']:.2f} per 100k", "📍")
    if year == max(YEARS):
        insight("⚠ PROVISIONAL YEAR", "2024 is a partial year, so most states show a fall versus 2023. Prefer 2023.", "warn")
    section("🎯 Priority board", "Index = 70% current incidence (scaled to the top state) + 30% rise score (percentile rank of the "
            "year-over-year % rise among rising states). Falls count as zero, so a big drop never raises priority.")
    board = t[["State", "Region", "Incidence_per_100k", "YoY_%", "Priority_Index"]].head(15)
    st.dataframe(board.round(2), hide_index=True, height=460)
    l, r = st.columns(2, gap="large")
    with l:
        section("Incidence × momentum")
        f = px.scatter(t, x="Incidence_per_100k", y="YoY_%", size=t["Priority_Index"].clip(lower=1), hover_name="State",
                       color="Priority_Index", color_continuous_scale=SEQUENTIAL)
        f.add_hline(y=0, line_dash="dot", line_color=MUTED)
        f.update_xaxes(title="Incidence per 100k")
        f.update_yaxes(title="Change vs previous year (%)")
        chart(f, "Right = high incidence; above the dotted line = rising. Bigger, darker bubbles have a higher priority index.", 440)
    with r:
        section("Regional concentration", D.method_note(METHOD))
        chart(hbar(reg, "Incidence_per_100k", "Region", "Incidence per 100k", 440), "Incidence per region for the focus year.")
    st.download_button("⬇️ Export priority board (CSV)", t.to_csv(index=False).encode(), f"{disease}_{year}_priority.csv", "text/csv")

# ============================================================
# ML INSIGHTS
# ============================================================

def page_ml():
    header("🤖 ML Insights", "Three machine-learning methods: grouping states, forecasting next year, and finding anomalies.")
    insight("ℹ REPRODUCIBLE", "All models use fixed random seeds (42), so results are the same on every run.")
    tA, tB, tC = st.tabs(["A · State risk clusters", "B · Next-year forecast", "C · ML anomaly detection"])

    with tA:
        base = clusters_cached()
        with st.expander("📘 In plain English: what is clustering?", expanded=True):
            st.write("K-Means groups states that have a similar disease profile, without being told any labels. For each state "
                     f"we use its average incidence of each disease (2019–{LC}, log-scaled because a few states have very large "
                     "values) plus its average trend, and put every feature on the same scale. We try 2 to 8 groups and choose "
                     "the number with the best **silhouette score** (how clearly separated the groups are; closer to 1 is better).")
        sil = base["silhouette"]
        l, r = st.columns([1, 1.4], gap="large")
        with l:
            section("Choosing k", f"Best silhouette at k = {base['best_k']}")
            f = px.line(sil, x="k", y="silhouette", markers=True)
            f.update_traces(line_color=SECONDARY, marker=dict(size=9))
            f.add_scatter(x=[base["best_k"]], y=[sil["silhouette"].max()], mode="markers", marker=dict(size=14, color=ALERT),
                          name="chosen", showlegend=False)
            f.update_xaxes(dtick=1, title="Number of clusters (k)")
            f.update_yaxes(title="Silhouette score")
            chart(f, "Higher = better separated groups. The coral dot marks the k chosen automatically.", 340)
            k = st.slider("Explore a different k", 2, 8, base["best_k"])
        res = clusters_cached(k) if k != base["best_k"] else base
        a = res["assignments"]
        names = sorted(a["Cluster"].unique())
        cmap = dict(zip(names, CATEGORICAL))
        with r:
            section("Clusters on the map", f"k = {res['k']}")
            geo, _ = geo_cached()
            fig, _, _ = india_map(geo, a[["State", "Cluster", "Region"]], "Cluster", "Cluster", hover={"Region": True},
                                  discrete_map=cmap, height=470)
            fig.update_layout(legend=dict(orientation="h", y=-.05))
            chart(fig, "States with the same colour have a similar disease profile.")
        l2, r2 = st.columns([1.2, 1], gap="large")
        with l2:
            section("PCA view", f"PC1 explains {res['pca_var'][0]:.0%}, PC2 {res['pca_var'][1]:.0%} of the variation")
            f = px.scatter(a, x="PC1", y="PC2", color="Cluster", hover_name="State", text="State", color_discrete_map=cmap)
            f.update_traces(marker=dict(size=10, line=dict(width=1.5, color="white")), textposition="top center", textfont_size=9)
            f.update_layout(legend=dict(orientation="h", y=-.2))
            chart(f, "PCA squeezes the 6 features into 2 axes so the states can be drawn on a page. Nearby dots have similar "
                     "profiles. It is only for display — clustering used all 6 features.", 480)
        with r2:
            section("Cluster profiles", "Typical incidence per 100k (2019–2023)")
            p = res["profile"].rename(columns=SHORT)
            st.dataframe(p.round(2), hide_index=True)
            corr = np.corrcoef(a["PC1"], np.log(df.groupby("State")["Population_Approx"].first().reindex(a["State"]).values))[0, 1]
            insight("✦ WHAT THE CLUSTERS SHOW", f"With k = {res['k']}, the main split separates mostly small UTs and north-eastern "
                    "states (high incidence per person for every disease) from large states. PC1 correlates with log population at "
                    f"r = {corr:.2f}. This partly reflects how the non-Dengue series were modelled, so treat the clusters as an "
                    "exploratory grouping, not a risk rating.")

    with tB:
        choice = st.radio("Latest input year", ["2024 (provisional) → forecast 2025", f"{LC} (complete) → forecast 2024"],
                          horizontal=True, help="2024 is a partial year. Using it as input pulls forecasts down, especially for Dengue.")
        fr = forecast_cached(None if choice.startswith("2024") else LC)
        with st.expander("📘 In plain English: how the forecast works", expanded=True):
            st.write("For each state and disease the model looks at **last year's** and the **year before's** incidence, plus the "
                     "disease, the region and the population, and predicts **next year's** incidence. We train on target years "
                     f"{fr['train_years'][0]}–{fr['train_years'][-1]} ({fr['n_train']} rows) and test on {LC} ({fr['n_test']} rows) "
                     "the model has never seen — years are never shuffled, because in real life you cannot use the future to "
                     "predict the past. Every model is compared with a **naive baseline: next year = this year**. Errors are in "
                     "cases per 100,000 people (MAE = average miss, RMSE = punishes big misses more, R² = share of variation explained).")
        m = fr["metrics"].copy()
        base_mae = m.loc[m["Model"].str.startswith("Naive"), "MAE"].iloc[0]
        m["vs baseline"] = (m["MAE"] / base_mae - 1) * 100
        section(f"Test results · target year {LC}")
        st.dataframe(m.round(3), hide_index=True)
        ml_best = m[~m["Model"].str.startswith("Naive")].sort_values("MAE").iloc[0]
        if ml_best["MAE"] >= base_mae:
            insight("✦ HONEST RESULT", f"<b>No model beat the naive baseline</b> on {LC}. The best model ({ml_best['Model']}) "
                    f"had MAE {ml_best['MAE']:.2f} versus {base_mae:.2f} for 'same as last year'. With only two training years "
                    "and noisy year-to-year jumps, last year's value is the strongest predictor. The forecasts below are "
                    "shown to demonstrate the method, not as reliable predictions.", "alert")
        else:
            insight("✦ RESULT", f"<b>{ml_best['Model']}</b> beat the naive baseline (MAE {ml_best['MAE']:.2f} vs {base_mae:.2f}).")
        l, r = st.columns(2, gap="large")
        with l:
            section("Error by disease (MAE)", "Lower is better; the overall R² is inflated by big differences between diseases")
            st.dataframe(fr["per_disease"].assign(Disease=fr["per_disease"]["Disease"].map(SHORT)).round(2), hide_index=True)
        with r:
            section("What the Random Forest relies on", "Permutation importance on the test year")
            imp = fr["importance"]
            f = px.bar(imp, x="MAE increase", y="Feature", orientation="h", error_x="Std")
            f.update_traces(marker_color=SECONDARY)
            f.update_yaxes(title="", categoryorder="total ascending")
            f.update_xaxes(title="Increase in test MAE when shuffled")
            chart(f, "We shuffle one input at a time and measure how much worse the predictions get. A big increase means the "
                     "model depends on that input; near zero means it is ignored.", 320)
        section("Predicted vs actual", f"Test year {LC} · log–log scale")
        mdl = st.selectbox("Model", [c for c in fr["test"].columns if c in set(m["Model"])], index=0, key="ml_m")
        t = fr["test"]
        f = px.scatter(t, x="Incidence_per_100k", y=mdl, color="Disease", hover_name="State", log_x=True, log_y=True,
                       color_discrete_map=DISEASE_COLORS)
        lim = [max(t["Incidence_per_100k"].min(), .01), t["Incidence_per_100k"].max()]
        f.add_scatter(x=lim, y=lim, mode="lines", line=dict(dash="dot", color=MUTED), name="perfect", showlegend=False)
        f.update_traces(selector=dict(mode="markers"), marker=dict(size=8, line=dict(width=1, color="white")))
        f.update_xaxes(title=f"Actual {LC}")
        f.update_yaxes(title="Predicted")
        chart(f, "Each dot is a state-disease pair. Dots on the dotted line were predicted perfectly; above = over-predicted, "
                 "below = under-predicted.", 460)

        fc = fr["forecast"]
        fy = int(fc["Forecast_Year"].iloc[0])
        section(f"🔮 {fy} forecast", "Forecast = median of 400 Random Forest trees, range = 10th–90th percentile")
        if fy == 2025:
            insight("⚠ PROVISIONAL INPUT", "These forecasts use the partial-year 2024 values as input, so they are likely too low "
                    "(especially Dengue). Switch the input year above to compare.", "warn")
        a, b = st.columns(2)
        with a: fd = st.selectbox("Disease", DISEASES, key="fc_d")
        with b: fs = st.selectbox("State", STATES, index=STATES.index("Kerala"), key="fc_s")
        hist = df[(df["Disease"] == fd) & (df["State"] == fs)]
        row = fc[(fc["Disease"] == fd) & (fc["State"] == fs)].iloc[0]
        f = go.Figure()
        f.add_scatter(x=hist["Year"], y=hist["Incidence_per_100k"], mode="lines+markers", name="Recorded",
                      line=dict(color=DISEASE_COLORS[fd], width=2.5), marker=dict(size=8))
        f.add_scatter(x=[fy], y=[row["Forecast"]], mode="markers", name="Forecast", marker=dict(size=12, color=PRIMARY, symbol="diamond"),
                      error_y=dict(type="data", symmetric=False, array=[row["High_P90"] - row["Forecast"]],
                                   arrayminus=[row["Forecast"] - row["Low_P10"]], color=ALERT, thickness=2))
        mark_provisional(f)
        f.update_xaxes(dtick=1)
        f.update_yaxes(title="Incidence per 100k")
        chart(f, f"Recorded {fd} incidence for {fs}, with the {fy} forecast (diamond) and its uncertainty range (coral bar). "
                 "A wide bar means the model's trees disagree a lot.", 400)
        st.dataframe(fc[fc["Disease"] == fd][["State", "Region", "Last_Complete_Value", "Last_Value", "Forecast", "Low_P10", "High_P90"]]
                     .rename(columns={"Last_Complete_Value": f"{LC} actual", "Last_Value": f"{fy - 1} input"})
                     .sort_values("Forecast", ascending=False).round(2), hide_index=True, height=360)

    with tC:
        with st.expander("📘 In plain English: Isolation Forest", expanded=True):
            st.write("An Isolation Forest builds many random decision trees that keep splitting the data. Unusual points get "
                     "separated (\"isolated\") in very few splits, so they receive a high anomaly score. Unlike the IQR rule, "
                     "it looks at **three things at once**: incidence (log scale), case fatality rate, and the change from the "
                     "previous year. Each disease is analysed separately and each feature is standardised.")
        cont = st.slider("Share of observations to flag (contamination)", .02, .10, .05, .01)
        iso = iforest_cached(cont)
        iso = iso[~iso["Provisional"]] if st.checkbox("Exclude provisional 2024", value=True, key="if_x") else iso
        ct = pd.crosstab(iso["IQR_Flag"], iso["IF_Flag"])
        both = int(((iso["IQR_Flag"] != "Normal") & (iso["IF_Flag"] == "Anomaly")).sum())
        c = st.columns(3)
        with c[0]: kpi("ISOLATION FOREST", f"{(iso['IF_Flag'] == 'Anomaly').sum()}", "flagged", "🌲")
        with c[1]: kpi("IQR RULE", f"{(iso['IQR_Flag'] != 'Normal').sum()}", "flagged (High + Low)", "📏")
        with c[2]: kpi("BOTH AGREE", f"{both}", "flagged by both", "🤝")
        l, r = st.columns([1.4, 1], gap="large")
        with l:
            section("Isolation Forest view", "Incidence vs change from last year")
            f = px.scatter(iso.assign(Disease=iso["Disease"].map(SHORT)), x="Log_Inc", y="YoY_log", color="IF_Flag",
                           symbol="IQR_Flag", facet_col="Disease", facet_col_wrap=3,
                           color_discrete_map={"Anomaly": ALERT, "Normal": "#B8C9C6"},
                           hover_data=["State", "Year", "Incidence_per_100k", "CFR"])
            f.update_traces(marker=dict(size=7, line=dict(width=.8, color="white")))
            f.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            chart(f, "Coral points are flagged by the Isolation Forest; marker shape shows the IQR rule's verdict. Points far "
                     "from the cloud (very high/low, or a sudden jump or drop) are flagged.", 560)
        with r:
            section("Agreement table", "Rows = IQR rule, columns = Isolation Forest")
            st.dataframe(ct, height=160)
            st.write("The two methods often disagree because they ask different questions: the IQR rule asks *was this year "
                     "unusual for this state?*, while the Isolation Forest asks *is this combination of level, fatality rate and "
                     "change unusual among all states?* — e.g. it also catches high case-fatality rates.")
        section("Top Isolation Forest anomalies")
        st.dataframe(iso[iso["IF_Flag"] == "Anomaly"].sort_values("IF_Score", ascending=False)[
            ["Disease", "State", "Year", "Incidence_per_100k", "CFR", "YoY_log", "IF_Score", "IQR_Flag"]].round(3),
            hide_index=True, height=380)

# ============================================================
# RESOURCE PRIORITY
# ============================================================

def page_priority():
    header("🎯 Resource Priority", "Where awareness and prevention efforts could help most: incidence that is high AND rising.")
    a, b = st.columns(2)
    with a: disease = st.selectbox("Disease", DISEASES, key="rp_d")
    with b: basis = st.radio("Measure 'high' by", ["Rate per 100k (risk per person)", "Total cases (people affected)"], horizontal=True)
    t = D.resource_priority(df, disease, basis="cases" if basis.startswith("Total") else "rate")
    nat = t["National_Level"].iloc[0]
    hr = t[t["Quadrant"] == "High & rising"]
    c = st.columns(3)
    with c[0]: kpi("HIGH & RISING", len(hr), f"states/UTs for {SHORT[disease]}", "🔺")
    with c[1]: kpi("NATIONAL LEVEL", f"{nat:.2f}", f"per 100k, {LC}, population-weighted", "◎")
    with c[2]: kpi("TOP PRIORITY", t.iloc[0]["State"], f"score {t.iloc[0]['Priority_Score']:.0f}/100", "🎯")
    qcol = {"High & rising": ALERT, "High & stable/falling": WARNING, "Low & rising": SECONDARY, "Low & stable/falling": "#B8C9C6"}
    section("Level × trend", f"{LC} incidence vs average yearly trend 2019–{LC}")
    f = px.scatter(t, x="Incidence_per_100k", y="Trend_%_per_year", color="Quadrant", hover_name="State", log_x=True,
                   size=np.sqrt(t["Population_Approx"]), size_max=34, color_discrete_map=qcol,
                   hover_data={"Cases": ":,.0f", "Priority_Score": ":.0f"})
    # Drawn as a trace (not add_vline) because shapes misplace on log axes.
    ylo, yhi = float(t["Trend_%_per_year"].min()), float(t["Trend_%_per_year"].max())
    f.add_scatter(x=[nat, nat], y=[ylo, yhi], mode="lines+text", text=["", "national level"], textposition="top right",
                  line=dict(dash="dot", color=MUTED, width=1.5), showlegend=False, hoverinfo="skip")
    f.add_hline(y=0, line_dash="dot", line_color=MUTED)
    f.update_xaxes(title=f"Incidence per 100k in {LC} (log)")
    f.update_yaxes(title="Trend (% per year)")
    chart(f, "Top-right (coral) states are above the national level AND rising — the priority group. Bubble size = population.", 500)
    l, r = st.columns([1.3, 1], gap="large")
    with l:
        section("Priority ranking", "Only rising states get a score")
        st.dataframe(t[["State", "Region", "Incidence_per_100k", "Cases", "Trend_%_per_year", "Quadrant", "Priority_Score"]]
                     .head(15).round(2), hide_index=True, height=460)
    with r:
        section("All diseases at once", "How many diseases are high & rising in each state")
        allq = pd.concat([D.resource_priority(df, d).assign(Disease=d) for d in DISEASES])
        cnt = allq[allq["Quadrant"] == "High & rising"].groupby("State").size().rename("Diseases").reset_index()
        chart(hbar(cnt.sort_values("Diseases", ascending=False).head(12), "Diseases", "State", "Number of diseases high & rising", 440, ".0f"),
              "States appearing for several diseases may benefit from combined campaigns (e.g. water safety + mosquito control).")
    insight("✦ METHOD", f"<b>High</b> = {LC} incidence above the population-weighted national level. <b>Rising</b> = positive "
            f"least-squares trend in log incidence over 2019–{LC} (2024 excluded as partial). Score = 60% percentile rank of the "
            "level (rate or cases) + 40% percentile rank of the trend; non-rising states score 0. The rate view favours small "
            "UTs (high risk per person); the cases view favours big states (many people affected). This is a planning aid for "
            "awareness work, not an official resource-allocation tool.")

# ============================================================
# PUBLIC HEALTH ADVISORY
# ============================================================

def advice_cards(d, sections=("spread", "symptoms", "prevention", "doctor")):
    titles = {"spread": "How it spreads", "symptoms": "Common symptoms", "prevention": "Prevention", "doctor": "When to see a doctor"}
    cols = st.columns(len(sections))
    for col, s in zip(cols, sections):
        with col:
            items = "".join(f"<li>{x}</li>" for x in ADVICE[d][s])
            st.markdown(f'<div class="tip"><h4>{titles[s]}</h4><ul>{items}</ul></div>', unsafe_allow_html=True)


def page_advisory():
    header("🩺 Public Health Advisory", "Plain-language awareness: how each disease spreads, what to look for and how to prevent it.")
    insight("ℹ NOT MEDICAL ADVICE", DISCLAIMER.replace("**", ""), "warn")
    tabs = st.tabs([f"{ADVICE[d]['icon']} {SHORT[d]}" for d in DISEASES])
    for tb, d in zip(tabs, DISEASES):
        with tb:
            advice_cards(d)
            st.markdown("**Official sources:** " + " · ".join(f"[{n}]({u})" for n, u in SOURCES[d]))
    section("📅 Seasonal risk calendar", "Indicative general pattern for India — NOT computed from this dataset (which has yearly totals only)")
    z = np.array([SEASONAL[d] for d in DISEASES])
    lab = np.array([["Lower", "Moderate", "Higher"][v] for v in z.ravel()]).reshape(z.shape)
    f = go.Figure(go.Heatmap(z=z, x=MONTHS, y=[SHORT[d] for d in DISEASES], text=lab, texttemplate="%{text}",
                             colorscale=[[0, "#F2F8F7"], [.5, "#93CBC2"], [1, PRIMARY]], showscale=False, xgap=2, ygap=2,
                             hovertemplate="%{y} · %{x}: %{text}<extra></extra>"))
    f.update_yaxes(autorange="reversed")
    chart(f, "Darker months are when each disease is commonly reported to be more frequent in India. Patterns differ by state "
             "and year; check your state health department's alerts.", 330)
    for d in DISEASES:
        st.markdown(f"- **{SHORT[d]}:** {SEASON_NOTE[d]}")

# ============================================================
# MY STATE
# ============================================================

def page_mystate():
    header("🧭 My State", "Everything about one state on one screen — and a report you can download and share.")
    state = st.selectbox("Choose your state / UT", STATES, index=STATES.index("Maharashtra"), key="ms_s")
    cl = clusters_cached()["assignments"]
    fr = forecast_cached(None)
    mb = fr["metrics"]
    base = mb.loc[mb["Model"].str.startswith("Naive"), "MAE"].iloc[0]
    rf = mb.loc[mb["Model"] == "Random Forest", "MAE"].iloc[0]
    note = (f"On the {LC} test the naive 'same as last year' baseline (MAE {base:.2f}) was more accurate than the Random Forest "
            f"(MAE {rf:.2f}), so forecasts are indicative only." if rf >= base else
            f"On the {LC} test the Random Forest (MAE {rf:.2f}) beat the naive baseline (MAE {base:.2f}).")
    s = state_summary(df, state, cl, fr["forecast"], slopes_cached(), note)
    c = st.columns(4)
    with c[0]: kpi("RISK CLUSTER", s["cluster"], "K-Means group", "🧩")
    with c[1]: kpi("RISING DISEASES", len(s["rising"]), f"trend 2019–{LC}", "📈")
    with c[2]: kpi("REGION", s["region"], "", "📍")
    with c[3]: kpi("POPULATION", f"{s['population'] / 1e5:,.1f} lakh", "approximate", "👥")
    tbl = pd.DataFrame(s["rows"])
    l, r = st.columns([1.15, 1], gap="large")
    with l:
        section(f"Latest year vs {s['forecast_year']} forecast", "Forecast = median of Random Forest trees, range = 10th–90th percentile")
        f = go.Figure()
        f.add_bar(y=tbl["Disease"].map(SHORT), x=tbl[f"{LC} incidence"], orientation="h", name=f"{LC} actual", marker_color="#93CBC2")
        f.add_bar(y=tbl["Disease"].map(SHORT), x=tbl["Forecast"], orientation="h", name=f"{s['forecast_year']} forecast",
                  marker_color=PRIMARY, error_x=dict(type="data", symmetric=False, array=tbl["Range high"] - tbl["Forecast"],
                                                     arrayminus=tbl["Forecast"] - tbl["Range low"], color=ALERT))
        f.update_layout(barmode="group", legend=dict(orientation="h", y=1.08, x=0))
        f.update_xaxes(type="log", title="Incidence per 100k (log)")
        chart(f, f"Light bars: what was recorded in {LC}. Dark bars: the model's {s['forecast_year']} forecast with its range. "
                 + note + (" The 2025 forecast uses partial-year 2024 input and is likely too low." if s["forecast_year"] == 2025 else ""), 380)
    with r:
        section("Trend by disease")
        for row in s["rows"]:
            st.markdown(f"**{SHORT[row['Disease']]}** &nbsp; {badge(row['Trend %/yr (2019–23)'])} per year", unsafe_allow_html=True)
    section("What you can do", "Prevention tips for the diseases rising in this state" if s["rising"] else "Prevention tips")
    for d in (s["rising"] or DISEASES)[:2]:
        st.markdown(f"**{ADVICE[d]['icon']} {d}**")
        advice_cards(d, ("prevention", "doctor"))
    st.caption(DISCLAIMER.replace("**", ""))
    section("⬇️ Download a shareable report")
    d1, d2 = st.columns(2)
    with d1: st.download_button("📄 PDF report", build_pdf(s), f"DiseaseScope_{state.replace(' ', '_')}.pdf", "application/pdf")
    with d2: st.download_button("🌐 HTML report", build_html(s), f"DiseaseScope_{state.replace(' ', '_')}.html", "text/html")

# ============================================================
# DATA QUALITY
# ============================================================

def page_quality():
    header("🧹 Data Quality", "Exactly what was in the raw file and what was cleaned before analysis.")
    num = [c for c in raw.columns if pd.api.types.is_numeric_dtype(raw[c]) and raw[c].dtype != bool]
    cat = [c for c in raw.columns if c not in num]
    k = st.columns(4)
    with k[0]: kpi("ROWS", f"{len(raw):,}", "records", "▤")
    with k[1]: kpi("COLUMNS", raw.shape[1], f"{len(num)} numerical · {len(cat)} non-numerical", "◫")
    with k[2]: kpi("MISSING CELLS (RAW)", int(raw.isna().sum().sum()), f"in {int(raw.isna().any(axis=1).sum())} rows", "⚠️")
    with k[3]: kpi("IMPUTED ROWS", int(df["Imputed"].sum()), "incidence filled", "✓")
    l, r = st.columns(2, gap="large")
    with l:
        section("Missing values: raw vs cleaned")
        miss = pd.DataFrame({"Raw": raw.isna().sum(), "Cleaned": df[raw.columns].isna().sum()}).reset_index(names="Column")
        miss = miss[miss["Raw"] > 0].melt(id_vars="Column", var_name="Stage", value_name="Missing")
        f = px.bar(miss, x="Missing", y="Column", color="Stage", barmode="group", orientation="h",
                   color_discrete_map={"Raw": WARNING, "Cleaned": SECONDARY})
        f.update_yaxes(title="")
        chart(f, "Amber = missing in the original file, teal = still missing after cleaning. The 7 remaining CFR gaps are rows with "
                 "zero cases, where a fatality rate cannot be calculated.", 340)
    with r:
        section("Schema")
        prof = pd.DataFrame({"Column": raw.columns, "Type": ["numerical" if c in num else "non-numerical" for c in raw.columns],
                             "dtype": [str(raw[c].dtype) for c in raw.columns], "Missing (raw)": raw.isna().sum().values,
                             "Unique": [raw[c].nunique() for c in raw.columns]})
        st.dataframe(prof, hide_index=True, height=420)
    st.caption(D.DATA_SOURCE_NOTE)
    insight("✦ PREPROCESSING LOG", "1) Numeric columns coerced; text trimmed. 2) Missing incidence (25 rows) filled by linear "
            "interpolation across years within the same state and disease (median of the disease if a state had no values). "
            "3) For those rows Cases, % affected and Deaths were re-derived from the filled incidence (Deaths via the state's "
            "median CFR). 4) CFR recomputed where Cases > 0. 5) Rows flagged <b>Imputed</b> and excluded from anomaly detection. "
            "Previously, missing incidence was filled with one national median per disease, which ignored big state differences.")
    section("Imputed rows")
    st.dataframe(df[df["Imputed"]][["Disease", "State", "Year", "Incidence_per_100k", "Cases", "Deaths"]].round(2), hide_index=True, height=300)
    section("Numerical summary (cleaned)")
    st.dataframe(df[D.NUMERIC_COLS].describe().T.round(2))
    st.download_button("⬇️ Download cleaned dataset (CSV)", df.to_csv(index=False).encode(), "diseasescope_cleaned.csv", "text/csv")


ROUTES = {"🏠 Overview": page_overview, "🧭 My State": page_mystate, "🦠 Disease Explorer": page_disease,
          "📈 Regional Trends": page_regional, "🗺️ State Explorer": page_state, "🔎 Compare Diseases": page_compare,
          "🚨 Anomaly Radar": page_anomaly, "🧠 Intelligence Lab": page_lab, "🤖 ML Insights": page_ml,
          "🎯 Resource Priority": page_priority, "🩺 Public Health Advisory": page_advisory, "🧹 Data Quality": page_quality}
ROUTES[page]()

st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:11px;margin-top:40px;padding-top:14px;border-top:1px solid #D5E5E2">'
            'DiseaseScope · India disease incidence 2019–2024 · Not medical advice</div>',
            unsafe_allow_html=True)
