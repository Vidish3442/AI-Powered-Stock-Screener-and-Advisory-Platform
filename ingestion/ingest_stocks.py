import requests
import time
import os
from db import get_db
MAX_REQUESTS=25
from dotenv import load_dotenv
load_dotenv()
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance not available, using Alpha Vantage only")
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "NFLX", "ADBE",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "BLK",
    "JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN",
    "WMT", "HD", "PG", "KO", "PEP", "COST", "TGT", "LOW", "SBUX", "MCD",
    "INFY", "BABA", "ASML", "NVO", "TM", "HDB", "TSM", "UL", "SNY", "DEO"
]

ALPHA_REQUESTS_MADE = 0
MAX_ALPHA_REQUESTS = 15 
def get_yfinance_data(symbol):
    """Get company data from yfinance."""
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if info and info.get('symbol') == symbol:
            return info
        return None
    except Exception as e:
        print(f"  ⚠️ yfinance error for {symbol}: {str(e)}")
        return None

def get_alpha_vantage_data(symbol):
    """Get company overview from Alpha Vantage as fallback."""
    global ALPHA_REQUESTS_MADE
    
    if ALPHA_REQUESTS_MADE >= MAX_ALPHA_REQUESTS:
        print(f"  ⚠️ Alpha Vantage limit reached ({MAX_ALPHA_REQUESTS})")
        return None
    
    if not ALPHA_VANTAGE_API_KEY:
        return None
    
    try:
        url = f"{ALPHA_VANTAGE_BASE_URL}?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=10)
        ALPHA_REQUESTS_MADE += 1
        
        if response.status_code == 200:
            data = response.json()
            if data.get('Symbol') == symbol and 'Error Message' not in data:
                return data
        return None
    except Exception as e:
        print(f"  ⚠️ Alpha Vantage error for {symbol}: {str(e)}")
        return None

def merge_stock_data(yf_data, av_data, symbol):
    """Merge data from both sources, prioritizing yfinance."""
    merged = {}
    
    if yf_data:
        merged['company_name'] = yf_data.get('longName') or yf_data.get('shortName', '')
        merged['sector'] = yf_data.get('sector', '')
        merged['industry'] = yf_data.get('industry', '')
        merged['exchange'] = yf_data.get('exchange', 'NASDAQ')
        merged['country'] = yf_data.get('country', 'US')
        merged['market_cap'] = yf_data.get('marketCap', 0)    
    if av_data:
        if not merged.get('company_name'):
            merged['company_name'] = av_data.get('Name', '')
        if not merged.get('sector'):
            merged['sector'] = av_data.get('Sector', '')
        if not merged.get('industry'):
            merged['industry'] = av_data.get('Industry', '')
        if not merged.get('exchange'):
            merged['exchange'] = av_data.get('Exchange', 'NASDAQ')
        if not merged.get('country'):
            merged['country'] = av_data.get('Country', 'US')
        if not merged.get('market_cap'):
            merged['market_cap'] = safe_int(av_data.get('MarketCapitalization'))
    
    if (merged.get('company_name') and 
        merged.get('sector') and 
        merged.get('industry') and 
        merged.get('market_cap', 0) > 0):
        return merged
    
    return None

def get_company_overview(symbol):
    """Get company overview from Alpha Vantage."""
    global REQUESTS_MADE
    
    if REQUESTS_MADE >= MAX_REQUESTS:
        return None
    
    try:
        url = f"{ALPHA_VANTAGE_BASE_URL}?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=10)
        REQUESTS_MADE += 1
        
        if response.status_code == 200:
            data = response.json()
            if data.get('Symbol') == symbol:
                return data
        return None
    except:
        return None

def safe_float(value):
    try:
        return float(value) if value and value != 'None' else 0.0
    except:
        return 0.0

def safe_int(value):
    try:
        return int(float(value)) if value and value != 'None' else 0
    except:
        return 0

def ingest_stocks():
    """Ingest stock information using both yfinance and Alpha Vantage."""
    print(f"Starting stock ingestion for {len(SYMBOLS)} companies...")
    print(f"Primary: {'yfinance' if YFINANCE_AVAILABLE else 'Alpha Vantage only'}")
    print(f"Fallback: Alpha Vantage (limit: {MAX_ALPHA_REQUESTS} requests)")
    
    db = get_db()
    cur = db.cursor()
    
    successful = 0
    failed = 0
    yf_success = 0
    av_fallback = 0
    
    for i, symbol in enumerate(SYMBOLS):
        print(f"\nProcessing {symbol} ({i+1}/{len(SYMBOLS)})...")
        
        yf_data = get_yfinance_data(symbol)
        av_data = None
        
        if not yf_data or not yf_data.get('longName') or not yf_data.get('marketCap'):
            print(f"  📡 Trying Alpha Vantage fallback...")
            av_data = get_alpha_vantage_data(symbol)
            if av_data:
                av_fallback += 1
        merged_data = merge_stock_data(yf_data, av_data, symbol)
        if not merged_data:
            print(f"✗ No valid data for {symbol}")
            failed += 1
            continue        
        market_cap = merged_data['market_cap']
        if market_cap >= 200_000_000_000:
            cap_category = 'Mega'
        elif market_cap >= 10_000_000_000:
            cap_category = 'Large'
        elif market_cap >= 2_000_000_000:
            cap_category = 'Mid'
        elif market_cap >= 300_000_000:
            cap_category = 'Small'
        else:
            cap_category = 'Micro'
        is_adr = False
        country = merged_data['country']
        
        if symbol in ["INFY", "HDB"]:
            country = "India"
            is_adr = True
        elif symbol in ["BABA", "TSM"]:
            country = "China" if symbol == "BABA" else "Taiwan"
            is_adr = True
        elif symbol in ["ASML", "NVO", "TM", "UL", "SNY", "DEO"]:
            is_adr = True
        cur.execute("""
            INSERT IGNORE INTO stocks (symbol, company_name, sector, industry, exchange, country, market_cap_category, is_adr)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            symbol,
            merged_data['company_name'][:100],
            merged_data['sector'][:50],
            merged_data['industry'][:50],
            merged_data['exchange'][:50],
            country[:50],
            cap_category,
            is_adr
        ))
        
        data_source = "yfinance" if yf_data and yf_data.get('longName') else "Alpha Vantage"
        print(f"✓ {symbol} - {merged_data['company_name']} ({cap_category}) [{data_source}]")
        
        if yf_data and yf_data.get('longName'):
            yf_success += 1
        
        successful += 1
        if av_data:
            time.sleep(12)
        else:
            time.sleep(0.5) 
            
    db.commit()
    cur.close()
    db.close()
    
    print(f"\n{'='*50}")
    print(f"✅ Stock ingestion completed!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📊 yfinance primary: {yf_success}")
    print(f"📡 Alpha Vantage fallback: {av_fallback}")
    print(f"🌐 Alpha Vantage requests used: {ALPHA_REQUESTS_MADE}/{MAX_ALPHA_REQUESTS}")
    print(f"{'='*50}")

if __name__ == "__main__":
    ingest_stocks()