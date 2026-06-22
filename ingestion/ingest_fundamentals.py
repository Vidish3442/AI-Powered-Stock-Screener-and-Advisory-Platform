"""
Ingest fundamental metrics from yfinance into TiDB Cloud.
Source: yfinance (only)
Target: TiDB Cloud
"""

import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.tidb")

import yfinance as yf
from db import get_db


def safe_float(value) -> float:
    """Convert to float, returning 0.0 for None / NaN / Inf."""
    try:
        f = float(value)
        import math
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except Exception:
        return 0.0


def safe_int(value) -> int:
    try:
        import math
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0
        return int(f)
    except Exception:
        return 0


def fetch(symbol: str) -> dict | None:
    """Fetch fundamentals from yfinance."""
    try:
        info = yf.Ticker(symbol).info
        if not info or not info.get("symbol"):
            print(f"  ⚠️  No data for {symbol}")
            return None
        return info
    except Exception as e:
        print(f"  ⚠️  yfinance error for {symbol}: {e}")
        return None


def extract(info: dict) -> dict:
    """Pull all fundamental fields from yfinance info dict."""
    return {
        "pe_ratio":      safe_float(info.get("trailingPE") or info.get("forwardPE")),
        "eps":           safe_float(info.get("trailingEps") or info.get("forwardEps")),
        "market_cap":    safe_int(info.get("marketCap")),
        "roe":           safe_float(info.get("returnOnEquity")),
        "debt_equity":   safe_float(info.get("debtToEquity")),
        "price_to_book": safe_float(info.get("priceToBook")),
        "dividend_yield":safe_float(info.get("dividendYield")),
        "profit_margin": safe_float(info.get("profitMargins")),
        "beta":          safe_float(info.get("beta")),
        "current_price": safe_float(
            info.get("currentPrice") or info.get("regularMarketPrice")
        ),
    }


def ingest_fundamentals():
    print("=" * 60)
    print(" STEP 2 — Fundamental Metrics  (source: yfinance)")
    print("=" * 60)

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT stock_id, symbol FROM stocks ORDER BY stock_id")
    stocks = cur.fetchall()

    if not stocks:
        print("❌  No stocks found. Run ingest_stocks.py first.")
        cur.close(); db.close()
        return

    ok = 0
    fail = 0

    for idx, stock in enumerate(stocks, 1):
        symbol = stock["symbol"]
        print(f"\n[{idx}/{len(stocks)}] {symbol} ...", end=" ", flush=True)

        info = fetch(symbol)
        if not info:
            fail += 1
            continue

        d = extract(info)

        # At minimum we need a current price to be useful
        if d["current_price"] <= 0:
            print(f"⚠️  skipped (no current_price)")
            fail += 1
            continue

        cur.execute("""
            INSERT INTO fundamentals
                (stock_id, pe_ratio, eps, market_cap, roe, debt_equity,
                 price_to_book, dividend_yield, profit_margin, beta,
                 current_price, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW())
            ON DUPLICATE KEY UPDATE
                pe_ratio       = VALUES(pe_ratio),
                eps            = VALUES(eps),
                market_cap     = VALUES(market_cap),
                roe            = VALUES(roe),
                debt_equity    = VALUES(debt_equity),
                price_to_book  = VALUES(price_to_book),
                dividend_yield = VALUES(dividend_yield),
                profit_margin  = VALUES(profit_margin),
                beta           = VALUES(beta),
                current_price  = VALUES(current_price),
                updated_at     = NOW()
        """, (
            stock["stock_id"],
            d["pe_ratio"], d["eps"], d["market_cap"],
            d["roe"], d["debt_equity"], d["price_to_book"],
            d["dividend_yield"], d["profit_margin"], d["beta"],
            d["current_price"],
        ))

        print(
            f"✓  price=${d['current_price']:.2f}  "
            f"PE={d['pe_ratio']:.1f}  "
            f"mktcap={d['market_cap']//1_000_000_000:.0f}B"
        )
        ok += 1
        time.sleep(0.3)

    db.commit()
    cur.close()
    db.close()

    print(f"\n{'=' * 60}")
    print(f"✅ Fundamentals done  — ✓ {ok}  ✗ {fail}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    ingest_fundamentals()
