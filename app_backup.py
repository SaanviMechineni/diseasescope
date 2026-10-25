import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DiseaseScope",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(124, 58, 237, 0.13),
            transparent 25%
        ),
        radial-gradient(
            circle at 5% 30%,
            rgba(6, 182, 212, 0.08),
            transparent 25%
        ),
        #080b12;
    color: #f8fafc;
}

/* Main content width */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0b0f18;
    border-right: 1px solid rgba(148, 163, 184, 0.12);
}

section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}

/* Sidebar text */
.sidebar-brand {
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 4px;
}

.sidebar-subtitle {
    color: #94a3b8;
    font-size: 12px;
    margin-bottom: 25px;
}

/* Hero */
.hero {
    padding: 10px 0 25px 0;
}

.hero-label {
    color: #a78bfa;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.hero-title {
    font-size: 48px;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1.05;
    margin: 0;
}

.hero-title span {
    background: linear-gradient(
        90deg,
        #c084fc,
        #22d3ee
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-description {
    color: #94a3b8;
    font-size: 16px;
    max-width: 700px;
    line-height: 1.6;
    margin-top: 14px;
}

/* KPI cards */
.metric-card {
    background: linear-gradient(
        145deg,
        rgba(30, 41, 59, 0.72),
        rgba(15, 23, 42, 0.72)
    );
    border: 1px solid rgba(148, 163, 184, 0.13);
    border-radius: 18px;
    padding: 20px 22px;
    min-height: 125px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.18);
}

.metric-label {
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 12px;
}

.metric-value {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -1px;
}

.metric-icon {
    font-size: 20px;
    float: right;
}

/* Section headings */
.section-title {
    font-size: 23px;
    font-weight: 750;
    margin-top: 15px;
    margin-bottom: 5px;
}

.section-caption {
    color: #64748b;
    font-size: 13px;
    margin-bottom: 15px;
}

/* Chart cards */
.chart-card {
    background: rgba(15, 23, 42, 0.60);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 18px;
    padding: 8px;
}

/* Insight card */
.insight-card {
    background:
        linear-gradient(
            135deg,
            rgba(124, 58, 237, 0.16),
            rgba(6, 182, 212, 0.08)
        );
    border: 1px solid rgba(167, 139, 250, 0.18);
    border-radius: 18px;
    padding: 22px;
    margin-top: 10px;
}

.insight-title {
    font-size: 14px;
    color: #a78bfa;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.insight-text {
    font-size: 17px;
    line-height: 1.6;
    margin-top: 8px;
}

/* Hide Streamlit branding */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid rgba(167, 139, 250, 0.35);
    background: rgba(124, 58, 237, 0.15);
    color: #e9d5ff;
    font-weight: 600;
}

.stButton > button:hover {
    border-color: #a78bfa;
    background: rgba(124, 58, 237, 0.28);
}

