import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from pathlib import Path

# ============================================================
# DISEASESCOPE — INDIA DISEASE INTELLIGENCE
# ============================================================

st.set_page_config(
    page_title="DiseaseScope",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PREMIUM DARK UI
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
 --bg:#070a11;--panel:#0f1726;--panel2:#111b2d;--line:rgba(148,163,184,.13);
 --text:#f8fafc;--muted:#8292aa;--purple:#8b5cf6;--cyan:#22d3ee;
 --blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;
}
html,body,[class*="css"]{font-family:Inter,sans-serif}
.stApp{
 background:
 radial-gradient(circle at 82% 0%,rgba(124,58,237,.17),transparent 28%),
 radial-gradient(circle at 0% 35%,rgba(34,211,238,.065),transparent 26%),
 #070a11;color:var(--text);
}
.block-container{max-width:1500px;padding-top:1.25rem;padding-bottom:4rem}
section[data-testid="stSidebar"]{background:#090d16;border-right:1px solid var(--line)}
section[data-testid="stSidebar"]>div{padding-top:1.25rem}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:transparent}

.sidebar-brand{font-size:25px;font-weight:800;letter-spacing:-1px}
.sidebar-sub{font-size:12px;color:#8292aa;margin-top:3px}
.side-label{font-size:10px;font-weight:800;letter-spacing:1.5px;color:#66758d;margin:22px 0 8px;text-transform:uppercase}

.hero{padding:8px 0 20px}
.eyebrow{font-size:12px;font-weight:800;letter-spacing:2px;color:#b28cff;text-transform:uppercase}
.hero h1{font-size:clamp(38px,4.2vw,60px);line-height:1.02;letter-spacing:-3px;margin:9px 0 12px}
.grad{background:linear-gradient(90deg,#c084fc,#60a5fa,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{max-width:780px;color:#91a1b8;font-size:15px;line-height:1.65}

.page-title{font-size:31px;font-weight:800;letter-spacing:-1.3px;margin:3px 0 4px}
.page-sub{font-size:13px;color:#7e8ea7;margin-bottom:18px}

.card{
 background:linear-gradient(145deg,rgba(18,28,45,.96),rgba(10,16,28,.96));
 border:1px solid var(--line);border-radius:18px;padding:18px 20px;
 box-shadow:0 15px 40px rgba(0,0,0,.16)
}
.k-label{font-size:10px;font-weight:800;letter-spacing:1.1px;color:#8191aa}
.k-value{font-size:31px;font-weight:800;letter-spacing:-1px;margin-top:8px}
.k-sub{font-size:11px;color:#687991;margin-top:4px}
.k-icon{float:right;font-size:20px}

.section{font-size:22px;font-weight:800;letter-spacing:-.7px;margin:27px 0 4px}
.caption{font-size:12px;color:#708099;margin-bottom:12px}
.insight{
 border:1px solid rgba(139,92,246,.2);border-radius:17px;padding:18px 21px;
 background:linear-gradient(135deg,rgba(139,92,246,.13),rgba(34,211,238,.055));
 margin:13px 0
}
.insight-title{font-size:10px;color:#22d3ee;font-weight:800;letter-spacing:1.2px}
.insight-body{font-size:14px;line-height:1.65;color:#d6deea;margin-top:7px}
.signal{
 border:1px solid var(--line);border-radius:16px;padding:17px;
 background:rgba(15,23,38,.72);min-height:112px
}
.signal-title{font-size:10px;color:#8a9ab0;font-weight:800;letter-spacing:1px}
.signal-value{font-size:18px;font-weight:800;margin-top:7px}
.signal-text{font-size:11px;color:#73849b;margin-top:5px;line-height:1.45}

.badge{display:inline-block;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:800}
.up{background:rgba(52,211,153,.12);color:#34d399}
.down{background:rgba(251,113,133,.12);color:#fb7185}
.neutral{background:rgba(148,163,184,.12);color:#94a3b8}

div[data-baseweb="select"]>div{background:#111827;border-color:rgba(148,163,184,.16);border-radius:10px}
.stButton>button{border-radius:10px;border:1px solid rgba(139,92,246,.32);background:rgba(124,58,237,.13);color:#f1f5f9;font-weight:650}
.stButton>button:hover{border-color:#a78bfa;background:rgba(124,58,237,.25)}
div[data-testid="stDataFrame"]{border-radius:14px;overflow:hidden;border:1px solid var(--line)}
.stDownloadButton>button{width:100%}

[data-testid="stMetric"]{
 background:linear-gradient(145deg,rgba(18,28,45,.95),rgba(10,16,28,.95));
 border:1px solid var(--line);border-radius:15px;padding:14px
}
hr{border-color:rgba(148,163,184,.08)}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_data():
    paths=[
        Path("data/india_5_diseases_enriched.xlsx"),
        Path("india_5_diseases_enriched.xlsx"),
        Path(__file__).resolve().parent/"data"/"india_5_diseases_enriched.xlsx",
    ]
    source=next((p for p in paths if p.exists()),None)
    if source is None:
        st.error("Could not find data/india_5_diseases_enriched.xlsx")
        st.stop()
    x=pd.read_excel(source,sheet_name="All Diseases (combined)")
    x.columns=[str(c).strip() for c in x.columns]
    for c in ["Population_Approx","Cases","Deaths","Incidence_per_100k","Pct_Population_Affected","Case_Fatality_Rate_pct"]:
        x[c]=pd.to_numeric(x[c],errors="coerce")
    x["Year"]=pd.to_numeric(x["Year"],errors="coerce").astype("Int64")
    missing_before=int(x["Incidence_per_100k"].isna().sum())
    x["Incidence_per_100k"]=x.groupby("Disease")["Incidence_per_100k"].transform(lambda s:s.fillna(s.median()))
    missing_after=int(x["Incidence_per_100k"].isna().sum())
    return x,missing_before,missing_after,str(source)

df,missing_before,missing_after,source_file=load_data()
DISEASES=sorted(df["Disease"].dropna().unique())
REGIONS=sorted(df["Region"].dropna().unique())
STATES=sorted(df["State"].dropna().unique())
YEARS=sorted(df["Year"].dropna().astype(int).unique())

# ============================================================
# HELPERS
# ============================================================

def kpi(label,value,sub="",icon=""):
    st.markdown(f"""<div class="card"><span class="k-icon">{icon}</span>
    <div class="k-label">{label}</div><div class="k-value">{value}</div>
    <div class="k-sub">{sub}</div></div>""",unsafe_allow_html=True)

def header(title,sub):
    st.markdown(f'<div class="page-title">{title}</div><div class="page-sub">{sub}</div>',unsafe_allow_html=True)

def theme(fig,height=430):
    fig.update_layout(
        height=height,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1",family="Inter"),margin=dict(l=15,r=15,t=42,b=18),
        hoverlabel=dict(bgcolor="#111827",font_color="#fff"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    fig.update_xaxes(showline=False,zeroline=False,gridcolor="rgba(148,163,184,.08)")
    fig.update_yaxes(showline=False,zeroline=False,gridcolor="rgba(148,163,184,.08)")
    return fig

def pct_change(first,last):
    return ((last-first)/first*100) if first not in [0,np.nan] else 0

def badge(v):
    if v>0:return f'<span class="badge up">↑ {v:.1f}%</span>'
    if v<0:return f'<span class="badge down">↓ {abs(v):.1f}%</span>'
    return '<span class="badge neutral">→ 0.0%</span>'

def normalize_state(name):
    return (str(name).lower().replace("&","and").replace(".","").replace(",","")
            .replace("-"," ").replace("'","").replace("  "," ").strip())

ALIASES={
 "jammu and kashmir":"Jammu & Kashmir",
 "andaman and nicobar":"Andaman & Nicobar Islands",
 "andaman and nicobar islands":"Andaman & Nicobar Islands",
 "dadra and nagar haveli and daman and diu":"Dadra and Nagar Haveli and Daman & Diu",
 "dadra and nagar haveli":"Dadra and Nagar Haveli",
 "daman and diu":"Daman and Diu",
 "pondicherry":"Puducherry",
 "uttaranchal":"Uttarakhand",
 "orissa":"Odisha",
}

@st.cache_data(ttl=86400,show_spinner=False)
def get_india_geojson():
    url="https://raw.githubusercontent.com/india-in-data/india-states-2019/master/india_states.geojson"
    r=requests.get(url,timeout=20)
    r.raise_for_status()
    return r.json()

def make_map(data,disease,year):
    geo=get_india_geojson()
    states={f["properties"].get("ST_NM") for f in geo["features"] if "ST_NM" in f["properties"]}
    lookup={normalize_state(s):s for s in states}

    def match(s):
        n=normalize_state(s)
        if n in lookup:return lookup[n]
        if n in ALIASES:return lookup.get(normalize_state(ALIASES[n]))
        return None

    x=data[(data["Disease"]==disease)&(data["Year"]==year)].copy()
    x=x.groupby(["State","Region"],as_index=False)["Incidence_per_100k"].mean()
    x["GeoState"]=x["State"].map(match)

    fig=px.choropleth(
        x,geojson=geo,locations="GeoState",featureidkey="properties.ST_NM",
        color="Incidence_per_100k",
        color_continuous_scale=["#111827","#312e81","#6d28d9","#a855f7","#22d3ee"],
        hover_name="State",
        hover_data={"Region":True,"Incidence_per_100k":":.2f","GeoState":False},
        labels={"Incidence_per_100k":"Incidence / 100k","Region":"Region"}
    )
    fig.update_geos(fitbounds="locations",visible=False,bgcolor="rgba(0,0,0,0)",showland=False,showlakes=False)
    fig.update_traces(marker_line_color="#64748b",marker_line_width=.7)
    fig.update_layout(height=610,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",coloraxis_colorbar=dict(title="Incidence<br>/ 100k",thickness=14,len=.68))
    return fig,x

def anomaly_frame(data):
    out=[]
    for disease,g in data.groupby("Disease"):
        q1=g["Incidence_per_100k"].quantile(.25);q3=g["Incidence_per_100k"].quantile(.75);iqr=q3-q1
        lo=q1-1.5*iqr;hi=q3+1.5*iqr
        z=g.copy();z["Anomaly"]=np.where(z["Incidence_per_100k"]>hi,"High",np.where(z["Incidence_per_100k"]<lo,"Low","Normal"))
        z["Lower_Threshold"]=lo;z["Upper_Threshold"]=hi
        out.append(z)
    return pd.concat(out,ignore_index=True)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown('<div class="sidebar-brand">🩺 DiseaseScope</div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">India · Disease Intelligence</div>',unsafe_allow_html=True)
    st.markdown('<div class="side-label">Explore</div>',unsafe_allow_html=True)
    page=st.radio("Navigation",[
        "🏠 Overview","🦠 Disease Explorer","📈 Regional Trends","🗺️ State Explorer",
        "🔎 Compare Diseases","🚨 Anomaly Radar","🧠 Intelligence Lab","🧹 Data Quality"
    ],label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<div class="side-label">Dataset</div>',unsafe_allow_html=True)
    st.caption(f"India · {min(YEARS)}–{max(YEARS)}")
    st.caption(f"{len(DISEASES)} diseases · {len(STATES)} states/UTs")
    st.caption(f"{len(REGIONS)} regions · {len(df):,} records")
    st.markdown("---")
    st.caption("All incidence values are per 100,000 population.")

# ============================================================
# OVERVIEW
# ============================================================

if page=="🏠 Overview":
    st.markdown("""<div class="hero"><div class="eyebrow">INDIA · DISEASE INTELLIGENCE</div>
    <h1>Understand the <span class="grad">pulse</span> of disease incidence.</h1>
    <p>Explore six years of disease records through trends, geographic concentration,
    anomaly signals and automated analytical insights.</p></div>""",unsafe_allow_html=True)

    c=st.columns(4)
    with c[0]:kpi("TOTAL RECORDS",f"{len(df):,}","observations","📊")
    with c[1]:kpi("DISEASES",len(DISEASES),"tracked conditions","🦠")
    with c[2]:kpi("STATES / UTs",len(STATES),"geographic coverage","🗺️")
    with c[3]:kpi("REGIONS",len(REGIONS),"Indian regions","🌎")

    dm=df.groupby("Disease")["Incidence_per_100k"].mean().sort_values(ascending=False)
    ym=df.groupby("Year")["Incidence_per_100k"].mean()
    rm=df.groupby("Region")["Incidence_per_100k"].mean().sort_values(ascending=False)
    overall=pct_change(float(ym.iloc[0]),float(ym.iloc[-1]))

    st.markdown('<div class="section">⚡ Intelligence at a glance</div>',unsafe_allow_html=True)
    s=st.columns(4)
    signals=[
        ("HIGHEST MEAN INCIDENCE",dm.index[0],f"{dm.iloc[0]:.2f} per 100k"),
        ("LEADING REGION",rm.index[0],f"{rm.iloc[0]:.2f} mean incidence"),
        ("LATEST YEAR",str(max(YEARS)),f"{ym.iloc[-1]:.2f} overall mean"),
        ("2019 → 2024",f"{overall:+.1f}%", "dataset-wide mean change"),
    ]
    for col,(a,b,cx) in zip(s,signals):
        with col: st.markdown(f'<div class="signal"><div class="signal-title">{a}</div><div class="signal-value">{b}</div><div class="signal-text">{cx}</div></div>',unsafe_allow_html=True)

    l,r=st.columns([1.2,1],gap="large")
    with l:
        st.markdown('<div class="section">Disease landscape</div><div class="caption">Mean incidence across all years and locations.</div>',unsafe_allow_html=True)
        d=dm.reset_index(name="Mean_Incidence")
        f=px.bar(d,x="Mean_Incidence",y="Disease",orientation="h",text="Mean_Incidence",color="Mean_Incidence",color_continuous_scale=["#312e81","#8b5cf6","#22d3ee"])
        f.update_traces(texttemplate="%{text:.2f}",textposition="outside",cliponaxis=False);f.update_layout(coloraxis_showscale=False)
        theme(f,410);f.update_yaxes(categoryorder="total ascending",title="");f.update_xaxes(title="Incidence / 100k")
        st.plotly_chart(f,use_container_width=True)
    with r:
        st.markdown('<div class="section">National pulse</div><div class="caption">Overall mean incidence by year.</div>',unsafe_allow_html=True)
        y=ym.reset_index(name="Mean_Incidence")
        f=px.area(y,x="Year",y="Mean_Incidence",markers=True)
        f.update_traces(line=dict(color="#22d3ee",width=3),fillcolor="rgba(34,211,238,.13)")
        theme(f,410);f.update_xaxes(dtick=1,title="");f.update_yaxes(title="Mean incidence")
        st.plotly_chart(f,use_container_width=True)

    # MAP — RESTORED AND PROMOTED
    st.markdown('<div class="section">🗺️ India Disease Intelligence Map</div>',unsafe_allow_html=True)
    st.markdown('<div class="caption">A geographic view of the selected disease. Hover a state to inspect its incidence and region.</div>',unsafe_allow_html=True)
    m1,m2,m3=st.columns([1.3,1,1])
    with m1:map_disease=st.selectbox("Disease",DISEASES,key="overview_map_disease")
    with m2:map_year=st.selectbox("Year",YEARS,index=len(YEARS)-1,key="overview_map_year")
    with m3:
        map_metric=st.selectbox("Map metric",["Incidence per 100k","Cases","Deaths"],key="overview_map_metric")

    try:
        geo=get_india_geojson()
        map_data=df[(df["Disease"]==map_disease)&(df["Year"]==map_year)].copy()
        metric_col={"Incidence per 100k":"Incidence_per_100k","Cases":"Cases","Deaths":"Deaths"}[map_metric]
        map_data=map_data.groupby(["State","Region"],as_index=False)[metric_col].mean()
        states={f["properties"].get("ST_NM") for f in geo["features"] if "ST_NM" in f["properties"]}
        lookup={normalize_state(s):s for s in states}
        def match(s):
            n=normalize_state(s)
            if n in lookup:return lookup[n]
            if n in ALIASES:return lookup.get(normalize_state(ALIASES[n]))
        map_data["GeoState"]=map_data["State"].map(match)
        figm=px.choropleth(map_data,geojson=geo,locations="GeoState",featureidkey="properties.ST_NM",
            color=metric_col,color_continuous_scale=["#111827","#312e81","#6d28d9","#a855f7","#22d3ee"],
            hover_name="State",hover_data={"Region":True,metric_col:":.2f","GeoState":False})
        figm.update_geos(fitbounds="locations",visible=False,bgcolor="rgba(0,0,0,0)")
        figm.update_traces(marker_line_color="#64748b",marker_line_width=.7)
        figm.update_layout(height=600,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)",coloraxis_colorbar=dict(title=map_metric,thickness=14,len=.7))
        st.plotly_chart(figm,use_container_width=True)
        unmatched=map_data[map_data["GeoState"].isna()]["State"].tolist()
        if unmatched: st.caption("Unmatched boundaries: "+", ".join(unmatched))
    except Exception as e:
        st.warning("The India map could not load from the remote boundary file. Check your internet connection and refresh. Other dashboard features remain available.")

    # HOTSPOT TABLE
    latest=df[df["Year"]==max(YEARS)].groupby(["State","Region"])["Incidence_per_100k"].mean().reset_index().sort_values("Incidence_per_100k",ascending=False)
    st.markdown('<div class="section">🔥 Latest-year hotspots</div>',unsafe_allow_html=True)
    h1,h2=st.columns([1.1,1],gap="large")
    with h1:
        hf=px.bar(latest.head(12).sort_values("Incidence_per_100k"),x="Incidence_per_100k",y="State",orientation="h",
                  color="Incidence_per_100k",color_continuous_scale=["#312e81","#8b5cf6","#fb7185"])
        hf.update_layout(coloraxis_showscale=False);theme(hf,470);hf.update_yaxes(title="");hf.update_xaxes(title="Mean incidence / 100k")
        st.plotly_chart(hf,use_container_width=True)
    with h2:
        show=latest.head(12).copy();show["Incidence_per_100k"]=show["Incidence_per_100k"].round(2)
        st.dataframe(show,use_container_width=True,hide_index=True,height=430)

    st.markdown(f"""<div class="insight"><div class="insight-title">✦ EXECUTIVE READOUT</div>
    <div class="insight-body"><b>{dm.index[0]}</b> has the highest average incidence in the supplied dataset.
    The latest-year state ranking is shown above as a descriptive surveillance signal.
    These statistics are dataset-level patterns and are not clinical diagnoses or measures of healthcare quality.</div></div>""",unsafe_allow_html=True)

# ============================================================
# DISEASE EXPLORER
# ============================================================

elif page=="🦠 Disease Explorer":
    header("Disease Explorer","Deep-dive into one disease without repeating global dashboard information.")
    a,b,c=st.columns([1.3,1,1])
    with a:disease=st.selectbox("Disease",DISEASES,key="dx_disease")
    with b:region=st.selectbox("Region",["All Regions"]+REGIONS,key="dx_region")
    with c:year=st.selectbox("Year",YEARS,index=len(YEARS)-1,key="dx_year")
    data=df[df["Disease"]==disease].copy()
    if region!="All Regions":data=data[data["Region"]==region]
    yd=data[data["Year"]==year]
    mean=float(data["Incidence_per_100k"].mean());cases=float(yd["Cases"].sum());deaths=float(yd["Deaths"].sum())
    k1,k2,k3=st.columns(3)
    with k1:kpi("MEAN INCIDENCE",f"{mean:.2f}","per 100,000","📈")
    with k2:kpi("TOTAL CASES",f"{cases:,.0f}",str(year),"🧾")
    with k3:kpi("TOTAL DEATHS",f"{deaths:,.0f}",str(year),"⚕️")

    trend=data.groupby("Year")["Incidence_per_100k"].mean().reset_index()
    change=pct_change(float(trend.iloc[0,1]),float(trend.iloc[-1,1]))
    st.markdown('<div class="section">📈 Disease trajectory</div>',unsafe_allow_html=True)
    f=px.line(trend,x="Year",y="Incidence_per_100k",markers=True)
    f.update_traces(line=dict(color="#22d3ee",width=3),marker=dict(size=8))
    theme(f,420);f.update_xaxes(dtick=1,title="");f.update_yaxes(title="Incidence / 100k")
    st.plotly_chart(f,use_container_width=True)
    x1,x2,x3=st.columns(3)
    x1.metric("First year",f"{trend.iloc[0,1]:.2f}")
    x2.metric("Latest year",f"{trend.iloc[-1,1]:.2f}")
    x3.metric("2019 → latest",f"{change:+.1f}%")

    rank=yd.groupby(["State","Region"])["Incidence_per_100k"].mean().reset_index().sort_values("Incidence_per_100k",ascending=False)
    l,r=st.columns([1.25,1],gap="large")
    with l:
        st.markdown(f'<div class="section">State distribution · {year}</div>',unsafe_allow_html=True)
        f=px.bar(rank.head(15).sort_values("Incidence_per_100k"),x="Incidence_per_100k",y="State",orientation="h",
                 color="Incidence_per_100k",color_continuous_scale=["#312e81","#8b5cf6","#22d3ee"])
        f.update_layout(coloraxis_showscale=False);theme(f,500);f.update_yaxes(title="");f.update_xaxes(title="Incidence / 100k")
        st.plotly_chart(f,use_container_width=True)
    with r:
        st.markdown('<div class="section">Top state signals</div>',unsafe_allow_html=True)
        t=rank.head(10).copy();t["Incidence_per_100k"]=t["Incidence_per_100k"].round(2)
        st.dataframe(t,use_container_width=True,hide_index=True,height=460)
    if not rank.empty:
        st.markdown(f"""<div class="insight"><div class="insight-title">✦ AUTOMATED INSIGHT</div>
        <div class="insight-body">For <b>{year}</b>, <b>{rank.iloc[0]['State']}</b> has the highest
        recorded {disease} incidence in the selected scope at <b>{rank.iloc[0]['Incidence_per_100k']:.2f}</b> per 100,000.</div></div>""",unsafe_allow_html=True)

# ============================================================
# REGIONAL TRENDS
# ============================================================

elif page=="📈 Regional Trends":
    header("Regional Trends","Compare regional trajectories and concentration patterns.")
    a,b=st.columns(2)
    with a:disease=st.selectbox("Disease",DISEASES,key="reg_disease")
    with b:regions=st.multiselect("Regions",REGIONS,default=REGIONS,key="reg_regions")
    data=df[df["Disease"]==disease].copy()
    if regions:data=data[data["Region"].isin(regions)]
    trend=data.groupby(["Region","Year"])["Incidence_per_100k"].mean().reset_index()
    f=px.line(trend,x="Year",y="Incidence_per_100k",color="Region",markers=True)
    f.update_traces(line=dict(width=3),marker=dict(size=7));theme(f,500);f.update_xaxes(dtick=1,title="");f.update_yaxes(title="Mean incidence / 100k")
    st.markdown('<div class="section">📈 Regional trajectories</div>',unsafe_allow_html=True)
    st.plotly_chart(f,use_container_width=True)
    summary=data.groupby("Region").agg(Mean_Incidence=("Incidence_per_100k","mean"),Total_Cases=("Cases","sum"),Total_Deaths=("Deaths","sum")).reset_index().sort_values("Mean_Incidence",ascending=False)
    summary["Mean_Incidence"]=summary["Mean_Incidence"].round(2)
    l,r=st.columns([1,1],gap="large")
    with l:
        f=px.bar(summary,x="Mean_Incidence",y="Region",orientation="h",text="Mean_Incidence",color="Mean_Incidence",color_continuous_scale=["#0e7490","#22d3ee","#8b5cf6"])
        f.update_traces(texttemplate="%{text:.2f}",textposition="outside");f.update_layout(coloraxis_showscale=False);theme(f,420);f.update_yaxes(categoryorder="total ascending",title="")
        st.markdown('<div class="section">Regional ranking</div>',unsafe_allow_html=True);st.plotly_chart(f,use_container_width=True)
    with r:
        st.markdown('<div class="section">Regional summary</div>',unsafe_allow_html=True);st.dataframe(summary,use_container_width=True,hide_index=True,height=390)
    st.markdown('<div class="section">🧬 Disease × region fingerprint</div>',unsafe_allow_html=True)
    heat=df.groupby(["Disease","Region"])["Incidence_per_100k"].mean().unstack()
    f=px.imshow(heat,text_auto=".1f",aspect="auto",color_continuous_scale=["#111827","#312e81","#8b5cf6","#22d3ee"])
    theme(f,410);st.plotly_chart(f,use_container_width=True)

# ============================================================
# STATE EXPLORER
# ============================================================

elif page=="🗺️ State Explorer":
    header("State Explorer","A complete analytical profile for an Indian state or union territory.")
    state=st.selectbox("Select state / UT",STATES,index=STATES.index("Telangana") if "Telangana" in STATES else 0,key="state")
    data=df[df["State"]==state].copy()
    region=data["Region"].mode().iloc[0] if not data.empty else "—"
    avg=data["Incidence_per_100k"].mean();cases=data["Cases"].sum();deaths=data["Deaths"].sum()
    k=st.columns(4)
    with k[0]:kpi("MEAN INCIDENCE",f"{avg:.2f}","all years","📈")
    with k[1]:kpi("TOTAL CASES",f"{cases:,.0f}","all diseases","🧾")
    with k[2]:kpi("TOTAL DEATHS",f"{deaths:,.0f}","all diseases","⚕️")
    with k[3]:kpi("REGION",region,"dataset classification","📍")
    l,r=st.columns(2,gap="large")
    profile=data.groupby("Disease")["Incidence_per_100k"].mean().reset_index().sort_values("Incidence_per_100k")
    with l:
        st.markdown('<div class="section">Disease profile</div>',unsafe_allow_html=True)
        f=px.bar(profile,x="Incidence_per_100k",y="Disease",orientation="h",color="Incidence_per_100k",color_continuous_scale=["#312e81","#8b5cf6","#22d3ee"])
        f.update_layout(coloraxis_showscale=False);theme(f,420);f.update_yaxes(title="");f.update_xaxes(title="Mean incidence / 100k");st.plotly_chart(f,use_container_width=True)
    with r:
        st.markdown('<div class="section">State trajectory</div>',unsafe_allow_html=True)
        y=data.groupby("Year")["Incidence_per_100k"].mean().reset_index()
        f=px.line(y,x="Year",y="Incidence_per_100k",markers=True);f.update_traces(line=dict(width=3,color="#60a5fa"),marker=dict(size=8));theme(f,420);f.update_xaxes(dtick=1,title="");f.update_yaxes(title="Mean incidence");st.plotly_chart(f,use_container_width=True)
    st.markdown('<div class="section">State records</div>',unsafe_allow_html=True)
    table=data[["Disease","Region","Year","Cases","Deaths","Incidence_per_100k"]].copy();table["Incidence_per_100k"]=table["Incidence_per_100k"].round(2)
    st.dataframe(table.sort_values(["Year","Disease"]),use_container_width=True,hide_index=True,height=430)

# ============================================================
# COMPARE
# ============================================================

elif page=="🔎 Compare Diseases":
    header("Compare Diseases","Put multiple diseases on one analytical canvas.")
    selected=st.multiselect("Select diseases",DISEASES,default=DISEASES[:3],max_selections=5,key="compare")
    if not selected:st.info("Select at least one disease.");st.stop()
    data=df[df["Disease"].isin(selected)]
    comp=data.groupby(["Disease","Year"])["Incidence_per_100k"].mean().reset_index()
    f=px.line(comp,x="Year",y="Incidence_per_100k",color="Disease",markers=True);f.update_traces(line=dict(width=3),marker=dict(size=8));theme(f,500);f.update_xaxes(dtick=1,title="");f.update_yaxes(title="Mean incidence / 100k")
    st.markdown('<div class="section">📊 Incidence comparison</div>',unsafe_allow_html=True);st.plotly_chart(f,use_container_width=True)
    latest=comp[comp["Year"]==max(YEARS)].sort_values("Incidence_per_100k",ascending=False)
    first=comp[comp["Year"]==min(YEARS)].set_index("Disease")["Incidence_per_100k"]
    cols=st.columns(len(selected))
    for col,d in zip(cols,selected):
        cur=float(latest[latest["Disease"]==d]["Incidence_per_100k"].iloc[0]);ini=float(first.get(d,cur));pc=pct_change(ini,cur)
        with col:st.markdown(f'<div class="signal"><div class="signal-title">{d.upper()}</div><div class="signal-value">{cur:.2f}</div><div class="signal-text">latest mean incidence / 100k<br>{badge(pc)}</div></div>',unsafe_allow_html=True)
    snap=data[data["Year"]==max(YEARS)].groupby("Disease").agg(Mean_Incidence=("Incidence_per_100k","mean"),Total_Cases=("Cases","sum"),Total_Deaths=("Deaths","sum")).reset_index().sort_values("Mean_Incidence",ascending=False)
    snap["Mean_Incidence"]=snap["Mean_Incidence"].round(2)
    st.markdown('<div class="section">Latest-year snapshot</div>',unsafe_allow_html=True);st.dataframe(snap,use_container_width=True,hide_index=True)
    mat=comp.pivot(index="Disease",columns="Year",values="Incidence_per_100k")
    f=px.imshow(mat,text_auto=".1f",aspect="auto",color_continuous_scale=["#111827","#312e81","#8b5cf6","#22d3ee"]);theme(f,350)
    st.markdown('<div class="section">Disease × year fingerprint</div>',unsafe_allow_html=True);st.plotly_chart(f,use_container_width=True)

# ============================================================
# ANOMALY RADAR
# ============================================================

elif page=="🚨 Anomaly Radar":
    header("Anomaly Radar","Statistically flag unusually high or low observations using a transparent IQR rule.")
    ad=anomaly_frame(df);unusual=ad[ad["Anomaly"]!="Normal"]
    high=int((ad["Anomaly"]=="High").sum());low=int((ad["Anomaly"]=="Low").sum())
    k=st.columns(3)
    with k[0]:kpi("UNUSUAL",f"{len(unusual):,}","outside IQR bounds","🚨")
    with k[1]:kpi("HIGH",f"{high:,}","above Q3 + 1.5×IQR","🔴")
    with k[2]:kpi("LOW",f"{low:,}","below Q1 − 1.5×IQR","🔵")
    filt=st.selectbox("Disease filter",["All Diseases"]+DISEASES,key="af")
    display=unusual if filt=="All Diseases" else unusual[unusual["Disease"]==filt]
    counts=ad[ad["Anomaly"]!="Normal"].groupby(["Disease","Anomaly"]).size().reset_index(name="Count")
    f=px.bar(counts,x="Disease",y="Count",color="Anomaly",barmode="group",color_discrete_map={"High":"#fb7185","Low":"#22d3ee"});theme(f,420);f.update_xaxes(title="");f.update_yaxes(title="Observations")
    st.markdown('<div class="section">🚨 Anomaly distribution</div>',unsafe_allow_html=True);st.plotly_chart(f,use_container_width=True)
    cols=["Disease","State","Region","Year","Cases","Deaths","Incidence_per_100k","Anomaly"]
    t=display[cols].sort_values("Incidence_per_100k",ascending=False).copy();t["Incidence_per_100k"]=t["Incidence_per_100k"].round(2)
    st.markdown('<div class="section">Detected observations</div>',unsafe_allow_html=True);st.dataframe(t,use_container_width=True,hide_index=True,height=480)
    st.markdown('<div class="insight"><div class="insight-title">✦ METHODOLOGY</div><div class="insight-body">For each disease separately, observations above <b>Q3 + 1.5 × IQR</b> are High and observations below <b>Q1 − 1.5 × IQR</b> are Low. This is a statistical flag, not a medical diagnosis.</div></div>',unsafe_allow_html=True)

# ============================================================
# INTELLIGENCE LAB — NEW FEATURE
# ============================================================

elif page=="🧠 Intelligence Lab":
    header("Intelligence Lab","Turn the dataset into an analytical priority board — not just another collection of charts.")

    disease=st.selectbox("Focus disease",DISEASES,key="lab_disease")
    year=st.selectbox("Focus year",YEARS,index=len(YEARS)-1,key="lab_year")

    current=df[(df["Disease"]==disease)&(df["Year"]==year)].copy()
    previous=df[(df["Disease"]==disease)&(df["Year"]==year-1)].copy() if year-1 in YEARS else pd.DataFrame()

    state=current.groupby(["State","Region"])["Incidence_per_100k"].mean().reset_index()
    national=float(current["Incidence_per_100k"].mean())
    if not previous.empty:
        prev=previous.groupby("State")["Incidence_per_100k"].mean()
        state["Previous"]=state["State"].map(prev)
        state["YoY_%"]=(state["Incidence_per_100k"]-state["Previous"])/state["Previous"].replace(0,np.nan)*100
        state["YoY_%"]=state["YoY_%"].replace([np.inf,-np.inf],np.nan).fillna(0)
    else:state["YoY_%"]=0

    # Analytical priority index: descriptive, transparent, not clinical.
    inc_norm=(state["Incidence_per_100k"]/state["Incidence_per_100k"].max()).fillna(0)
    change_abs=(state["YoY_%"].abs()/max(float(state["YoY_%"].abs().max()),1)).fillna(0)
    state["Priority_Index"]=(0.7*inc_norm+0.3*change_abs)*100
    state=state.sort_values("Priority_Index",ascending=False)

    top=state.iloc[0]
    fastest=state.sort_values("YoY_%",ascending=False).iloc[0]
    regional=current.groupby("Region")["Incidence_per_100k"].mean().sort_values(ascending=False)

    c=st.columns(4)
    with c[0]:kpi("NATIONAL MEAN",f"{national:.2f}","incidence / 100k","◎")
    with c[1]:kpi("TOP PRIORITY STATE",str(top["State"]),f"index {top['Priority_Index']:.1f}/100","🎯")
    with c[2]:kpi("FASTEST RISE",str(fastest["State"]),f"{fastest['YoY_%']:+.1f}% YoY","⚡")
    with c[3]:kpi("LEADING REGION",str(regional.index[0]),f"{regional.iloc[0]:.2f} incidence","📍")

    st.markdown('<div class="section">🎯 Surveillance Priority Board</div>',unsafe_allow_html=True)
    st.caption("A transparent analytical index combining current incidence (70%) and absolute year-over-year movement (30%). It is a data-science prioritization signal, not a medical risk score.")

    board=state[["State","Region","Incidence_per_100k","YoY_%","Priority_Index"]].head(15).copy()
    board["Incidence_per_100k"]=board["Incidence_per_100k"].round(2)
    board["YoY_%"]=board["YoY_%"].round(1)
    board["Priority_Index"]=board["Priority_Index"].round(1)
    st.dataframe(board,use_container_width=True,hide_index=True,height=500)

    l,r=st.columns(2,gap="large")
    with l:
        f=px.scatter(state,x="Incidence_per_100k",y="YoY_%",size="Priority_Index",color="Priority_Index",
                     hover_name="State",color_continuous_scale=["#312e81","#8b5cf6","#22d3ee"])
        f.add_hline(y=0,line_dash="dot",line_color="#64748b")
        theme(f,460);f.update_xaxes(title="Current incidence / 100k");f.update_yaxes(title="Year-over-year change %")
        st.markdown('<div class="section">Incidence × momentum</div>',unsafe_allow_html=True);st.plotly_chart(f,use_container_width=True)
    with r:
        regional_rank=current.groupby("Region")["Incidence_per_100k"].mean().reset_index().sort_values("Incidence_per_100k")
        f=px.bar(regional_rank,x="Incidence_per_100k",y="Region",orientation="h",text="Incidence_per_100k",
                 color="Incidence_per_100k",color_continuous_scale=["#0e7490","#22d3ee","#8b5cf6"])
        f.update_traces(texttemplate="%{text:.1f}",textposition="outside");f.update_layout(coloraxis_showscale=False)
        theme(f,460);f.update_yaxes(title="");f.update_xaxes(title="Incidence / 100k")
        st.markdown('<div class="section">Regional concentration</div>',unsafe_allow_html=True);st.plotly_chart(f,use_container_width=True)

    st.markdown(f"""<div class="insight"><div class="insight-title">✦ MACHINE-GENERATED READOUT</div>
    <div class="insight-body"><b>{top['State']}</b> ranks first on the transparent priority index for
    <b>{disease}</b> in <b>{year}</b>. <b>{fastest['State']}</b> shows the largest positive year-over-year
    movement among available states. Use these signals to decide where to inspect the underlying records next.</div></div>""",unsafe_allow_html=True)

    csv=state.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export Intelligence Board",csv,f"{disease}_{year}_intelligence.csv","text/csv")

# ============================================================
# DATA QUALITY
# ============================================================

elif page=="🧹 Data Quality":
    header("Data Quality Center","See exactly what was cleaned before the dashboard calculations.")
    cells=len(df)*len(df.columns);missing=int(df.isna().sum().sum());complete=(1-missing/cells)*100
    k=st.columns(4)
    with k[0]:kpi("ROWS",f"{len(df):,}","records","▤")
    with k[1]:kpi("COLUMNS",df.shape[1],"variables","◫")
    with k[2]:kpi("INCIDENCE MISSING",missing_before,"before imputation","⚠️")
    with k[3]:kpi("INCIDENCE MISSING",missing_after,"after imputation","✓")
    st.markdown('<div class="section">Data completeness</div>',unsafe_allow_html=True)
    st.progress(float(complete/100));st.caption(f"{complete:.2f}% of cells are populated after preprocessing.")
    l,r=st.columns(2,gap="large")
    with l:
        miss=df.isna().sum().sort_values(ascending=False).reset_index();miss.columns=["Column","Missing"]
        m=miss[miss["Missing"]>0]
        st.markdown('<div class="section">Missing-value profile</div>',unsafe_allow_html=True)
        if m.empty:st.success("No missing values remain.")
        else:
            f=px.bar(m,x="Missing",y="Column",orientation="h",color="Missing",color_continuous_scale=["#312e81","#8b5cf6","#fb7185"])
            f.update_layout(coloraxis_showscale=False);theme(f,370);f.update_yaxes(title="");st.plotly_chart(f,use_container_width=True)
    with r:
        profile=pd.DataFrame({"Column":df.columns,"Type":[str(df[c].dtype) for c in df.columns],"Missing":[int(df[c].isna().sum()) for c in df.columns],"Unique":[int(df[c].nunique()) for c in df.columns]})
        st.markdown('<div class="section">Schema profile</div>',unsafe_allow_html=True);st.dataframe(profile,use_container_width=True,hide_index=True,height=380)
    st.markdown(f'<div class="insight"><div class="insight-title">✦ PREPROCESSING LOG</div><div class="insight-body">The raw dataset had <b>{missing_before}</b> missing Incidence_per_100k values. They were filled using the <b>disease-specific median</b>. Remaining missing incidence values: <b>{missing_after}</b>.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section">Dataset preview</div>',unsafe_allow_html=True);st.dataframe(df.head(15),use_container_width=True,hide_index=True)
    st.download_button("⬇️ Download cleaned dataset",df.to_csv(index=False).encode("utf-8"),"diseasescope_cleaned.csv","text/csv")

# ============================================================
# FOOTER
# ============================================================

st.markdown('<div style="text-align:center;color:#53627a;font-size:10px;margin-top:48px;padding-top:18px;border-top:1px solid rgba(148,163,184,.08)">DiseaseScope · India Disease Incidence Intelligence · 2019–2024</div>',unsafe_allow_html=True)
