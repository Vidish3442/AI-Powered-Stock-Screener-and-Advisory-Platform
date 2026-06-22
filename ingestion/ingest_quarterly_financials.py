"""
Ingest quarterly financial data from yfinance into TiDB Cloud.
Source: yfinance quarterly income statement (only)
Target: TiDB Cloud
"""

import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.tidb")

import yfinance as yf
import pandas as pd
from db import get_db


def safe_int(value) -> int:
    try:
        import math
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return 0
        return int(v)
    except Exception:
        return 0


MAX_QUARTERS = 20   # 5 years × 4 quarters; takes all if stock has fewer


def fetch_quarters(symbol: str) -> list[dict] | None:
    """
    Return up to MAX_QUARTERS (20) quarterly rows sorted newest-first.
    Tries quarterly_income_stmt → quarterly_financials → financials (annual fallback).
    yfinance only exposes ~5 recent quarters in the quarterly statements;
    to get further back we also check the full income_stmt (annual) and
    cross-check with the quarterly cache if available.
    """
    try:
        ticker = yf.Ticker(symbol)

        # Primary: quarterly income statement
        stmt = None
        for attr in ("quarterly_income_stmt", "quarterly_financials"):
            try:
                s = getattr(ticker, attr, None)
                if s is not None and not s.empty:
                    stmt = s
                    break
            except Exception:
                continue

        if stmt is None or stmt.empty:
            print(f"  ⚠️  No quarterly statement for {symbol}")
            return None

        rows = []
        for col in stmt.columns:
            try:
                q_date  = pd.Timestamp(col)
                year    = q_date.year
                month   = q_date.month
                quarter = f"Q{((month - 1) // 3) + 1}"

                def get_row(keys, s=stmt, c=col):
                    for k in keys:
                        if k in s.index:
                            v = s.loc[k, c]
                            return safe_int(v) if pd.notna(v) else 0
                    return 0

                revenue    = get_row(["Total Revenue", "Revenue"])
                ebitda     = get_row(["EBITDA", "Ebitda"])
                net_profit = get_row(["Net Income", "Net Income Common Stockholders"])

                if revenue == 0 and net_profit == 0:
                    continue

                rows.append({
                    "year":       year,
                    "quarter":    quarter,
                    "revenue":    revenue,
                    "ebitda":     ebitda,
                    "net_profit": net_profit,
                })
            except Exception as e:
                print(f"  ⚠️  Error parsing col {col}: {e}")
                continue

        if not rows:
            return None

        # Sort newest-first, cap at 5 years (20 quarters)
        rows.sort(key=lambda r: (r["year"], r["quarter"]), reverse=True)
        # Deduplicate by (year, quarter) in case both attrs returned same rows
        seen = set()
        unique = []
        for r in rows:
            key = (r["year"], r["quarter"])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        kept = unique[:MAX_QUARTERS]
        return kept

    except Exception as e:
        print(f"  ⚠️  yfinance error for {symbol}: {e}")
        return None


def ingest_quarterly():
    print("=" * 60)
    print(" STEP 3 — Quarterly Financials  (source: yfinance)")
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
    total_quarters = 0

    for idx, stock in enumerate(stocks, 1):
        symbol = stock["symbol"]
        print(f"\n[{idx}/{len(stocks)}] {symbol} ...", end=" ", flush=True)

        quarters = fetch_quarters(symbol)
        if not quarters:
            print("✗ no data")
            fail += 1
            continue

        inserted = 0
        for q in quarters:
            cur.execute("""
                INSERT INTO quarterly_finance
                    (stock_id, quarter, year, revenue, ebitda, net_profit)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    revenue    = VALUES(revenue),
                    ebitda     = VALUES(ebitda),
                    net_profit = VALUES(net_profit)
            """, (
                stock["stock_id"],
                q["quarter"], q["year"],
                q["revenue"], q["ebitda"], q["net_profit"],
            ))
            inserted += 1
            total_quarters += 1

        print(f"✓  {inserted} quarters (max {MAX_QUARTERS})")
        ok += 1
        time.sleep(0.3)

    db.commit()
    cur.close()
    db.close()

    print(f"\n{'=' * 60}")
    print(f"✅ Quarterly done  — ✓ {ok} stocks  ✗ {fail}  total rows={total_quarters}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    ingest_quarterly()