/* Select boxes */
div[data-baseweb="select"] > div {
    background-color: #111827;
    border-color: rgba(148, 163, 184, 0.18);
    border-radius: 10px;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

file_path = "data/india_5_diseases_enriched.xlsx"

df = pd.read_excel(
    file_path,
    sheet_name="All Diseases (combined)"
)

# ============================================================
# DATA CLEANING
# ============================================================

missing_before = df["Incidence_per_100k"].isna().sum()

df["Incidence_per_100k"] = (
    df.groupby("Disease")["Incidence_per_100k"]
    .transform(
        lambda x: x.fillna(x.median())
    )
)

missing_after = df["Incidence_per_100k"].isna().sum()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-brand">🩺 DiseaseScope</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">'
        'Disease Incidence Intelligence'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### EXPLORE")

    page = st.radio(
        "Navigation",
        [
            "🏠 Overview",
            "🦠 Disease Explorer",
            "📈 Regional Trends",
            "🗺️ State Explorer",
            "🔎 Compare Diseases",
            "🚨 Anomalies",
            "🧹 Data Quality"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("DATASET")
    st.caption("India • 2019–2024")
    st.caption("5 diseases • 36 states/UTs")


# ============================================================
# HERO
# ============================================================

st.markdown("""
<div class="hero">

<div class="hero-label">
INDIA • DISEASE INTELLIGENCE
</div>

<div class="hero-title">
Understand the <span>pulse</span> of disease incidence.
</div>

<div class="hero-description">
DiseaseScope transforms disease incidence data into interactive
visual insights across diseases, states, regions and years.
</div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📊</div>
        <div class="metric-label">TOTAL RECORDS</div>
        <div class="metric-value">{len(df):,}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🦠</div>
        <div class="metric-label">DISEASES</div>
        <div class="metric-value">{df["Disease"].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🗺️</div>
        <div class="metric-label">STATES / UTs</div>
        <div class="metric-value">{df["State"].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🌎</div>
        <div class="metric-label">REGIONS</div>
        <div class="metric-value">{df["Region"].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# OVERVIEW
# ============================================================

if page == "🏠 Overview":

    st.markdown(
        '<div class="section-title">Disease Overview</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Average incidence across the complete dataset'
        '</div>',
        unsafe_allow_html=True
    )

    disease_mean = (
        df.groupby("Disease")["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    disease_mean["Incidence_per_100k"] = (
        disease_mean["Incidence_per_100k"].round(2)
    )

    fig = px.bar(
        disease_mean,
        x="Disease",
        y="Incidence_per_100k",
        text="Incidence_per_100k",
        color="Disease",
        color_discrete_sequence=[
            "#8b5cf6",
            "#22d3ee",
            "#3b82f6",
            "#a78bfa",
            "#06b6d4"
        ]
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Mean incidence: %{y:.2f} / 100k"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=470,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        xaxis=dict(
            showgrid=False
        ),
        yaxis=dict(
            title="Incidence per 100,000",
            gridcolor="rgba(148,163,184,0.10)"
        ),
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ========================================================
    # QUICK INSIGHT
    # ========================================================

    highest = disease_mean.loc[
        disease_mean["Incidence_per_100k"].idxmax()
    ]

    lowest = disease_mean.loc[
        disease_mean["Incidence_per_100k"].idxmin()
    ]

    st.markdown(f"""
    <div class="insight-card">

    <div class="insight-title">
    ✦ DATASET INSIGHT
    </div>

    <div class="insight-text">
    <b>{highest["Disease"]}</b> has the highest mean incidence
    in the dataset at
    <b>{highest["Incidence_per_100k"]:.2f}</b> cases per 100,000,
    while <b>{lowest["Disease"]}</b> has the lowest mean incidence
    at <b>{lowest["Incidence_per_100k"]:.2f}</b>.
    </div>

    </div>
    """, unsafe_allow_html=True)


    # ========================================================
    # RECENT DATA
    # ========================================================

    st.markdown(
        '<div class="section-title">Dataset Snapshot</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'A preview of the underlying disease records'
        '</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        df.head(10),
        use_container_width=True,
        hide_index=True
    )
    # ============================================================
# DISEASE EXPLORER
# ============================================================

elif page == "🦠 Disease Explorer":

    st.markdown(
        '<div class="section-title">Disease Explorer</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Explore incidence patterns for a selected disease, '
        'region and year.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    filter1, filter2, filter3 = st.columns(3)

    with filter1:

        selected_disease = st.selectbox(
            "Disease",
            sorted(df["Disease"].unique())
        )

    with filter2:

        region_options = ["All Regions"] + sorted(
            df["Region"].unique().tolist()
        )

        selected_region = st.selectbox(
            "Region",
            region_options
        )

    with filter3:

        selected_year = st.selectbox(
            "Year",
            sorted(df["Year"].unique()),
            index=len(df["Year"].unique()) - 1
        )

    # --------------------------------------------------------
    # FILTER DATA
    # --------------------------------------------------------

    explorer_data = df[
        df["Disease"] == selected_disease
    ].copy()

    if selected_region != "All Regions":

        explorer_data = explorer_data[
            explorer_data["Region"] == selected_region
        ]

    # --------------------------------------------------------
    # KPI CALCULATIONS
    # --------------------------------------------------------

    mean_incidence = explorer_data[
        "Incidence_per_100k"
    ].mean()

    total_cases = explorer_data[
        explorer_data["Year"] == selected_year
    ]["Cases"].sum()

    total_deaths = explorer_data[
        explorer_data["Year"] == selected_year
    ]["Deaths"].sum()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    k1, k2, k3 = st.columns(3)

    with k1:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        MEAN INCIDENCE
        </div>

        <div class="metric-value">
        {mean_incidence:.2f}
        </div>

        <div style="color:#64748b;font-size:12px;">
        per 100,000 population
        </div>

        </div>
        """, unsafe_allow_html=True)

    with k2:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        TOTAL CASES
        </div>

        <div class="metric-value">
        {total_cases:,.0f}
        </div>

        <div style="color:#64748b;font-size:12px;">
        {selected_year}
        </div>

        </div>
        """, unsafe_allow_html=True)

    with k3:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        TOTAL DEATHS
        </div>

        <div class="metric-value">
        {total_deaths:,.0f}
        </div>

        <div style="color:#64748b;font-size:12px;">
        {selected_year}
        </div>

        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --------------------------------------------------------
    # TREND DATA
    # --------------------------------------------------------

    trend_data = (
        explorer_data
        .groupby("Year")["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    # --------------------------------------------------------
    # TREND CHART
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📈 Incidence Trend</div>',
        unsafe_allow_html=True
    )

    trend_fig = px.line(
        trend_data,
        x="Year",
        y="Incidence_per_100k",
        markers=True,
        title=f"{selected_disease} — Incidence Trend"
    )

    trend_fig.update_traces(
        line=dict(
            color="#a78bfa",
            width=4
        ),
        marker=dict(
            size=9,
            color="#22d3ee"
        ),
        hovertemplate=(
            "<b>Year:</b> %{x}<br>"
            "<b>Incidence:</b> %{y:.2f} / 100k"
            "<extra></extra>"
        )
    )

    trend_fig.update_layout(
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        xaxis=dict(
            dtick=1,
            showgrid=False
        ),
        yaxis=dict(
            title="Incidence per 100,000",
            gridcolor="rgba(148,163,184,0.10)"
        )
    )

    st.plotly_chart(
        trend_fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # STATE DISTRIBUTION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🗺️ State Distribution</div>',
        unsafe_allow_html=True
    )

    state_data = (
        explorer_data[
            explorer_data["Year"] == selected_year
        ]
        .groupby("State")["Incidence_per_100k"]
        .mean()
        .reset_index()
        .sort_values(
            "Incidence_per_100k",
            ascending=False
        )
    )

    state_fig = px.bar(
        state_data,
        x="Incidence_per_100k",
        y="State",
        orientation="h",
        color="Incidence_per_100k",
        color_continuous_scale=[
            "#312e81",
            "#7c3aed",
            "#22d3ee"
        ],
        title=(
            f"{selected_disease} incidence by state "
            f"— {selected_year}"
        )
    )

    state_fig.update_layout(
        height=700,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        coloraxis_showscale=False,
        xaxis=dict(
            title="Incidence per 100,000",
            gridcolor="rgba(148,163,184,0.10)"
        ),
        yaxis=dict(
            title=""
        )
    )

    st.plotly_chart(
        state_fig,
        use_container_width=True
    )
     # ============================================================
# REGIONAL TRENDS
# ============================================================
elif page == "📈 Regional Trends":

    st.markdown(
        '<div class="section-title">Regional Trends</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Track how disease incidence changes across '
        'India\'s regions over time.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    f1, f2 = st.columns(2)

    with f1:

        selected_disease = st.selectbox(
            "Select Disease",
            sorted(df["Disease"].unique()),
            key="regional_disease"
        )

    with f2:

        selected_regions = st.multiselect(
            "Select Regions",
            sorted(df["Region"].unique()),
            default=sorted(df["Region"].unique()),
            key="regional_regions"
        )

    # --------------------------------------------------------
    # FILTER DATA
    # --------------------------------------------------------

    regional_data = df[
        df["Disease"] == selected_disease
    ].copy()

    if selected_regions:

        regional_data = regional_data[
            regional_data["Region"].isin(selected_regions)
        ]

    # --------------------------------------------------------
    # REGIONAL SUMMARY
    # --------------------------------------------------------

    regional_summary = (
        regional_data
        .groupby(
            ["Region", "Year"]
        )["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    # --------------------------------------------------------
    # MAIN TREND CHART
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📈 Incidence by Region</div>',
        unsafe_allow_html=True
    )

    regional_fig = px.line(
        regional_summary,
        x="Year",
        y="Incidence_per_100k",
        color="Region",
        markers=True,
        title=f"{selected_disease} — Regional Incidence Trends"
    )

    regional_fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate=(
            "<b>Region:</b> %{fullData.name}<br>"
            "<b>Year:</b> %{x}<br>"
            "<b>Incidence:</b> %{y:.2f} / 100k"
            "<extra></extra>"
        )
    )

    regional_fig.update_layout(
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        legend=dict(
            title="Region",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        xaxis=dict(
            dtick=1,
            showgrid=False,
            title="Year"
        ),
        yaxis=dict(
            title="Mean Incidence per 100,000",
            gridcolor="rgba(148,163,184,0.10)"
        )
    )

    st.plotly_chart(
        regional_fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # REGIONAL SUMMARY TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📊 Regional Summary</div>',
        unsafe_allow_html=True
    )

    regional_table = (
        regional_data
        .groupby("Region")
        .agg(
            Mean_Incidence=(
                "Incidence_per_100k",
                "mean"
            ),
            Total_Cases=(
                "Cases",
                "sum"
            ),
            Total_Deaths=(
                "Deaths",
                "sum"
            )
        )
        .reset_index()
    )

    regional_table["Mean_Incidence"] = (
        regional_table["Mean_Incidence"].round(2)
    )

    regional_table = regional_table.sort_values(
        "Mean_Incidence",
        ascending=False
    )

    st.dataframe(
        regional_table,
        use_container_width=True,
        hide_index=True
    )
    # ============================================================
# STATE EXPLORER
# ============================================================

elif page == "🗺️ State Explorer":

    st.markdown(
        '<div class="section-title">State Explorer</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Explore the disease profile and incidence patterns '
        'of an individual Indian state or union territory.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # STATE SELECTION
    # --------------------------------------------------------

    selected_state = st.selectbox(
        "Select State / Union Territory",
        sorted(df["State"].unique()),
        key="state_explorer"
    )

    state_data = df[
        df["State"] == selected_state
    ].copy()

    # --------------------------------------------------------
    # STATE KPIs
    # --------------------------------------------------------

    state_mean = state_data[
        "Incidence_per_100k"
    ].mean()

    state_cases = state_data["Cases"].sum()

    state_deaths = state_data["Deaths"].sum()

    highest_disease = (
        state_data
        .groupby("Disease")["Incidence_per_100k"]
        .mean()
        .idxmax()
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        MEAN INCIDENCE
        </div>

        <div class="metric-value">
        {state_mean:.2f}
        </div>

        <div style="color:#64748b;font-size:12px;">
        per 100,000
        </div>

        </div>
        """, unsafe_allow_html=True)

    with k2:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        TOTAL CASES
        </div>

        <div class="metric-value">
        {state_cases:,.0f}
        </div>

        </div>
        """, unsafe_allow_html=True)

    with k3:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        TOTAL DEATHS
        </div>

        <div class="metric-value">
        {state_deaths:,.0f}
        </div>

        </div>
        """, unsafe_allow_html=True)

    with k4:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        MOST PREVALENT DISEASE
        </div>

        <div style="
            font-size:17px;
            font-weight:700;
            margin-top:10px;
        ">
        {highest_disease}
        </div>

        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --------------------------------------------------------
    # YEARLY INCIDENCE TREND
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📈 Incidence Trend</div>',
        unsafe_allow_html=True
    )

    state_yearly = (
        state_data
        .groupby("Year")["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    state_trend = px.area(
        state_yearly,
        x="Year",
        y="Incidence_per_100k",
        markers=True,
        title=f"{selected_state} — Overall Incidence Trend"
    )

    state_trend.update_traces(
        line=dict(
            color="#8b5cf6",
            width=3
        ),
        marker=dict(
            size=8,
            color="#22d3ee"
        ),
        fillcolor="rgba(139,92,246,0.15)",
        hovertemplate=(
            "<b>Year:</b> %{x}<br>"
            "<b>Mean incidence:</b> %{y:.2f}"
            "<extra></extra>"
        )
    )

    state_trend.update_layout(
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        xaxis=dict(
            dtick=1,
            showgrid=False
        ),
        yaxis=dict(
            title="Mean Incidence per 100,000",
            gridcolor="rgba(148,163,184,0.10)"
        )
    )

    st.plotly_chart(
        state_trend,
        use_container_width=True
    )

    # --------------------------------------------------------
    # DISEASE COMPARISON
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🦠 Disease Profile</div>',
        unsafe_allow_html=True
    )

    disease_profile = (
        state_data
        .groupby("Disease")["Incidence_per_100k"]
        .mean()
        .reset_index()
        .sort_values(
            "Incidence_per_100k",
            ascending=True
        )
    )

    disease_fig = px.bar(
        disease_profile,
        x="Incidence_per_100k",
        y="Disease",
        orientation="h",
        color="Incidence_per_100k",
        color_continuous_scale=[
            "#312e81",
            "#7c3aed",
            "#22d3ee"
        ],
        title=f"Disease incidence profile — {selected_state}"
    )

    disease_fig.update_layout(
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        coloraxis_showscale=False,
        xaxis=dict(
            title="Mean Incidence per 100,000",
            gridcolor="rgba(148,163,184,0.10)"
        ),
        yaxis=dict(title="")
    )

    st.plotly_chart(
        disease_fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # STATE DATA TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📋 State Records</div>',
        unsafe_allow_html=True
    )

    state_table = state_data[
        [
            "Disease",
            "Region",
            "Year",
            "Cases",
            "Deaths",
            "Incidence_per_100k"
        ]
    ].copy()

    state_table["Incidence_per_100k"] = (
        state_table["Incidence_per_100k"].round(2)
    )

    st.dataframe(
        state_table,
        use_container_width=True,
        hide_index=True
    )
    # ============================================================
