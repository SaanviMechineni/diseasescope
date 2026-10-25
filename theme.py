"""Visual theme for DiseaseScope: palette, page CSS, Plotly template and small UI helpers."""
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ------------------------------------------------------------
# PALETTE
# ------------------------------------------------------------
PRIMARY = "#0F4C5C"    # deep teal: headings, primary accents
SECONDARY = "#2A9D8F"  # teal: main single-series colour
ALERT = "#E76F51"      # coral: alerts / high values only
WARNING = "#F4A261"    # amber: warnings
TINT = "#E9F3F2"       # soft background tint
TEXT = "#1F2933"
MUTED = "#52606D"
CARD = "#FFFFFF"
GRID = "#E3EBEA"

# Categorical order for diseases/regions/clusters. Checked with the dataviz
# validator (lightness, chroma, colour-blind separation, contrast on white).
CATEGORICAL = ["#2A9D8F", "#4A6FD0", "#C2852A", "#9A5BB5", "#5E8C2E", "#C24C7A"]

# Sequential single-hue teal scale for maps and heatmaps (light = low).
SEQUENTIAL = ["#F2F8F7", "#CFE6E2", "#93CBC2", "#4FA99C", "#24808A", "#0F4C5C"]

# Fixed colour per disease so a filter never repaints a series.
DISEASE_ORDER = ["Dengue", "Malaria", "Acute Diarrheal Disease", "Measles", "H1N1 (Seasonal Influenza-A)"]
DISEASE_COLORS = dict(zip(DISEASE_ORDER, CATEGORICAL))
REGION_ORDER = ["North", "South", "East", "West", "Central", "Northeast"]
REGION_COLORS = dict(zip(REGION_ORDER, CATEGORICAL))

# ------------------------------------------------------------
# PLOTLY TEMPLATE
# ------------------------------------------------------------
pio.templates["diseasescope"] = go.layout.Template(
    layout=dict(
        font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT, size=13),
        colorway=CATEGORICAL,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorscale=dict(sequential=SEQUENTIAL),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=PRIMARY, font=dict(color=TEXT)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        xaxis=dict(gridcolor=GRID, linecolor="#C9D6D4", zeroline=False, ticks="outside", tickcolor="#C9D6D4"),
        yaxis=dict(gridcolor=GRID, linecolor="#C9D6D4", zeroline=False),
        margin=dict(l=10, r=10, t=36, b=10),
    )
)
pio.templates.default = "plotly_white+diseasescope"


def style(fig, height=420):
    """Apply the shared height/margins to a Plotly figure and return it."""
    fig.update_layout(height=height, template="plotly_white+diseasescope")
    return fig


