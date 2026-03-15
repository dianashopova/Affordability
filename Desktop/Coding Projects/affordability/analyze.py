"""
analyze.py — Load cached FRED data and compute affordability metrics.
Returns a dict of DataFrames consumed by dashboard.py.
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")


def load(series_id: str) -> pd.Series:
    path = DATA_DIR / f"{series_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run fetch_data.py first.")
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df["value"].dropna()


def monthly_payment(price: float, annual_rate_pct: float, down_pct: float = 0.20, years: int = 30) -> float:
    """Standard amortization payment formula."""
    if annual_rate_pct <= 0:
        return 0.0
    principal = price * (1 - down_pct)
    r = (annual_rate_pct / 100) / 12  # monthly rate
    n = years * 12
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def build_metrics() -> dict:
    # --- Load raw series ---
    m30 = load("MORTGAGE30US")
    m15 = load("MORTGAGE15US")
    gs10 = load("GS10")
    gs2 = load("GS2")
    gs30 = load("GS30")
    fedfunds = load("FEDFUNDS")
    fed_upper = load("DFEDTARU")
    fed_lower = load("DFEDTARL")
    tips10 = load("DFII10")
    cshiller = load("CSUSHPISA")
    median_price = load("MSPUS")

    # --- Rates panel: align to monthly, resample to end-of-month ---
    rates = pd.DataFrame({
        "30yr Mortgage": m30,
        "15yr Mortgage": m15,
        "10yr Treasury": gs10,
        "2yr Treasury": gs2,
        "30yr Treasury": gs30,
        "Fed Funds Rate": fedfunds,
        "Fed Funds Upper": fed_upper,
        "Fed Funds Lower": fed_lower,
        "10yr Real Rate (TIPS)": tips10,
    }).resample("ME").last()

    # --- Spread metrics ---
    spreads = pd.DataFrame({
        "Mortgage Spread (30yr - 10yr Tsy)": m30 - gs10,
        "Yield Curve (10yr - 2yr)": gs10 - gs2,
        "Real Mortgage Rate (30yr - TIPS)": m30 - tips10,
    }).resample("ME").last()

    # --- Home prices ---
    prices = pd.DataFrame({
        "Case-Shiller Index": cshiller,
        "Median Sale Price ($)": median_price,
    }).resample("ME").last()

    # Normalize Case-Shiller to 100 at Jan 2000
    base = cshiller.resample("ME").last()
    jan2000 = base.loc["2000-01-01":"2000-02-01"].iloc[0] if not base.loc["2000":"2000-02"].empty else base.iloc[0]
    prices["Case-Shiller (rebased 2000=100)"] = (cshiller.resample("ME").last() / jan2000) * 100

    # --- Monthly payment on median home ---
    # Align median price (quarterly) with monthly mortgage rate
    price_monthly = median_price.resample("ME").last().ffill()
    rate_monthly = m30.resample("ME").last()
    aligned = pd.DataFrame({"price": price_monthly, "rate": rate_monthly}).dropna()

    aligned["monthly_payment"] = aligned.apply(
        lambda row: monthly_payment(row["price"], row["rate"]), axis=1
    )

    # --- Statistical summary: latest, 1yr ago, 5yr ago, historical avg ---
    key_series = {
        "30yr Mortgage Rate (%)": m30,
        "10yr Treasury Rate (%)": gs10,
        "Fed Funds Rate (%)": fedfunds,
        "10yr Real Rate TIPS (%)": tips10,
        "Mortgage Spread vs 10yr (%)": (m30 - gs10).resample("ME").last(),
        "Yield Curve 10yr-2yr (%)": (gs10 - gs2).resample("ME").last(),
        "Median Home Price ($)": median_price,
        "Case-Shiller Index": cshiller,
    }

    summary_rows = []
    for label, series in key_series.items():
        s = series.dropna()
        latest_date = s.index[-1]
        def _get(offset_years):
            target = latest_date - pd.DateOffset(years=offset_years)
            idx = s.index.get_indexer([target], method="nearest")[0]
            return s.iloc[idx]

        summary_rows.append({
            "Metric": label,
            "Latest": round(s.iloc[-1], 2),
            "1yr Ago": round(_get(1), 2),
            "5yr Ago": round(_get(5), 2),
            "10yr Avg": round(s[s.index >= s.index[-1] - pd.DateOffset(years=10)].mean(), 2),
            "All-Time Avg": round(s.mean(), 2),
            "All-Time Min": round(s.min(), 2),
            "All-Time Max": round(s.max(), 2),
        })

    summary = pd.DataFrame(summary_rows).set_index("Metric")

    return {
        "rates": rates,
        "spreads": spreads,
        "prices": prices,
        "payment": aligned[["monthly_payment"]],
        "summary": summary,
        "latest_date": rates.index[-1].strftime("%B %d, %Y"),
    }