# COMPARE DISEASES
# ============================================================

elif page == "🔎 Compare Diseases":

    st.markdown(
        '<div class="section-title">Compare Diseases</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Compare incidence patterns of multiple diseases '
        'across the same time period.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DISEASE SELECTION
    # --------------------------------------------------------

    all_diseases = sorted(df["Disease"].unique())

    selected_diseases = st.multiselect(
        "Select diseases to compare",
        all_diseases,
        default=all_diseases[:3],
        max_selections=5,
        key="compare_diseases"
    )

    if not selected_diseases:

        st.info(
            "Select at least one disease to display the comparison."
        )

    else:

        compare_data = df[
            df["Disease"].isin(selected_diseases)
        ].copy()

        # ----------------------------------------------------
        # YEARLY COMPARISON
        # ----------------------------------------------------

        comparison = (
            compare_data
            .groupby(
                ["Disease", "Year"]
            )["Incidence_per_100k"]
            .mean()
            .reset_index()
        )

        # ----------------------------------------------------
        # LINE CHART
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">'
            '📈 Incidence Comparison'
            '</div>',
            unsafe_allow_html=True
        )

        compare_fig = px.line(
            comparison,
            x="Year",
            y="Incidence_per_100k",
            color="Disease",
            markers=True,
            title="Disease Incidence — 2019 to 2024"
        )

        compare_fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate=(
                "<b>Disease:</b> %{fullData.name}<br>"
                "<b>Year:</b> %{x}<br>"
                "<b>Incidence:</b> %{y:.2f} / 100k"
                "<extra></extra>"
            )
        )

        compare_fig.update_layout(
            height=500,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
            legend=dict(
                title="Disease",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0
            ),
            xaxis=dict(
                dtick=1,
                showgrid=False,
                title="Year"
            ),
            yaxis=dict(
                title="Mean Incidence per 100,000",
                gridcolor="rgba(148,163,184,0.10)"
            )
        )

        st.plotly_chart(
            compare_fig,
            use_container_width=True
        )

        # ----------------------------------------------------
        # COMPARISON BAR CHART
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">'
            '📊 Average Incidence Comparison'
            '</div>',
            unsafe_allow_html=True
        )

        comparison_mean = (
            compare_data
            .groupby("Disease")["Incidence_per_100k"]
            .mean()
            .reset_index()
        )

        comparison_mean[
            "Incidence_per_100k"
        ] = comparison_mean[
            "Incidence_per_100k"
        ].round(2)

        bar_fig = px.bar(
            comparison_mean,
            x="Disease",
            y="Incidence_per_100k",
            color="Disease",
            text="Incidence_per_100k",
            title="Mean Incidence Across Selected Diseases"
        )

        bar_fig.update_traces(
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Mean incidence: %{y:.2f} / 100k"
                "<extra></extra>"
            )
        )

        bar_fig.update_layout(
            height=450,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
            xaxis=dict(
                showgrid=False,
                title=""
            ),
            yaxis=dict(
                title="Mean Incidence per 100,000",
                gridcolor="rgba(148,163,184,0.10)"
            )
        )

        st.plotly_chart(
            bar_fig,
            use_container_width=True
        )

        # ----------------------------------------------------
        # COMPARISON TABLE
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">'
            '📋 Comparison Summary'
            '</div>',
            unsafe_allow_html=True
        )

        summary = (
            compare_data
            .groupby("Disease")
            .agg(
                Mean_Incidence=(
                    "Incidence_per_100k",
                    "mean"
                ),
                Total_Cases=(
                    "Cases",
                    "sum"
                ),
                Total_Deaths=(
                    "Deaths",
                    "sum"
                )
            )
            .reset_index()
        )

        summary["Mean_Incidence"] = (
            summary["Mean_Incidence"].round(2)
        )

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )
        # ============================================================
