"""
Generate and ingest analyst target data for all stocks in TiDB Cloud.
Uses fundamental data already in the DB (current_price, pe_ratio) to
produce realistic-looking analyst recommendations.
Source: derived from existing fundamentals (no external API needed)
Target: TiDB Cloud
"""

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.tidb")

from db import get_db

FIRMS = [
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America",
    "Citigroup", "Wells Fargo", "Deutsche Bank", "Barclays", "UBS", "Credit Suisse",
]


def make_recommendation(symbol: str, pe_ratio: float, current_price: float) -> dict:
    """
    Derive a realistic analyst target/recommendation from fundamentals.
    Logic:
      PE < 15  → Buy  (+10-15 % target)
      PE < 25  → Hold (±5 % target)
      PE >= 25 → Sell (-5-10 % target)
    """
    seed_a = sum(ord(c) for c in symbol) % 100
    seed_b = sum(ord(c) * i for i, c in enumerate(symbol, 1)) % 100

    if pe_ratio > 0 and pe_ratio < 15:
        multiplier   = 1.10 + (seed_a % 20) * 0.005   # 1.10 – 1.195
        rec          = "Buy"
    elif pe_ratio > 0 and pe_ratio < 25:
        multiplier   = 0.975 + (seed_a % 10) * 0.005  # 0.975 – 1.022
        rec          = "Hold"
    else:
        multiplier   = 0.88 + (seed_a % 15) * 0.004   # 0.88 – 0.936
        rec          = "Sell"

    target_price = round(current_price * multiplier, 2)
    firm         = FIRMS[seed_b % len(FIRMS)]

    return {
        "target_price":  target_price,
        "current_price": round(current_price, 2),
        "recommendation": rec,
        "analyst_firm":  firm,
    }


def ingest_analyst_targets():
    print("=" * 60)
    print(" STEP 4 — Analyst Targets  (derived from fundamentals)")
    print("=" * 60)

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT s.stock_id, s.symbol,
               COALESCE(f.pe_ratio, 0)      AS pe_ratio,
               COALESCE(f.current_price, 0) AS current_price
        FROM stocks s
        LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
        ORDER BY s.stock_id
    """)
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

        price = float(stock["current_price"])
        pe    = float(stock["pe_ratio"])

        # If we have no price, manufacture a rough one from symbol hash
        if price <= 0:
            price = 20 + (sum(ord(c) for c in symbol) % 100) * 2.5

        rec = make_recommendation(symbol, pe, price)

        cur.execute("""
            INSERT INTO analyst_targets
                (stock_id, target_price, current_price, recommendation, analyst_firm, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                target_price   = VALUES(target_price),
                current_price  = VALUES(current_price),
                recommendation = VALUES(recommendation),
                analyst_firm   = VALUES(analyst_firm),
                updated_at     = NOW()
        """, (
            stock["stock_id"],
            rec["target_price"], rec["current_price"],
            rec["recommendation"], rec["analyst_firm"],
        ))

        upside = ((rec["target_price"] - rec["current_price"]) / rec["current_price"]) * 100
        print(
            f"✓  {rec['recommendation']:4s}  "
            f"target=${rec['target_price']:.2f}  "
            f"current=${rec['current_price']:.2f}  "
            f"upside={upside:+.1f}%"
        )
        ok += 1

    db.commit()
    cur.close()
    db.close()

    print(f"\n{'=' * 60}")
    print(f"✅ Analyst targets done  — ✓ {ok}  ✗ {fail}")
    print("⚠️  Disclaimer: targets are for demo purposes, NOT financial advice")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    ingest_analyst_targets()
