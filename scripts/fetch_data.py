"""
Muyuan Hog-Cycle Dashboard - Master Data Fetcher
Pulls China hog/feed prices + futures + Muyuan A/H via akshare, folds in the
manually-maintained CSVs (data/manual/), and writes data/live-data.json.
Run locally or via GitHub Actions on a schedule.

On any individual source failure the previous values in live-data.json are
kept, so a flaky soozhu/sina endpoint never blanks the dashboard.

Usage:
    python scripts/fetch_data.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
MANUAL_DIR = DATA_DIR / "manual"
OUTPUT_FILE = DATA_DIR / "live-data.json"
DATA_DIR.mkdir(exist_ok=True)


def load_existing():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def records(df, date_col="date", round_cols=None):
    """DataFrame -> list of dicts with ISO date strings."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")
    if round_cols:
        for c, n in round_cols.items():
            df[c] = pd.to_numeric(df[c], errors="coerce").round(n)
    return json.loads(df.to_json(orient="records"))


# ------------------------------------------------------------- live fetchers

def fetch_hog_index():
    import akshare as ak
    df = ak.index_hog_spot_price().rename(columns={
        "日期": "date", "成交均价": "price", "预售均价": "presale", "成交均重": "weight_kg"})
    return records(df[["date", "price", "presale"]], round_cols={"price": 2, "presale": 2})


def _soozhu(fn_name):
    import akshare as ak
    df = getattr(ak, fn_name)().rename(columns={"日期": "date", "价格": "price"})
    return records(df[["date", "price"]], round_cols={"price": 2})


def _futures(symbol, days=420):
    import akshare as ak
    df = ak.futures_main_sina(symbol).rename(columns={"日期": "date", "收盘价": "close"})
    df["close_kg"] = pd.to_numeric(df["close"], errors="coerce") / 1000.0
    return records(df[["date", "close_kg"]].tail(days), round_cols={"close_kg": 3})


def fetch_muyuan_a():
    import akshare as ak
    df = ak.stock_zh_a_daily(symbol="sz002714", start_date="20210101",
                             end_date=datetime.now().strftime("%Y%m%d"))
    return records(df[["date", "close"]], round_cols={"close": 2})


def fetch_muyuan_h():
    import akshare as ak
    df = ak.stock_hk_daily(symbol="02714")
    return records(df[["date", "close"]], round_cols={"close": 2})


LIVE_SOURCES = {
    "hog_index": fetch_hog_index,                                   # weekly, 2015-
    "hog_spot": lambda: _soozhu("spot_hog_lean_price_soozhu"),      # daily 外三元
    "piglet": lambda: _soozhu("spot_hog_three_way_soozhu"),         # 15kg crossbred, Rmb/head
    "corn": lambda: _soozhu("spot_corn_price_soozhu"),
    "soybean": lambda: _soozhu("spot_soybean_price_soozhu"),
    "feed": lambda: _soozhu("spot_mixed_feed_soozhu"),
    "lh_futures": lambda: _futures("LH0"),
    "corn_futures": lambda: _futures("C0"),
    "meal_futures": lambda: _futures("M0"),
    "muyuan_a": fetch_muyuan_a,
    "muyuan_h": fetch_muyuan_h,
}

MANUAL_FILES = ["sow_inventory", "effective_supply", "street_estimates",
                "distress_events", "price_checkpoints", "muyuan"]


def main():
    print("=" * 60)
    print("Muyuan Hog-Cycle Dashboard - Data Fetcher")
    print(f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 60)

    existing = load_existing()
    output = {"updated_at": datetime.now().isoformat()}
    failures = 0

    for i, (key, fn) in enumerate(LIVE_SOURCES.items(), 1):
        print(f"[{i}/{len(LIVE_SOURCES)}] {key}...", end=" ")
        try:
            output[key] = fn()
            print(f"OK ({len(output[key])} rows)")
        except Exception as e:  # noqa: BLE001 - keep stale data on any failure
            output[key] = existing.get(key, [])
            failures += 1
            print(f"FAIL ({type(e).__name__}) -> kept {len(output[key])} stale rows")

    print("Folding in manual CSVs...")
    output["manual"] = {}
    for name in MANUAL_FILES:
        df = pd.read_csv(MANUAL_DIR / f"{name}.csv")
        output["manual"][name] = json.loads(df.to_json(orient="records"))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[DONE] {OUTPUT_FILE} written, {failures} source(s) fell back to stale data")
    # Exit 0 even with partial failures - stale data beats a red X + no update.


if __name__ == "__main__":
    sys.exit(main())