# ANOMALY INTELLIGENCE
# ============================================================

elif page == "🚨 Anomalies":

    st.markdown(
        '<div class="section-title">Anomaly Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Automatically identify unusually high or low disease '
        'incidence observations using the Interquartile Range (IQR) method.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # CALCULATE IQR THRESHOLDS BY DISEASE
    # --------------------------------------------------------

    anomaly_df = df.copy()

    q1 = (
        anomaly_df
        .groupby("Disease")["Incidence_per_100k"]
        .transform("quantile", 0.25)
    )

    q3 = (
        anomaly_df
        .groupby("Disease")["Incidence_per_100k"]
        .transform("quantile", 0.75)
    )

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    anomaly_df["Anomaly"] = np.where(
        anomaly_df["Incidence_per_100k"] > upper_bound,
        "High",
        np.where(
            anomaly_df["Incidence_per_100k"] < lower_bound,
            "Low",
            "Normal"
        )
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_anomalies = (
        anomaly_df["Anomaly"] != "Normal"
    ).sum()

    high_anomalies = (
        anomaly_df["Anomaly"] == "High"
    ).sum()

    low_anomalies = (
        anomaly_df["Anomaly"] == "Low"
    ).sum()

    a1, a2, a3 = st.columns(3)

    with a1:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        UNUSUAL OBSERVATIONS
        </div>

        <div class="metric-value">
        {total_anomalies:,}
        </div>

        <div style="color:#64748b;font-size:12px;">
        detected using IQR
        </div>

        </div>
        """, unsafe_allow_html=True)

    with a2:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        HIGH INCIDENCE
        </div>

        <div class="metric-value">
        {high_anomalies:,}
        </div>

        <div style="color:#64748b;font-size:12px;">
        above upper IQR threshold
        </div>

        </div>
        """, unsafe_allow_html=True)

    with a3:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        LOW INCIDENCE
        </div>

        <div class="metric-value">
        {low_anomalies:,}
        </div>

        <div style="color:#64748b;font-size:12px;">
        below lower IQR threshold
        </div>

        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --------------------------------------------------------
    # DISEASE FILTER
    # --------------------------------------------------------

    selected_anomaly_disease = st.selectbox(
        "Filter by Disease",
        ["All Diseases"] +
        sorted(anomaly_df["Disease"].unique()),
        key="anomaly_disease"
    )

    if selected_anomaly_disease != "All Diseases":

        display_anomalies = anomaly_df[
            anomaly_df["Disease"] == selected_anomaly_disease
        ].copy()

    else:

        display_anomalies = anomaly_df.copy()

    display_anomalies = display_anomalies[
        display_anomalies["Anomaly"] != "Normal"
    ].copy()

    # --------------------------------------------------------
    # ANOMALY DISTRIBUTION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📊 Unusual Observation Distribution</div>',
        unsafe_allow_html=True
    )

    anomaly_counts = (
        anomaly_df[
            anomaly_df["Anomaly"] != "Normal"
        ]
        .groupby(
            ["Disease", "Anomaly"]
        )
        .size()
        .reset_index(name="Count")
    )

    anomaly_fig = px.bar(
        anomaly_counts,
        x="Disease",
        y="Count",
        color="Anomaly",
        barmode="group",
        color_discrete_map={
            "High": "#f43f5e",
            "Low": "#22d3ee"
        },
        title="High vs Low Incidence Observations"
    )

    anomaly_fig.update_layout(
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        xaxis=dict(
            showgrid=False
        ),
        yaxis=dict(
            title="Number of observations",
            gridcolor="rgba(148,163,184,0.10)"
        )
    )

    st.plotly_chart(
        anomaly_fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # ANOMALY TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🚨 Detected Observations</div>',
        unsafe_allow_html=True
    )

    anomaly_table = display_anomalies[
        [
            "Disease",
            "State",
            "Region",
            "Year",
            "Cases",
            "Deaths",
            "Incidence_per_100k",
            "Anomaly"
        ]
    ].sort_values(
        "Incidence_per_100k",
        ascending=False
    )

    anomaly_table["Incidence_per_100k"] = (
        anomaly_table["Incidence_per_100k"].round(2)
    )

    st.dataframe(
        anomaly_table,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # METHODOLOGY
    # --------------------------------------------------------

    st.markdown(f"""
    <div class="insight-card">

    <div class="insight-title">
    ✦ HOW ANOMALIES ARE DETECTED
    </div>

    <div class="insight-text">

    For each disease, DiseaseScope calculates the first quartile
    (Q1), third quartile (Q3), and interquartile range (IQR).

    <br><br>

    <b>Upper threshold</b> = Q3 + 1.5 × IQR

    <br>

    <b>Lower threshold</b> = Q1 − 1.5 × IQR

    <br><br>

    Observations outside these thresholds are flagged as
    <b>unusually high</b> or <b>unusually low</b> incidence
    observations.

    </div>

    </div>
    """, unsafe_allow_html=True)
    # ============================================================
# DATA QUALITY
# ============================================================

elif page == "🧹 Data Quality":

    st.markdown(
        '<div class="section-title">Data Quality Center</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Inspect missing values and the preprocessing performed '
        'before analysis.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DATA QUALITY METRICS
    # --------------------------------------------------------

    total_cells = df.shape[0] * df.shape[1]

    missing_total = df.isna().sum().sum()

    complete_cells = total_cells - missing_total

    completeness = (
        complete_cells / total_cells
    ) * 100

    q1_missing = missing_before
    q3_missing = missing_after

    d1, d2, d3, d4 = st.columns(4)

    with d1:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        TOTAL ROWS
        </div>

        <div class="metric-value">
        {df.shape[0]:,}
        </div>

        </div>
        """, unsafe_allow_html=True)

    with d2:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        TOTAL COLUMNS
        </div>

        <div class="metric-value">
        {df.shape[1]}
        </div>

        </div>
        """, unsafe_allow_html=True)

    with d3:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        INCIDENCE MISSING
        </div>

        <div class="metric-value">
        {q1_missing}
        </div>

        <div style="color:#64748b;font-size:12px;">
        before imputation
        </div>

        </div>
        """, unsafe_allow_html=True)

    with d4:

        st.markdown(f"""
        <div class="metric-card">

        <div class="metric-label">
        INCIDENCE MISSING
        </div>

        <div class="metric-value">
        {q3_missing}
        </div>

        <div style="color:#22d3ee;font-size:12px;">
        after imputation
        </div>

        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # --------------------------------------------------------
    # BEFORE / AFTER VISUALIZATION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🧹 Imputation Impact</div>',
        unsafe_allow_html=True
    )

    quality_data = pd.DataFrame({
        "Stage": [
            "Before Imputation",
            "After Imputation"
        ],
        "Missing Values": [
            q1_missing,
            q3_missing
        ]
    })

    quality_fig = px.bar(
        quality_data,
        x="Stage",
        y="Missing Values",
        text="Missing Values",
        color="Stage",
        color_discrete_sequence=[
            "#f43f5e",
            "#22d3ee"
        ],
        title="Missing Incidence Values — Before vs After"
    )

    quality_fig.update_traces(
        textposition="outside"
    )

    quality_fig.update_layout(
        height=400,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        xaxis=dict(
            showgrid=False
        ),
        yaxis=dict(
            title="Number of Missing Values",
            gridcolor="rgba(148,163,184,0.10)"
        )
    )

    st.plotly_chart(
        quality_fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # MISSING VALUES BY COLUMN
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">📋 Missing Values by Column</div>',
        unsafe_allow_html=True
    )

    missing_by_column = (
        df.isna()
        .sum()
        .reset_index()
    )

    missing_by_column.columns = [
        "Column",
        "Missing_Values"
    ]

    missing_by_column = missing_by_column[
        missing_by_column["Missing_Values"] > 0
    ]

    if len(missing_by_column) > 0:

        missing_fig = px.bar(
            missing_by_column,
            x="Column",
            y="Missing_Values",
            text="Missing_Values",
            color="Missing_Values",
            color_continuous_scale=[
                "#312e81",
                "#7c3aed",
                "#f43f5e"
            ],
            title="Remaining Missing Values by Column"
        )

        missing_fig.update_traces(
            textposition="outside"
        )

        missing_fig.update_layout(
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
            coloraxis_showscale=False,
            xaxis=dict(
                showgrid=False
            ),
            yaxis=dict(
                title="Missing Values",
                gridcolor="rgba(148,163,184,0.10)"
            )
        )

        st.plotly_chart(
            missing_fig,
            use_container_width=True
        )

    else:

        st.success(
            "✓ No missing values remain in the processed dataset."
        )

    # --------------------------------------------------------
    # METHODOLOGY
    # --------------------------------------------------------

    st.markdown(f"""
    <div class="insight-card">

    <div class="insight-title">
    ✦ DATA PREPROCESSING
    </div>

    <div class="insight-text">

    The original dataset contained
    <b>{q1_missing}</b> missing values in
    <b>Incidence_per_100k</b>.

    <br><br>

    Missing incidence values were imputed using the
    <b>median incidence for the corresponding disease</b>.

    <br><br>

    After preprocessing, the number of missing incidence
    values was reduced to <b>{q3_missing}</b>.

    <br><br>

    This cleaned dataset is then used throughout the
    DiseaseScope analysis and visualizations.

    </div>

    </div>
    """, unsafe_allow_html=True)
