"""Shareable state summary report (PDF and HTML), built with matplotlib so no extra packages are needed."""
import base64
import html
import io
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from advisory import ADVICE, DISCLAIMER
from data import DATA_SOURCE_NOTE, LAST_COMPLETE_YEAR
from theme import ALERT, DISEASE_COLORS, MUTED, PRIMARY, SECONDARY, TEXT

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#C9D6D4", "axes.labelcolor": TEXT,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False})


def state_summary(df, state, clusters, forecast, slopes, model_note=""):
    """Collect the key numbers for one state into a plain dict (used by the page and the report)."""
    d = df[df["State"] == state]
    fc = forecast[forecast["State"] == state].set_index("Disease")
    sl = slopes[slopes["State"] == state].set_index("Disease")
    rows = []
    for dis in sorted(d["Disease"].unique()):
        g = d[d["Disease"] == dis].set_index("Year")
        rows.append({"Disease": dis,
                     f"{LAST_COMPLETE_YEAR} incidence": g.loc[LAST_COMPLETE_YEAR, "Incidence_per_100k"],
                     f"{LAST_COMPLETE_YEAR} cases": g.loc[LAST_COMPLETE_YEAR, "Cases"],
                     "Trend %/yr (2019–23)": sl.loc[dis, "Trend_%_per_year"],
                     "Forecast": fc.loc[dis, "Forecast"], "Range low": fc.loc[dis, "Low_P10"],
                     "Range high": fc.loc[dis, "High_P90"]})
    cl = clusters[clusters["State"] == state]
    return {"state": state, "region": d["Region"].iloc[0], "population": int(d["Population_Approx"].iloc[0]),
            "cluster": cl["Cluster"].iloc[0] if not cl.empty else "—", "rows": rows,
            "rising": [r["Disease"] for r in rows if r["Trend %/yr (2019–23)"] > 0],
            "forecast_year": int(forecast["Forecast_Year"].iloc[0]), "history": d,
            "model_note": model_note}


def _trend_fig(s):
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=130)
    for dis, g in s["history"].groupby("Disease"):
        g = g.sort_values("Year")
        ax.plot(g["Year"], g["Incidence_per_100k"], marker="o", lw=2, color=DISEASE_COLORS.get(dis, SECONDARY), label=dis)
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xlabel("Year (2024 provisional)")
    ax.set_ylabel("Incidence per 100k (log scale)")
    ax.set_title(f"{s['state']}: incidence by disease", color=PRIMARY, loc="left", fontweight="bold")
    ax.grid(axis="y", color="#E3EBEA")
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.22))
    fig.tight_layout()
    return fig


def _forecast_fig(s):
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=130)
    names = [r["Disease"].replace(" (Seasonal Influenza-A)", "") for r in s["rows"]]
    last = [r[f"{LAST_COMPLETE_YEAR} incidence"] for r in s["rows"]]
    fc = [r["Forecast"] for r in s["rows"]]
    # Error-bar lengths clipped at 0 as a safety net (matplotlib rejects negative xerr).
    lo = [max(r["Forecast"] - r["Range low"], 0) for r in s["rows"]]
    hi = [max(r["Range high"] - r["Forecast"], 0) for r in s["rows"]]
    y = range(len(names))
    ax.barh([i + .2 for i in y], last, height=.38, color="#93CBC2", label=f"{LAST_COMPLETE_YEAR} actual")
    ax.barh([i - .2 for i in y], fc, height=.38, color=PRIMARY, xerr=[lo, hi], ecolor=ALERT, capsize=3,
            label=f"{s['forecast_year']} forecast (median, P10–P90 range)")
    ax.set_yticks(list(y), names)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("Incidence per 100k (log scale)")
    ax.set_title("Latest complete year vs forecast", color=PRIMARY, loc="left", fontweight="bold")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    return fig


def _fmt(v, nd=None):
    """Format a number; small values get more decimals so they do not show as 0.0."""
    if nd is None:
        nd = 1 if abs(v) >= 10 else 2 if abs(v) >= 0.1 else 3
    return f"{v:,.{nd}f}"


