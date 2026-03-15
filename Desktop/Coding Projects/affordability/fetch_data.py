"""
fetch_data.py — Download FRED series and cache to data/
Run: python fetch_data.py
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from fredapi import Fred

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY not found. Create a .env file with FRED_API_KEY=your_key")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CACHE_MAX_AGE_HOURS = 24

SERIES = {
    # Mortgage rates
    "MORTGAGE30US": "30-Year Fixed Mortgage Rate",
    "MORTGAGE15US": "15-Year Fixed Mortgage Rate",
    # Treasury rates
    "GS10": "10-Year Treasury Rate",
    "GS2": "2-Year Treasury Rate",
    "GS30": "30-Year Treasury Rate",
    # Fed policy
    "FEDFUNDS": "Effective Federal Funds Rate",
    "DFEDTARU": "Fed Funds Target Upper",
    "DFEDTARL": "Fed Funds Target Lower",
    # Real rates
    "DFII10": "10-Year TIPS Real Rate",
    # Home prices
    "CSUSHPISA": "Case-Shiller Home Price Index",
    "MSPUS": "Median Sales Price of Houses Sold",
}


def is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < CACHE_MAX_AGE_HOURS


def fetch_all():
    fred = Fred(api_key=FRED_API_KEY)

    for series_id, description in SERIES.items():
        cache_path = DATA_DIR / f"{series_id}.csv"

        if is_cache_fresh(cache_path):
            print(f"  [cached] {series_id} — {description}")
            continue

        print(f"  [fetch]  {series_id} — {description}")
        data = fred.get_series(series_id)
        df = data.to_frame(name="value")
        df.index.name = "date"
        df.to_csv(cache_path)

    print(f"\nAll series saved to {DATA_DIR}/")


if __name__ == "__main__":
    print("Fetching FRED data...\n")
    fetch_all()