if page == "🏠 Overview":
    # -----------------------------
    # INDIA REGIONAL INTELLIGENCE
    # -----------------------------

    st.markdown(
        '<div class="section-title">🇮🇳 India Regional Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Explore how disease incidence varies across India\'s major regions.'
        '</div>',
        unsafe_allow_html=True
    )

    # Regional summary
    regional_map = (
        df.groupby(["Region", "Disease"])["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    # Average incidence across diseases for each region
    regional_overall = (
        regional_map.groupby("Region")["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    regional_overall["Incidence_per_100k"] = (
        regional_overall["Incidence_per_100k"].round(2)
    )

    fig_region = px.bar(
        regional_overall.sort_values("Incidence_per_100k"),
        x="Incidence_per_100k",
        y="Region",
        orientation="h",
        text="Incidence_per_100k",
        title="Average Disease Incidence by Region",
        labels={
            "Incidence_per_100k": "Average Incidence per 100,000",
            "Region": ""
        }
    )

    fig_region.update_traces(
        textposition="outside"
    )

    fig_region.update_layout(
        height=450,
        showlegend=False,
        margin=dict(l=20, r=40, t=60, b=20)
    )

    st.plotly_chart(
        fig_region,
        use_container_width=True
    )
    # -----------------------------
    # INTERACTIVE INDIA MAP
    # -----------------------------

    st.markdown(
        '<div class="section-title">🗺️ India Disease Intelligence Map</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Explore disease incidence across Indian states and union territories.'
        '</div>',
        unsafe_allow_html=True
    )

    # -----------------------------
    # MAP CONTROLS
    # -----------------------------

    map_col1, map_col2 = st.columns([1, 3])

    with map_col1:

        map_disease = st.selectbox(
            "Select Disease",
            sorted(df["Disease"].dropna().unique()),
            key="india_map_disease"
        )

        map_year = st.selectbox(
            "Select Year",
            sorted(df["Year"].dropna().unique(), reverse=True),
            key="india_map_year"
        )


    # -----------------------------
    # FILTER DATA
    # -----------------------------

    map_data = df[
        (df["Disease"] == map_disease) &
        (df["Year"] == map_year)
    ].copy()

    map_data = (
        map_data
        .groupby(["State", "Region"], as_index=False)
        ["Incidence_per_100k"]
        .mean()
    )


    # -----------------------------
    # LOAD INDIA GEOJSON
    # -----------------------------

    geojson_url = (
        "https://raw.githubusercontent.com/"
        "india-in-data/india-states-2019/master/india_states.geojson"
    )

    try:

        response = requests.get(
            geojson_url,
            timeout=15
        )

        response.raise_for_status()

        india_geojson = response.json()


        # -----------------------------
        # NORMALIZE STATE NAMES
        # -----------------------------

        def normalize_state(name):

            return (
                str(name)
                .lower()
                .replace("&", "and")
                .replace(".", "")
                .replace(",", "")
                .replace("-", " ")
                .replace("'", "")
                .replace("  ", " ")
                .strip()
            )


        # -----------------------------
        # GET GEOJSON STATES
        # -----------------------------

        geo_states = sorted(
            set(
                feature["properties"]["ST_NM"]
                for feature in india_geojson["features"]
                if "ST_NM" in feature["properties"]
            )
        )


        # -----------------------------
        # SPECIAL STATE NAME MATCHES
        # -----------------------------

        aliases = {

            "jammu and kashmir":
                "Jammu & Kashmir",

            "jammu & kashmir":
                "Jammu & Kashmir",

            "andaman and nicobar":
                "Andaman & Nicobar Islands",

            "andaman and nicobar islands":
                "Andaman & Nicobar Islands",

            "dadra and nagar haveli and daman and diu":
                "Dadra and Nagar Haveli and Daman & Diu",

            "dadra and nagar haveli":
                "Dadra and Nagar Haveli",

            "daman and diu":
                "Daman and Diu",

            "puducherry":
                "Puducherry",

            "pondicherry":
                "Puducherry",

            "uttaranchal":
                "Uttarakhand",

            "orissa":
                "Odisha"

        }


        # -----------------------------
        # GEOJSON LOOKUP
        # -----------------------------

        geo_lookup = {
            normalize_state(state): state
            for state in geo_states
        }


        def find_geo_state(dataset_state):

            normalized = normalize_state(dataset_state)

            # Direct match
            if normalized in geo_lookup:
                return geo_lookup[normalized]

            # Alias match
            if normalized in aliases:

                target = normalize_state(
                    aliases[normalized]
                )

                if target in geo_lookup:
                    return geo_lookup[target]

            return None


        # -----------------------------
        # MATCH EXCEL STATES
        # -----------------------------

        map_data["GeoState"] = (
            map_data["State"]
            .apply(find_geo_state)
        )


        # -----------------------------
        # CREATE MAP
        # -----------------------------

        fig_map = px.choropleth(
            map_data,
            geojson=india_geojson,
            locations="GeoState",
            featureidkey="properties.ST_NM",

            color="Incidence_per_100k",

            color_continuous_scale=[
                "#17122B",
                "#312E81",
                "#5B21B6",
                "#9333EA",
                "#C026D3",
                "#22D3EE"
            ],

            hover_name="State",

            hover_data={
                "Region": True,
                "Incidence_per_100k": ":.2f",
                "GeoState": False
            },

            labels={
                "Incidence_per_100k":
                    "Incidence / 100k",
                "Region":
                    "Region"
            }
        )


        # -----------------------------
        # MAP APPEARANCE
        # -----------------------------

        fig_map.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)",
            showland=False,
            showlakes=False
        )


        fig_map.update_traces(
            marker_line_color="#64748B",
            marker_line_width=0.7
        )


        fig_map.update_layout(

            height=600,

            margin=dict(
                l=0,
                r=0,
                t=10,
                b=0
            ),

            paper_bgcolor="rgba(0,0,0,0)",

            plot_bgcolor="rgba(0,0,0,0)",

            coloraxis_colorbar=dict(
                title="Incidence<br>per 100k",
                thickness=15,
                len=0.7
            )
        )


        # -----------------------------
        # DISPLAY MAP
        # -----------------------------

        with map_col2:

            st.plotly_chart(
                fig_map,
                use_container_width=True
            )


        # -----------------------------
        # MATCHING INFORMATION
        # -----------------------------

        unmatched = map_data[
            map_data["GeoState"].isna()
        ]["State"].tolist()

        if unmatched:

            st.caption(
                "Some dataset states could not be matched to the current "
                "map boundary file: "
                + ", ".join(unmatched)
            )


    except Exception as e:

        with map_col2:

            st.error(
                f"India map could not be loaded: {e}"
            )
    except Exception as e:
        ...
        # -----------------------------
    # DYNAMIC DISEASE INSIGHTS
    # -----------------------------

    st.markdown(
        '<div class="section-title">🧠 Disease Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Automatically generated insights from the selected disease and year.'
        '</div>',
        unsafe_allow_html=True
    )


    # ---------------------------------
    # SELECTED DATASET
    # ---------------------------------

    insight_data = df[
        (df["Disease"] == map_disease) &
        (df["Year"] == map_year)
    ].copy()


    # ---------------------------------
    # STATE-LEVEL ANALYSIS
    # ---------------------------------

    state_incidence = (
        insight_data
        .groupby(["State", "Region"])["Incidence_per_100k"]
        .mean()
        .reset_index()
    )


    # Highest incidence
    highest_row = state_incidence.loc[
        state_incidence["Incidence_per_100k"].idxmax()
    ]

    highest_state = highest_row["State"]
    highest_region = highest_row["Region"]
    highest_value = highest_row["Incidence_per_100k"]


    # Lowest incidence
    lowest_row = state_incidence.loc[
        state_incidence["Incidence_per_100k"].idxmin()
    ]

    lowest_state = lowest_row["State"]
    lowest_region = lowest_row["Region"]
    lowest_value = lowest_row["Incidence_per_100k"]


    # ---------------------------------
    # REGIONAL ANALYSIS
    # ---------------------------------

    regional_incidence = (
        insight_data
        .groupby("Region")["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    regional_highest = regional_incidence.loc[
        regional_incidence["Incidence_per_100k"].idxmax()
    ]

    highest_region_name = regional_highest["Region"]
    highest_region_value = regional_highest["Incidence_per_100k"]


    # ---------------------------------
    # INSIGHT CARDS
    # ---------------------------------

    insight1, insight2, insight3 = st.columns(3)

    with insight1:
        st.markdown(
            f"""<div class="metric-card">
    <div class="metric-label">🔴 HIGHEST INCIDENCE</div>
    <div class="metric-value">{highest_state}</div>
    <div class="metric-sub">{highest_value:.2f} cases per 100,000<br>Region: {highest_region}</div>
    </div>""",
            unsafe_allow_html=True
        )

    with insight2:
        st.markdown(
            f"""<div class="metric-card">
    <div class="metric-label">🟢 LOWEST INCIDENCE</div>
    <div class="metric-value">{lowest_state}</div>
    <div class="metric-sub">{lowest_value:.2f} cases per 100,000<br>Region: {lowest_region}</div>
    </div>""",
            unsafe_allow_html=True
        )

    with insight3:
        st.markdown(
            f"""<div class="metric-card">
    <div class="metric-label">📊 REGIONAL PEAK</div>
    <div class="metric-value">{highest_region_name}</div>
    <div class="metric-sub">{highest_region_value:.2f} average<br>Across selected year</div>
    </div>""",
            unsafe_allow_html=True
        )


    # ---------------------------------
    # AUTOMATIC TEXT INSIGHT
    # ---------------------------------

    st.markdown(
        f"""<div class="insight-card">
    <div class="insight-title">✦ What the data tells us</div>
    <div class="insight-text">
    For <strong>{map_disease}</strong> in <strong>{map_year}</strong>,
    the highest state-level incidence in the dataset was recorded for
    <strong>{highest_state}</strong>, with
    <strong>{highest_value:.2f}</strong> cases per 100,000.
    <br><br>
    The lowest recorded incidence was in
    <strong>{lowest_state}</strong>, at
    <strong>{lowest_value:.2f}</strong> cases per 100,000.
    <br><br>
    Among the six regions, <strong>{highest_region_name}</strong>
    had the highest average incidence for the selected disease
    and year.
    </div>
    <div class="insight-note">
    Note: These are descriptive statistics from the dataset and
    should not be interpreted as a measure of healthcare quality.
    </div>
    </div>""",
        unsafe_allow_html=True
    )
    # ---------------------------------
    # STATE INCIDENCE RANKING
    # ---------------------------------

    st.markdown(
        '<div class="section-title">📊 State Incidence Ranking</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Compare state-level incidence for the selected disease and year.'
        '</div>',
        unsafe_allow_html=True
    )


    # Prepare ranking data
    ranking_data = (
        insight_data
        .groupby(["State", "Region"])["Incidence_per_100k"]
        .mean()
        .reset_index()
        .sort_values(
            "Incidence_per_100k",
            ascending=False
        )
    )


    # Interactive chart
    fig_ranking = px.bar(
        ranking_data,
        x="Incidence_per_100k",
        y="State",
        color="Incidence_per_100k",
        orientation="h",
        color_continuous_scale=[
            "#17122B",
            "#312E81",
            "#6D28D9",
            "#9333EA",
            "#22D3EE"
        ],
        hover_data={
            "Region": True,
            "Incidence_per_100k": ":.2f"
        },
        labels={
            "Incidence_per_100k": "Incidence per 100,000",
            "State": ""
        }
    )

    fig_ranking.update_layout(
        height=750,
        yaxis=dict(
            categoryorder="total ascending"
        ),
        margin=dict(
            l=10,
            r=20,
            t=20,
            b=20
        ),
        coloraxis_colorbar=dict(
            title="Incidence"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    fig_ranking.update_traces(
        marker_line_width=0
    )

    st.plotly_chart(
        fig_ranking,
        use_container_width=True
    )
    # ---------------------------------
    # DISEASE TREND INTELLIGENCE
    # ---------------------------------

    st.markdown(
        '<div class="section-title">📈 Disease Trend Intelligence</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Track how disease incidence changes across India over time.'
        '</div>',
        unsafe_allow_html=True
    )


    # ---------------------------------
    # YEARLY DISEASE SUMMARY
    # ---------------------------------

    trend_data = (
        df[df["Disease"] == map_disease]
        .groupby("Year")
        .agg(
            Mean_Incidence=("Incidence_per_100k", "mean"),
            Total_Cases=("Cases", "sum"),
            Total_Deaths=("Deaths", "sum")
        )
        .reset_index()
    )


    # ---------------------------------
    # TREND CHART
    # ---------------------------------

    fig_trend = px.line(
        trend_data,
        x="Year",
        y="Mean_Incidence",
        markers=True,
        labels={
            "Year": "Year",
            "Mean_Incidence": "Mean Incidence per 100,000"
        }
    )

    fig_trend.update_traces(
        line_width=3,
        marker_size=9,
        hovertemplate=
            "<b>Year:</b> %{x}<br>"
            "<b>Incidence:</b> %{y:.2f}"
            "<extra></extra>"
    )

    fig_trend.update_layout(
        height=450,
        margin=dict(
            l=10,
            r=20,
            t=20,
            b=20
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            dtick=1
        )
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )


    # ---------------------------------
    # TREND METRICS
    # ---------------------------------

    first_year = trend_data.iloc[0]
    last_year = trend_data.iloc[-1]

    change = (
        last_year["Mean_Incidence"]
        - first_year["Mean_Incidence"]
    )

    if first_year["Mean_Incidence"] != 0:

        percentage_change = (
            change /
            first_year["Mean_Incidence"]
        ) * 100

    else:

        percentage_change = 0


    trend1, trend2, trend3 = st.columns(3)


    with trend1:

        st.metric(
            "Starting Incidence",
            f"{first_year['Mean_Incidence']:.2f}",
            f"{int(first_year['Year'])}"
        )


    with trend2:

        st.metric(
            "Latest Incidence",
            f"{last_year['Mean_Incidence']:.2f}",
            f"{int(last_year['Year'])}"
        )


    with trend3:

        st.metric(
            "Overall Change",
            f"{percentage_change:+.1f}%",
            f"{change:+.2f} per 100k"
        )
        # ---------------------------------
    # DISEASE × REGION HEATMAP
    # ---------------------------------

    st.markdown(
        '<div class="section-title">🌡️ Disease × Region Heatmap</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Compare average disease incidence across India\'s six regions.'
        '</div>',
        unsafe_allow_html=True
    )


    # ---------------------------------
    # CREATE HEATMAP DATA
    # ---------------------------------

    heatmap_data = (
        df.groupby(
            ["Disease", "Region"]
        )["Incidence_per_100k"]
        .mean()
        .reset_index()
    )

    heatmap_data["Incidence_per_100k"] = (
        heatmap_data["Incidence_per_100k"]
        .round(2)
    )


    # ---------------------------------
    # CREATE HEATMAP
    # ---------------------------------

    fig_heatmap = px.density_heatmap(
        heatmap_data,
        x="Region",
        y="Disease",
        z="Incidence_per_100k",

        text_auto=".2f",

        color_continuous_scale=[
            "#111827",
            "#312E81",
            "#6D28D9",
            "#9333EA",
            "#C026D3",
            "#22D3EE"
        ],

        labels={
            "Region": "",
            "Disease": "",
            "Incidence_per_100k":
                "Mean Incidence / 100k"
        }
    )


    fig_heatmap.update_layout(

        height=500,

        margin=dict(
            l=10,
            r=20,
            t=30,
            b=20
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)",

        coloraxis_colorbar=dict(
            title="Incidence<br>per 100k",
            thickness=15
        )
    )


    fig_heatmap.update_xaxes(
        side="bottom"
    )


    fig_heatmap.update_yaxes(
        autorange="reversed"
    )


    st.plotly_chart(
        fig_heatmap,
        use_container_width=True
    )

