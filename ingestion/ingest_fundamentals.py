import requests
import time
import os
from db import get_db

from dotenv import load_dotenv
load_dotenv()
MAX_REQUESTS=25

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance not available, using Alpha Vantage only")

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

ALPHA_REQUESTS_MADE = 0
MAX_ALPHA_REQUESTS = 15

def get_yfinance_fundamentals(symbol):
    """Get fundamental data from yfinance."""
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

def get_alpha_vantage_fundamentals(symbol):
    """Get fundamental data from Alpha Vantage as fallback."""
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

def merge_fundamental_data(yf_data, av_data):
    """Merge fundamental data from both sources, prioritizing yfinance."""
    merged = {}
    
    if yf_data:
        merged['pe_ratio'] = safe_float(yf_data.get('trailingPE') or yf_data.get('forwardPE'))
        merged['eps'] = safe_float(yf_data.get('trailingEps') or yf_data.get('forwardEps'))
        merged['market_cap'] = safe_int(yf_data.get('marketCap'))
        merged['roe'] = safe_float(yf_data.get('returnOnEquity'))
        merged['debt_equity'] = safe_float(yf_data.get('debtToEquity'))
        merged['price_to_book'] = safe_float(yf_data.get('priceToBook'))
        merged['dividend_yield'] = safe_float(yf_data.get('dividendYield'))
        merged['profit_margin'] = safe_float(yf_data.get('profitMargins'))
        merged['beta'] = safe_float(yf_data.get('beta'))
        merged['current_price'] = safe_float(yf_data.get('currentPrice') or yf_data.get('regularMarketPrice'))
    
    if av_data:
        if not merged.get('pe_ratio'):
            merged['pe_ratio'] = safe_float(av_data.get('PERatio'))
        if not merged.get('eps'):
            merged['eps'] = safe_float(av_data.get('EPS'))
        if not merged.get('market_cap'):
            merged['market_cap'] = safe_int(av_data.get('MarketCapitalization'))
        if not merged.get('roe'):
            merged['roe'] = safe_float(av_data.get('ReturnOnEquityTTM'))
        if not merged.get('debt_equity'):
            merged['debt_equity'] = safe_float(av_data.get('DebtToEquityRatio'))
        if not merged.get('price_to_book'):
            merged['price_to_book'] = safe_float(av_data.get('PriceToBookRatio'))
        if not merged.get('dividend_yield'):
            merged['dividend_yield'] = safe_float(av_data.get('DividendYield'))
        if not merged.get('profit_margin'):
            merged['profit_margin'] = safe_float(av_data.get('ProfitMargin'))
        if not merged.get('beta'):
            merged['beta'] = safe_float(av_data.get('Beta'))
        if not merged.get('current_price') and av_data.get('52WeekHigh') and av_data.get('52WeekLow'):
            week_high = safe_float(av_data.get('52WeekHigh'))
            week_low = safe_float(av_data.get('52WeekLow'))
            merged['current_price'] = (week_high + week_low) / 2 if week_high > 0 and week_low > 0 else 0
    
    if (merged.get('pe_ratio', 0) > 0 and 
        merged.get('market_cap', 0) > 0 and 
        merged.get('current_price', 0) > 0):
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

def ingest_fundamentals():
    """Ingest fundamental data using both yfinance and Alpha Vantage."""
    print("Starting fundamentals ingestion...")
    print(f"Primary: {'yfinance' if YFINANCE_AVAILABLE else 'Alpha Vantage only'}")
    print(f"Fallback: Alpha Vantage (limit: {MAX_ALPHA_REQUESTS} requests)")
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT stock_id, symbol FROM stocks ORDER BY stock_id")
    stocks = cur.fetchall()
    
    if not stocks:
        print("No stocks found. Run ingest_stocks.py first.")
        return
    
    successful = 0
    failed = 0
    yf_success = 0
    av_fallback = 0
    
    for i, stock in enumerate(stocks):
        print(f"\nProcessing {stock['symbol']} ({i+1}/{len(stocks)})...")        
        yf_data = get_yfinance_fundamentals(stock['symbol'])
        av_data = None        
        if (not yf_data or 
            not yf_data.get('trailingPE') or 
            not yf_data.get('marketCap') or 
            not yf_data.get('currentPrice')):
            print(f"  📡 Trying Alpha Vantage fallback...")
            av_data = get_alpha_vantage_fundamentals(stock['symbol'])
            if av_data:
                av_fallback += 1
        merged_data = merge_fundamental_data(yf_data, av_data)
        
        if not merged_data:
            print(f"✗ No valid fundamental data for {stock['symbol']}")
            failed += 1
            continue
        
        cur.execute("""
            INSERT INTO fundamentals
            (stock_id, pe_ratio, eps, market_cap, roe, debt_equity, price_to_book, dividend_yield, profit_margin, beta, current_price, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            ON DUPLICATE KEY UPDATE
                pe_ratio=VALUES(pe_ratio),
                eps=VALUES(eps),
                market_cap=VALUES(market_cap),
                roe=VALUES(roe),
                debt_equity=VALUES(debt_equity),
                price_to_book=VALUES(price_to_book),
                dividend_yield=VALUES(dividend_yield),
                profit_margin=VALUES(profit_margin),
                beta=VALUES(beta),
                current_price=VALUES(current_price),
                updated_at=NOW()
        """, (
            stock["stock_id"],
            merged_data['pe_ratio'],
            merged_data['eps'],
            merged_data['market_cap'],
            merged_data['roe'],
            merged_data['debt_equity'],
            merged_data['price_to_book'],
            merged_data['dividend_yield'],
            merged_data['profit_margin'],
            merged_data['beta'],
            merged_data['current_price']
        ))
        
        data_source = "yfinance" if yf_data and yf_data.get('trailingPE') else "Alpha Vantage"
        print(f"✓ {stock['symbol']} (PE: {merged_data['pe_ratio']:.2f}, P/B: {merged_data['price_to_book']:.2f}) [{data_source}]")
        
        if yf_data and yf_data.get('trailingPE'):
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
    print(f"✅ Fundamentals ingestion completed!")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📊 yfinance primary: {yf_success}")
    print(f"📡 Alpha Vantage fallback: {av_fallback}")
    print(f"🌐 Alpha Vantage requests used: {ALPHA_REQUESTS_MADE}/{MAX_ALPHA_REQUESTS}")
    print(f"{'='*50}")

if __name__ == "__main__":
    ingest_fundamentals()