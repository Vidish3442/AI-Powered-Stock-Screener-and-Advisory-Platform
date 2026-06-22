"""
Full data-ingestion pipeline.
  Source : yfinance (all market data)
  Target : TiDB Cloud (via .env.tidb)

Run:
    cd ingestion
    python run_all.py
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load TiDB env before anything else
load_dotenv(Path(__file__).resolve().parent.parent / ".env.tidb")


def header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def step(n: int, title: str):
    print(f"\n{'─' * 60}")
    print(f"  STEP {n} ▶  {title}")
    print(f"{'─' * 60}")


def check_deps():
    """Verify yfinance and DB connection before running pipeline."""
    header("Pre-flight checks")

    # 1. yfinance
    try:
        import yfinance as yf
        info = yf.Ticker("AAPL").info
        if info and info.get("symbol"):
            print("✅ yfinance  — OK")
        else:
            print("⚠️  yfinance installed but returned empty data (network issue?)")
    except ImportError:
        print("❌ yfinance not installed — run: pip install yfinance")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  yfinance warning: {e}")

    # 2. TiDB Cloud config
    import os
    required = ["TIDB_HOST", "TIDB_USER", "TIDB_PASSWORD"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"❌ Missing TiDB env vars: {', '.join(missing)}")
        print("   Check your .env.tidb file.")
        sys.exit(1)
    print(f"✅ TiDB config — host={os.getenv('TIDB_HOST')}")

    # 3. DB connectivity
    try:
        from db import get_db
        db = get_db()
        db.close()
    except Exception as e:
        print(f"❌ Cannot connect to TiDB Cloud: {e}")
        sys.exit(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stock Screener ingestion pipeline")
    parser.add_argument("--from", dest="from_step", type=int, default=1,
                        choices=[1, 2, 3, 4],
                        help="Resume from step: 1=stocks 2=fundamentals 3=quarterly 4=analyst")
    args = parser.parse_args()

    started = datetime.now()
    header(f"STOCK SCREENER  ·  INGESTION PIPELINE  ·  {started:%Y-%m-%d %H:%M:%S}")
    print("  Source : yfinance")
    print("  Target : TiDB Cloud")
    if args.from_step > 1:
        print(f"  ⏩  Resuming from step {args.from_step}")

    check_deps()

    try:
        if args.from_step <= 1:
            step(1, "Stock information")
            from ingest_stocks import ingest_stocks
            ingest_stocks()
            time.sleep(2)

        if args.from_step <= 2:
            step(2, "Fundamental metrics")
            from ingest_fundamentals import ingest_fundamentals
            ingest_fundamentals()
            time.sleep(2)

        if args.from_step <= 3:
            step(3, "Quarterly financials")
            from ingest_quarterly_financials import ingest_quarterly
            ingest_quarterly()
            time.sleep(2)

        step(4, "Analyst targets")
        from ingest_analyst_targets import ingest_analyst_targets
        ingest_analyst_targets()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted — you can re-run individual steps:")
        print("    python ingest_stocks.py")
        print("    python ingest_fundamentals.py")
        print("    python ingest_quarterly_financials.py")
        print("    python ingest_analyst_targets.py")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        sys.exit(1)

    finished = datetime.now()
    header("PIPELINE COMPLETE")
    print(f"  Started  : {started:%H:%M:%S}")
    print(f"  Finished : {finished:%H:%M:%S}")
    print(f"  Duration : {finished - started}")
    print()


if __name__ == "__main__":
    main()
