"""
Ingest stock information from yfinance into TiDB Cloud.
Source: yfinance (only)
Target: TiDB Cloud
"""

import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.tidb")

import yfinance as yf
from db import get_db

# ── Stock list ───────────────────────────────────────────────────────────────
SYMBOLS = [
    # US Tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "NFLX", "ADBE",
    "INTC", "AMD", "QCOM", "TXN", "AVGO", "CRM", "ORCL", "IBM", "CSCO", "NOW",
    "SNOW", "PLTR", "UBER", "LYFT", "ABNB", "SHOP", "SQ", "PYPL", "DOCU",
    # US Finance
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK",
    "SCHW", "USB", "PNC", "TFC", "COF", "DFS", "SPGI", "MCO", "ICE", "CME",
    # US Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN",
    "GILD", "REGN", "VRTX", "ISRG", "BSX", "MDT", "ZTS", "ELV", "HUM", "CVS",
    # US Consumer (Discretionary + Staples)
    "WMT", "HD", "PG", "KO", "PEP", "COST", "TGT", "LOW", "SBUX", "MCD",
    "NKE", "DIS", "F", "GM", "YUM", "CMG", "EBAY", "ETSY",
    # US Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO", "PSX", "OXY",
    # US Industrials
    "BA", "CAT", "HON", "GE", "MMM", "RTX", "LMT", "NOC", "DE", "UPS",
    "FDX", "CSX", "UNP", "NSC", "WM", "ETN", "EMR", "ROK", "ITW",
    # US Real Estate / Utilities
    "AMT", "PLD", "CCI", "EQIX", "O", "SPG", "PSA", "DLR",
    "NEE", "DUK", "SO", "AEP", "SRE", "EXC", "XEL",
    # US Small/Mid Cap Growth
    "CRWD", "ZS", "DDOG", "NET", "MDB", "BILL", "HUBS", "OKTA",
    "AFRM", "HOOD", "SOFI", "COIN", "RBLX", "ROKU", "SPOT", "DUOL", "APP",
    # International ADRs — India
    "INFY", "HDB", "WIT", "IBN",
    # International ADRs — China
    "BABA", "JD", "PDD", "BIDU", "NIO", "NTES",
    # International ADRs — Europe
    "ASML", "NVO", "UL", "SNY", "DEO", "SAP", "LOGI", "ABB", "BP",
    "SHEL", "AZN", "GSK", "RIO", "BHP",
    # International ADRs — Asia Pacific
    "TM", "HMC", "SONY", "TSM", "MUFG", "KB",
]

# ── ADR country map ───────────────────────────────────────────────────────────
ADR_MAP = {
    "INFY": "India",  "HDB": "India",  "WIT": "India",  "IBN": "India",
    "BABA": "China",  "JD": "China",   "PDD": "China",  "BIDU": "China",
    "NIO":  "China",  "NTES": "China",
    "ASML": "Netherlands", "NVO": "Denmark",
    "UL":   "United Kingdom", "SNY": "France", "DEO": "United Kingdom",
    "SAP":  "Germany", "LOGI": "Switzerland", "ABB": "Switzerland",
    "BP":   "United Kingdom", "SHEL": "United Kingdom",
    "AZN":  "United Kingdom", "GSK":  "United Kingdom",
    "RIO":  "United Kingdom", "BHP":  "Australia",
    "TM":   "Japan",  "HMC": "Japan",  "SONY": "Japan", "MUFG": "Japan",
    "TSM":  "Taiwan",
    "KB":   "South Korea",
}


def safe_str(v, default="") -> str:
    return str(v).strip() if v and str(v) != "None" else default


def safe_int(v) -> int:
    try:
        import math
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return 0
        return int(f)
    except Exception:
        return 0


def cap_category(mc: int) -> str:
    if mc >= 200_000_000_000: return "Mega"
    if mc >= 10_000_000_000:  return "Large"
    if mc >= 2_000_000_000:   return "Mid"
    if mc >= 300_000_000:     return "Small"
    return "Micro"


def fetch(symbol: str) -> dict | None:
    try:
        info = yf.Ticker(symbol).info
        if not info or not info.get("longName"):
            print(f"  ⚠️  No data for {symbol}")
            return None
        return info
    except Exception as e:
        print(f"  ⚠️  yfinance error {symbol}: {e}")
        return None


def ingest_stocks():
    print("=" * 60)
    print(f" STEP 1 — Stock Information  ({len(SYMBOLS)} symbols, source: yfinance)")
    print("=" * 60)

    db  = get_db()
    cur = db.cursor()
    ok = fail = 0

    for idx, symbol in enumerate(SYMBOLS, 1):
        print(f"[{idx:>3}/{len(SYMBOLS)}] {symbol:<6}", end=" ", flush=True)

        info = fetch(symbol)
        if not info:
            print("✗")
            fail += 1
            continue

        company_name = safe_str(info.get("longName") or info.get("shortName"))
        sector       = safe_str(info.get("sector"))
        industry     = safe_str(info.get("industry"))
        exchange     = safe_str(info.get("exchange"), "NASDAQ")
        market_cap   = safe_int(info.get("marketCap"))
        country      = ADR_MAP.get(symbol, safe_str(info.get("country"), "US"))
        is_adr       = symbol in ADR_MAP
        cat          = cap_category(market_cap)

        cur.execute("""
            INSERT INTO stocks
                (symbol, company_name, sector, industry, exchange, country,
                 market_cap_category, is_adr)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                company_name        = VALUES(company_name),
                sector              = VALUES(sector),
                industry            = VALUES(industry),
                exchange            = VALUES(exchange),
                country             = VALUES(country),
                market_cap_category = VALUES(market_cap_category),
                is_adr              = VALUES(is_adr)
        """, (symbol, company_name[:100], sector[:50], industry[:50],
              exchange[:20], country[:50], cat, is_adr))

        print(f"✓  {company_name[:35]:<35} | {sector[:20]:<20} | {cat}")
        ok += 1
        time.sleep(0.3)

    db.commit()
    cur.close()
    db.close()

    print(f"\n{'=' * 60}")
    print(f"✅ Stocks done  —  ✓ {ok}   ✗ {fail}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    ingest_stocks()
