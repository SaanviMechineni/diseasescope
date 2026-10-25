"""India choropleth: local-first GeoJSON loading, per-state dissolve and name matching."""
import json
from pathlib import Path

import numpy as np
import plotly.express as px
import requests

from theme import SEQUENTIAL, style

GEO_FILE = Path(__file__).resolve().parent / "data" / "india_states.geojson"
GEO_URL = "https://raw.githubusercontent.com/india-in-data/india-states-2019/master/india_states.geojson"

# Dataset name -> GeoJSON ST_NM, for names that differ in spelling.
NAME_FIX = {
    "Andaman and Nicobar Islands": "Andaman & Nicobar Island",
    "Dadra and Nagar Haveli": "Dadara & Nagar Havelli",
    "Delhi": "NCT of Delhi",
    "Jammu and Kashmir": "Jammu & Kashmir",
}


def _round_coords(rings, nd=3):
    return [[[round(x, nd), round(y, nd)] for x, y in ring] for ring in rings]


def dissolve(geo):
    """Merge all features sharing an ST_NM into one MultiPolygon.

    The source file splits states into many pieces (271 features for 37 names; West
    Bengal alone has 88). Plotly draws only the FIRST feature per id, which for UP,
    MP, Bihar, West Bengal and Karnataka is a tiny sliver - that is why they appeared
    blank. Empty polygons are dropped and coordinates rounded to ~100 m to cut size.
    """
    merged = {}
    for f in geo["features"]:
        name = f["properties"].get("ST_NM")
        g = f.get("geometry") or {}
        polys = g.get("coordinates", []) if g.get("type") == "MultiPolygon" else [g.get("coordinates", [])]
        polys = [_round_coords(p) for p in polys if p and p[0]]
        merged.setdefault(name, []).extend(polys)
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": n, "properties": {"ST_NM": n},
         "geometry": {"type": "MultiPolygon", "coordinates": p}}
        for n, p in merged.items() if p]}


def load_geojson():
    """Load the boundaries from data/ first; fall back to the GitHub URL (and save it)."""
    source = "local file"
    if GEO_FILE.exists():
        geo = json.loads(GEO_FILE.read_text(encoding="utf-8"))
    else:
        r = requests.get(GEO_URL, timeout=20)
        r.raise_for_status()
        geo = r.json()
        source = "downloaded from GitHub"
        try:
            GEO_FILE.write_text(json.dumps(geo), encoding="utf-8")
        except OSError:
            pass
    return dissolve(geo), source


def _norm(s):
    return " ".join(str(s).lower().replace("&", "and").replace(".", "").replace("-", " ").split())


def match_states(states, geo):
    """Map dataset state names to GeoJSON names; returns (mapping, unmatched list)."""
    lookup = {_norm(f["properties"]["ST_NM"]): f["properties"]["ST_NM"] for f in geo["features"]}
    mapping, unmatched = {}, []
    for s in states:
        target = NAME_FIX.get(s, s)
        m = lookup.get(_norm(target))
        if m:
            mapping[s] = m
        else:
            unmatched.append(s)
    return mapping, unmatched


def india_map(geo, frame, color, label, hover=None, discrete_map=None, height=560, range_color=None):
    """Draw one choropleth of India.

    frame: one row per state with column 'State' and the `color` column.
    discrete_map: pass a {category: colour} dict for categorical maps (e.g. clusters).
    Returns (figure, unmatched dataset states, GeoJSON states with no data).
    """
    x = frame.copy()
    mapping, unmatched = match_states(x["State"].unique(), geo)
    x["GeoState"] = x["State"].map(mapping)
    x = x.dropna(subset=["GeoState"])
    hover = hover or {}
    hover_data = {"GeoState": False, **hover}
    kwargs = dict(geojson=geo, locations="GeoState", featureidkey="properties.ST_NM",
                  color=color, hover_name="State", hover_data=hover_data, labels={color: label})
    if discrete_map:
        fig = px.choropleth(x, color_discrete_map=discrete_map, **kwargs)
    else:
        # Log colour scale: a few small UTs have values 10x the rest, which would
        # otherwise wash every other state out to the palest colour.
        x["_log"] = np.log10(x[color].clip(lower=0) + 1)
        kwargs.update(color="_log", hover_data={**hover_data, "_log": False, color: hover.get(color, ":,.2f")})
        fig = px.choropleth(x, color_continuous_scale=SEQUENTIAL, range_color=range_color, **kwargs)
        top = float(x["_log"].max()) if len(x) else 1
        ticks = [v for v in [0, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000] if np.log10(v + 1) <= top + 1e-9]
        fig.update_layout(coloraxis_colorbar=dict(title=label + "<br>(log scale)", thickness=14, len=.7,
                                                  tickvals=[np.log10(v + 1) for v in ticks], ticktext=[f"{v:,}" for v in ticks]))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_traces(marker_line_color="#FFFFFF", marker_line_width=.6)
    style(fig, height)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    no_data = sorted({f["properties"]["ST_NM"] for f in geo["features"]} - set(mapping.values()))
    return fig, unmatched, no_data