# ------------------------------------------------------------
# PAGE CSS
# ------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:Inter,"Segoe UI",sans-serif}}
.stApp{{background:{TINT};color:{TEXT}}}
.block-container{{max-width:1360px;padding-top:1.4rem;padding-bottom:3rem}}
section[data-testid="stSidebar"]{{background:{PRIMARY}}}
section[data-testid="stSidebar"] *{{color:#F2F8F7}}
section[data-testid="stSidebar"] div[data-baseweb="select"] *{{color:{TEXT}}}
#MainMenu,footer{{visibility:hidden}}
header[data-testid="stHeader"]{{background:transparent}}

.sidebar-brand{{font-size:24px;font-weight:800;letter-spacing:-.5px}}
.sidebar-sub{{font-size:12px;opacity:.85;margin-top:2px}}
.side-label{{font-size:11px;font-weight:700;letter-spacing:1.2px;opacity:.8;margin:18px 0 6px;text-transform:uppercase}}

.hero{{background:{CARD};border-radius:18px;padding:26px 30px;border-left:6px solid {SECONDARY};margin-bottom:14px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:1.6px;color:{SECONDARY};text-transform:uppercase}}
.hero h1{{font-size:clamp(30px,3.2vw,44px);line-height:1.1;letter-spacing:-1px;margin:8px 0 10px;color:{PRIMARY}}}
.hero p{{max-width:820px;color:{MUTED};font-size:15px;line-height:1.6;margin:0}}

.page-title{{font-size:30px;font-weight:800;letter-spacing:-.6px;margin:2px 0 4px;color:{PRIMARY}}}
.page-sub{{font-size:14px;color:{MUTED};margin-bottom:16px}}

.card{{background:{CARD};border:1px solid #D5E5E2;border-radius:14px;padding:16px 18px;height:100%}}
.k-label{{font-size:11px;font-weight:700;letter-spacing:1px;color:{MUTED}}}
.k-value{{font-size:28px;font-weight:800;margin-top:6px;color:{PRIMARY}}}
.k-sub{{font-size:12px;color:{MUTED};margin-top:3px}}
.k-icon{{float:right;font-size:20px}}

.section{{font-size:21px;font-weight:800;letter-spacing:-.3px;margin:24px 0 4px;color:{PRIMARY}}}
.caption{{font-size:13px;color:{MUTED};margin-bottom:10px}}
.insight{{background:{CARD};border:1px solid #D5E5E2;border-left:5px solid {SECONDARY};border-radius:12px;padding:15px 18px;margin:12px 0}}
.insight.alert{{border-left-color:{ALERT}}}
.insight.warn{{border-left-color:{WARNING}}}
.insight-title{{font-size:11px;color:{PRIMARY};font-weight:800;letter-spacing:1px}}
.insight-body{{font-size:14px;line-height:1.6;color:{TEXT};margin-top:6px}}
.signal{{background:{CARD};border:1px solid #D5E5E2;border-radius:12px;padding:15px;min-height:108px}}
.signal-title{{font-size:11px;color:{MUTED};font-weight:700;letter-spacing:.8px}}
.signal-value{{font-size:18px;font-weight:800;margin-top:6px;color:{PRIMARY}}}
.signal-text{{font-size:12px;color:{MUTED};margin-top:4px;line-height:1.45}}
.tip{{background:{CARD};border:1px solid #D5E5E2;border-radius:12px;padding:14px 16px;height:100%}}
.tip h4{{margin:0 0 6px;color:{PRIMARY};font-size:15px}}
.tip ul{{margin:0;padding-left:18px;font-size:13.5px;line-height:1.55}}

.badge{{display:inline-block;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700}}
.up{{background:#FCE3DC;color:#9C3A22}}
.down{{background:#D7EEEA;color:{PRIMARY}}}
.neutral{{background:#E4E7EB;color:{MUTED}}}

.stButton>button,.stDownloadButton>button{{border-radius:10px;border:1px solid {SECONDARY};background:{CARD};color:{PRIMARY};font-weight:600}}
.stButton>button:hover,.stDownloadButton>button:hover{{background:{SECONDARY};color:#fff}}
div[data-testid="stDataFrame"]{{border-radius:12px;overflow:hidden;border:1px solid #D5E5E2}}
[data-testid="stMetric"]{{background:{CARD};border:1px solid #D5E5E2;border-radius:12px;padding:12px}}
div[data-testid="stExpander"]{{background:{CARD};border-radius:10px}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------
# UI HELPERS
# ------------------------------------------------------------
def kpi(label, value, sub="", icon=""):
    size = "" if len(str(value)) <= 10 else ' style="font-size:19px;line-height:1.25"'   # long names fit without mid-word breaks
    st.markdown(f"""<div class="card"><span class="k-icon">{icon}</span>
    <div class="k-label">{label}</div><div class="k-value"{size}>{value}</div>
    <div class="k-sub">{sub}</div></div>""", unsafe_allow_html=True)


def header(title, sub):
    st.markdown(f'<div class="page-title">{title}</div><div class="page-sub">{sub}</div>', unsafe_allow_html=True)


def section(title, caption=""):
    html = f'<div class="section">{title}</div>'
    if caption:
        html += f'<div class="caption">{caption}</div>'
    st.markdown(html, unsafe_allow_html=True)


def insight(title, body, kind=""):
    st.markdown(f'<div class="insight {kind}"><div class="insight-title">{title}</div>'
                f'<div class="insight-body">{body}</div></div>', unsafe_allow_html=True)


def explain(text):
    """'Explain this chart' expander placed under a main chart."""
    with st.expander("ℹ️ Explain this chart"):
        st.write(text)


def chart(fig, explanation=None, height=None):
    """Render a Plotly figure with the shared style and an optional explanation expander."""
    if height:
        style(fig, height)
    st.plotly_chart(fig, theme=None, config={"displaylogo": False})
    if explanation:
        explain(explanation)


def badge(v):
    """Coloured badge for a percentage change (rise = coral, fall = teal)."""
    if v is None or v != v:
        return '<span class="badge neutral">n/a</span>'
    if v > 0:
        return f'<span class="badge up">↑ {v:.1f}%</span>'
    if v < 0:
        return f'<span class="badge down">↓ {abs(v):.1f}%</span>'
    return '<span class="badge neutral">→ 0.0%</span>'
