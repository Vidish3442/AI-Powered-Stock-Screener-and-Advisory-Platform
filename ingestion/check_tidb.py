"""
Quick diagnostic: check TiDB Cloud connection and table contents.
Run from ingestion/ folder:
    python check_tidb.py
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.tidb")

from db import get_db

db  = get_db()
cur = db.cursor()

# ── 1. List tables ────────────────────────────────────────────────────────────
cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]
print(f"\n📋 Tables in database: {tables}\n")

# ── 2. Row counts ─────────────────────────────────────────────────────────────
for tbl in ["stocks", "fundamentals", "quarterly_finance", "analyst_targets"]:
    if tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cur.fetchone()[0]
        print(f"  {tbl:<25} → {count:>5} rows")
    else:
        print(f"  {tbl:<25} → ❌ TABLE MISSING")

# ── 3. Sample stocks ─────────────────────────────────────────────────────────
print()
if "stocks" in tables:
    cur.execute("SELECT stock_id, symbol, company_name, sector FROM stocks LIMIT 10")
    rows = cur.fetchall()
    if rows:
        print("Sample stocks:")
        for r in rows:
            print(f"  {r[0]:>3}  {r[1]:<8} {r[2][:35]:<35} {r[3]}")
    else:
        print("⚠️  stocks table is EMPTY")

cur.close()
db.close()