def build_pdf(s):
    """Two-page PDF: key numbers + table, then charts and prevention tips."""
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))   # A4
        fig.text(.07, .95, "DiseaseScope · State Summary", color=SECONDARY, fontsize=10, fontweight="bold")
        fig.text(.07, .91, s["state"], color=PRIMARY, fontsize=24, fontweight="bold")
        fig.text(.07, .885, f"Region: {s['region']}   ·   Approx. population: {s['population']:,}   ·   "
                 f"Generated {date.today():%d %b %Y}", color=MUTED, fontsize=9)
        fig.text(.07, .85, f"Risk cluster (K-Means): {s['cluster']}", fontsize=11, color=TEXT)
        fig.text(.07, .825, "Rising 2019–2023: " + (", ".join(s["rising"]) or "none"), fontsize=11, color=TEXT)
        cols = ["Disease", f"{LAST_COMPLETE_YEAR} inc./100k", "Trend %/yr", f"{s['forecast_year']} forecast", "Range (P10–P90)"]
        cells = [[r["Disease"].replace(" (Seasonal Influenza-A)", ""), _fmt(r[f"{LAST_COMPLETE_YEAR} incidence"]),
                  f"{r['Trend %/yr (2019–23)']:+.1f}", _fmt(r["Forecast"]), f"{_fmt(r['Range low'])}–{_fmt(r['Range high'])}"]
                 for r in s["rows"]]
        ax = fig.add_axes([.07, .6, .86, .2])
        ax.axis("off")
        tb = ax.table(cellText=cells, colLabels=cols, loc="upper left", cellLoc="left",
                      colWidths=[.28, .16, .13, .17, .26])
        tb.auto_set_font_size(False)
        tb.set_fontsize(8)
        tb.scale(1, 1.6)
        for (r, _), c in tb.get_celld().items():
            c.set_edgecolor("#D5E5E2")
            if r == 0:
                c.set_facecolor(PRIMARY)
                c.get_text().set_color("white")
        notes = (DATA_SOURCE_NOTE + " Population is approximate and constant across years. "
                 "2024 is provisional (partial year), so forecasts that use it may be too low. Forecast = median of "
                 "Random Forest trees, range = 10th–90th percentile. " + s["model_note"])
        fig.text(.07, .5, _wrap(notes, 110), fontsize=8, color=MUTED, va="top")
        fig.text(.07, .38, _wrap(DISCLAIMER.replace("**", ""), 110), fontsize=8, color=TEXT, va="top")
        pdf.savefig(fig)
        plt.close(fig)

        page = plt.figure(figsize=(8.27, 11.69))
        for fig_fn, rect in [(_trend_fig, [.05, .62, .9, .33]), (_forecast_fig, [.05, .32, .9, .28])]:
            f = fig_fn(s)
            img = _png(f)
            plt.close(f)
            ax = page.add_axes(rect)
            ax.imshow(plt.imread(io.BytesIO(img)))
            ax.axis("off")
        y = .29
        page.text(.07, y, "Prevention tips", color=PRIMARY, fontsize=13, fontweight="bold")
        for dis in (s["rising"] or [r["Disease"] for r in s["rows"]])[:3]:
            y -= .03
            page.text(.07, y, dis, fontsize=10, fontweight="bold", color=TEXT)
            for tip in ADVICE[dis]["prevention"][:3]:
                y -= .02
                page.text(.09, y, "• " + tip, fontsize=8, color=TEXT)
        pdf.savefig(page)
        plt.close(page)
    return buf.getvalue()


def build_html(s):
    """Self-contained HTML report (charts embedded as images; works offline)."""
    t = _b64(_trend_fig(s))
    f = _b64(_forecast_fig(s))
    rows = "".join(
        f"<tr><td>{html.escape(r['Disease'])}</td><td>{_fmt(r[f'{LAST_COMPLETE_YEAR} incidence'])}</td>"
        f"<td>{r['Trend %/yr (2019–23)']:+.1f}</td><td>{_fmt(r['Forecast'])}</td>"
        f"<td>{_fmt(r['Range low'])}–{_fmt(r['Range high'])}</td></tr>" for r in s["rows"])
    tips = "".join(
        f"<h3>{html.escape(d)}</h3><ul>{''.join(f'<li>{html.escape(x)}</li>' for x in ADVICE[d]['prevention'])}</ul>"
        for d in (s["rising"] or [r["Disease"] for r in s["rows"]])[:3])
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(s['state'])} – DiseaseScope summary</title>
<style>body{{font-family:Inter,Segoe UI,sans-serif;background:#E9F3F2;color:#1F2933;margin:0;padding:24px}}
main{{max-width:900px;margin:auto;background:#fff;border-radius:14px;padding:28px}}h1{{color:#0F4C5C;margin:.2em 0}}
h2{{color:#0F4C5C}}.muted{{color:#52606D;font-size:14px}}table{{border-collapse:collapse;width:100%;font-size:14px}}
th{{background:#0F4C5C;color:#fff;text-align:left}}td,th{{padding:7px 9px;border-bottom:1px solid #D5E5E2}}
img{{max-width:100%}}.note{{background:#FDEBD8;border-radius:10px;padding:12px;font-size:13px}}</style></head><body><main>
<div class="muted">DiseaseScope · State Summary · generated {date.today():%d %b %Y}</div>
<h1>{html.escape(s['state'])}</h1><div class="muted">Region: {s['region']} · Approx. population: {s['population']:,}</div>
<p><b>Risk cluster:</b> {html.escape(s['cluster'])}<br><b>Rising 2019–2023:</b> {html.escape(', '.join(s['rising']) or 'none')}</p>
<table><tr><th>Disease</th><th>{LAST_COMPLETE_YEAR} incidence /100k</th><th>Trend %/yr</th><th>{s['forecast_year']} forecast</th><th>Range (P10–P90)</th></tr>{rows}</table>
<h2>Charts</h2><img src="data:image/png;base64,{t}" alt="Incidence trend by disease"><img src="data:image/png;base64,{f}" alt="Forecast vs latest year">
<h2>Prevention tips</h2>{tips}
<p class="note">{html.escape(DATA_SOURCE_NOTE)}
Population is approximate. 2024 is provisional (partial year). Forecast = median of Random Forest trees, range = 10th–90th percentile.
{html.escape(s['model_note'])}</p>
<p class="muted">{DISCLAIMER.replace('**', '')}</p></main></body></html>""".encode("utf-8")


def _png(fig):
    b = io.BytesIO()
    fig.savefig(b, format="png", bbox_inches="tight")
    return b.getvalue()


def _b64(fig):
    data = base64.b64encode(_png(fig)).decode()
    plt.close(fig)
    return data


def _wrap(text, width):
    import textwrap
    return "\n".join(textwrap.wrap(text, width))
