"""
dashboard.py — Generate standalone HTML affordability dashboard.
Run: python dashboard.py
Output: output/dashboard.html
"""

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from analyze import build_metrics

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

COLORS = {
    "30yr Mortgage": "#e63946",
    "15yr Mortgage": "#f4a261",
    "10yr Treasury": "#457b9d",
    "2yr Treasury": "#a8dadc",
    "30yr Treasury": "#1d3557",
    "Fed Funds Rate": "#6a4c93",
    "Fed Funds Upper": "#b5838d",
    "Fed Funds Lower": "#b5838d",
    "10yr Real Rate (TIPS)": "#2a9d8f",
    "Mortgage Spread (30yr - 10yr Tsy)": "#e63946",
    "Yield Curve (10yr - 2yr)": "#457b9d",
    "Real Mortgage Rate (30yr - TIPS)": "#2a9d8f",
    "Case-Shiller Index": "#e9c46a",
    "Median Sale Price ($)": "#f4a261",
}

BG = "#0f172a"
PAPER_BG = "#1e293b"
GRID = "#334155"
TEXT = "#e2e8f0"
ACCENT = "#38bdf8"


def apply_dark_theme(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=ACCENT), x=0.01),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, system-ui, sans-serif"),
        legend=dict(bgcolor=PAPER_BG, bordercolor=GRID, borderwidth=1),
        margin=dict(l=60, r=30, t=50, b=40),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, showspikes=True, spikecolor=ACCENT)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def make_rates_chart(rates: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in ["30yr Mortgage", "10yr Treasury", "Fed Funds Rate", "10yr Real Rate (TIPS)"]:
        if col in rates.columns:
            fig.add_trace(go.Scatter(
                x=rates.index, y=rates[col], name=col,
                line=dict(color=COLORS.get(col), width=2),
                hovertemplate="%{y:.2f}%",
            ))
    fig.add_hline(y=0, line_dash="dot", line_color=GRID)
    apply_dark_theme(fig, "Interest Rate Environment")
    fig.update_yaxes(ticksuffix="%")
    return fig


def make_spreads_chart(spreads: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in spreads.columns:
        fig.add_trace(go.Scatter(
            x=spreads.index, y=spreads[col], name=col,
            line=dict(color=COLORS.get(col), width=2),
            hovertemplate="%{y:.2f}%",
        ))
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8", line_width=1)
    apply_dark_theme(fig, "Rate Spreads & Yield Curve")
    fig.update_yaxes(ticksuffix="%")
    return fig


def make_prices_chart(prices: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "Case-Shiller (rebased 2000=100)" in prices.columns:
        fig.add_trace(go.Scatter(
            x=prices.index,
            y=prices["Case-Shiller (rebased 2000=100)"],
            name="Case-Shiller (2000=100)",
            line=dict(color=COLORS["Case-Shiller Index"], width=2),
            hovertemplate="%{y:.1f}",
        ), secondary_y=False)

    if "Median Sale Price ($)" in prices.columns:
        fig.add_trace(go.Scatter(
            x=prices.index,
            y=prices["Median Sale Price ($)"],
            name="Median Sale Price",
            line=dict(color=COLORS["Median Sale Price ($)"], width=2),
            hovertemplate="$%{y:,.0f}",
        ), secondary_y=True)

    apply_dark_theme(fig, "Home Prices")
    fig.update_yaxes(title_text="Case-Shiller Index (2000=100)", secondary_y=False, gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(title_text="Median Sale Price", secondary_y=True, tickprefix="$", tickformat=",", gridcolor=GRID, zerolinecolor=GRID)
    return fig


def make_payment_chart(payment: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=payment.index,
        y=payment["monthly_payment"],
        name="Est. Monthly P&I",
        line=dict(color="#e63946", width=2),
        fill="tozeroy",
        fillcolor="rgba(230,57,70,0.12)",
        hovertemplate="$%{y:,.0f}",
    ))
    apply_dark_theme(fig, "Estimated Monthly Payment on Median Home (20% Down, 30yr Fixed)")
    fig.update_yaxes(tickprefix="$", tickformat=",")
    return fig


def make_all_rates_chart(rates: pd.DataFrame) -> go.Figure:
    """Full rate comparison: all series on one chart."""
    fig = go.Figure()
    cols = [c for c in rates.columns if c not in ("Fed Funds Upper", "Fed Funds Lower")]
    for col in cols:
        fig.add_trace(go.Scatter(
            x=rates.index, y=rates[col], name=col,
            line=dict(color=COLORS.get(col), width=1.5),
            hovertemplate="%{y:.2f}%",
        ))
    # Fed funds target band as shaded area
    if "Fed Funds Upper" in rates.columns and "Fed Funds Lower" in rates.columns:
        fig.add_trace(go.Scatter(
            x=list(rates.index) + list(rates.index[::-1]),
            y=list(rates["Fed Funds Upper"].ffill()) + list(rates["Fed Funds Lower"].ffill()[::-1]),
            fill="toself",
            fillcolor="rgba(106,76,147,0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Fed Target Range",
            hoverinfo="skip",
        ))
    fig.add_hline(y=0, line_dash="dot", line_color=GRID)
    apply_dark_theme(fig, "All Rates: Full Comparison")
    fig.update_yaxes(ticksuffix="%")
    return fig


def summary_table_html(summary: pd.DataFrame, latest_date: str) -> str:
    def fmt(val, metric):
        if "$" in metric:
            return f"${val:,.0f}"
        return f"{val:.2f}%"

    rows = ""
    for metric, row in summary.iterrows():
        cells = "".join(
            f"<td>{fmt(row[col], metric)}</td>"
            for col in ["Latest", "1yr Ago", "5yr Ago", "10yr Avg", "All-Time Avg", "All-Time Min", "All-Time Max"]
        )
        rows += f"<tr><td class='metric-name'>{metric}</td>{cells}</tr>\n"

    return f"""
<div class="section">
  <h2>Rate &amp; Price Snapshot <span class="date-badge">as of {latest_date}</span></h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Latest</th>
          <th>1yr Ago</th>
          <th>5yr Ago</th>
          <th>10yr Avg</th>
          <th>All-Time Avg</th>
          <th>All-Time Min</th>
          <th>All-Time Max</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>
"""


def build_html(figures: list[tuple[str, go.Figure]], summary_html: str) -> str:
    chart_divs = ""
    for section_title, fig in figures:
        div_html = pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})
        chart_divs += f'<div class="section"><h2>{section_title}</h2>{div_html}</div>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Home Affordability Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: {BG};
    color: {TEXT};
    font-family: Inter, system-ui, sans-serif;
    font-size: 14px;
    line-height: 1.5;
  }}
  header {{
    background: {PAPER_BG};
    border-bottom: 1px solid {GRID};
    padding: 20px 32px;
  }}
  header h1 {{ font-size: 22px; color: {ACCENT}; font-weight: 700; }}
  header p {{ color: #94a3b8; margin-top: 4px; font-size: 13px; }}
  main {{ max-width: 1400px; margin: 0 auto; padding: 24px 24px 48px; display: flex; flex-direction: column; gap: 24px; }}
  .section {{
    background: {PAPER_BG};
    border: 1px solid {GRID};
    border-radius: 10px;
    padding: 20px 20px 12px;
  }}
  .section h2 {{
    font-size: 15px;
    font-weight: 600;
    color: {TEXT};
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .date-badge {{
    font-size: 11px;
    font-weight: 400;
    background: {GRID};
    color: #94a3b8;
    padding: 2px 8px;
    border-radius: 99px;
  }}
  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{
    text-align: left;
    padding: 8px 12px;
    color: #94a3b8;
    font-weight: 500;
    border-bottom: 1px solid {GRID};
    white-space: nowrap;
  }}
  td {{
    padding: 8px 12px;
    border-bottom: 1px solid {GRID};
    white-space: nowrap;
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .metric-name {{ color: {ACCENT}; font-weight: 500; }}
</style>
</head>
<body>
<header>
  <h1>Home Affordability Dashboard</h1>
  <p>FRED data &mdash; Mortgage rates, treasury yields, home prices, and affordability metrics</p>
</header>
<main>
  {chart_divs}
  {summary_html}
</main>
</body>
</html>"""


def main():
    print("Building metrics...")
    metrics = build_metrics()

    figures = [
        ("Interest Rate Environment", make_rates_chart(metrics["rates"])),
        ("All Rates: Full Comparison", make_all_rates_chart(metrics["rates"])),
        ("Rate Spreads & Yield Curve", make_spreads_chart(metrics["spreads"])),
        ("Home Prices", make_prices_chart(metrics["prices"])),
        ("Estimated Monthly Payment on Median Home", make_payment_chart(metrics["payment"])),
    ]

    summary_html = summary_table_html(metrics["summary"], metrics["latest_date"])
    html = build_html(figures, summary_html)

    out_path = OUTPUT_DIR / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
