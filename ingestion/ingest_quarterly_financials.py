import requests
import time
import os
from db import get_db
from dotenv import load_dotenv
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

ALPHA_REQUESTS_MADE = 0
MAX_ALPHA_REQUESTS = 20 
def safe_int(value):
    try:
        return int(float(value)) if value and value != 'None' else 0
    except:
        return 0

def get_alpha_vantage_quarterly(symbol):
    """Get quarterly income statement from Alpha Vantage."""
    global ALPHA_REQUESTS_MADE
    
    if ALPHA_REQUESTS_MADE >= MAX_ALPHA_REQUESTS:
        print(f"  ⚠️ Alpha Vantage limit reached ({MAX_ALPHA_REQUESTS})")
        return None
    
    if not ALPHA_VANTAGE_API_KEY:
        print("  ⚠️ Alpha Vantage API key not found")
        return None
    
    try:
        url = f"{ALPHA_VANTAGE_BASE_URL}?function=INCOME_STATEMENT&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=15)
        ALPHA_REQUESTS_MADE += 1
        
        if response.status_code == 200:
            data = response.json()
            if "Error Message" in data:
                print(f"  ⚠️ Alpha Vantage error: {data['Error Message']}")
                return None
            elif "Note" in data:
                print(f"  ⚠️ Rate limit hit: {data['Note']}")
                return None
            
            quarterly_reports = data.get("quarterlyReports", [])
            
            if not quarterly_reports:
                print(f"  ⚠️ No quarterly reports found")
                return None
            
            quarters_data = []
            for report in quarterly_reports[:20]:
                try:
                    fiscal_date = report.get('fiscalDateEnding', '')
                    if not fiscal_date:
                        continue
                    
                    year = int(fiscal_date[:4])
                    month = int(fiscal_date[5:7])
                    quarter = f"Q{((month - 1) // 3) + 1}"
                    revenue = safe_int(report.get('totalRevenue'))
                    ebitda = safe_int(report.get('ebitda'))
                    net_profit = safe_int(report.get('netIncome'))
                    if revenue > 0 or net_profit != 0:
                        quarters_data.append({
                            'year': year,
                            'quarter': quarter,
                            'revenue': revenue,
                            'ebitda': ebitda,
                            'net_profit': net_profit
                        })
                
                except Exception as e:
                    print(f"  ⚠️ Error processing quarter: {str(e)}")
                    continue
            
            return quarters_data if quarters_data else None
            
    except Exception as e:
        print(f"  ⚠️ Alpha Vantage request error: {str(e)}")
        return None

def ingest_quarterly():
    """Ingest quarterly financial data using Alpha Vantage exclusively."""
    print("Starting quarterly financials ingestion using Alpha Vantage...")
    print("📡 Alpha Vantage provides more reliable quarterly data than yfinance")
    print(f"API request limit: {MAX_ALPHA_REQUESTS} requests")
    
    if not ALPHA_VANTAGE_API_KEY:
        print("❌ Alpha Vantage API key not found in .env file")
        print("Please add ALPHA_VANTAGE_API_KEY to continue")
        return
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT stock_id, symbol FROM stocks ORDER BY stock_id")
    stocks = cur.fetchall()
    
    if not stocks:
        print("No stocks found. Run ingest_stocks.py first.")
        return
    
    successful = 0
    failed = 0
    total_quarters = 0
    
    for i, stock in enumerate(stocks):
        print(f"\nProcessing {stock['symbol']} ({i+1}/{len(stocks)})...")        
        if ALPHA_REQUESTS_MADE >= MAX_ALPHA_REQUESTS:
            print(f"⚠️ Reached Alpha Vantage request limit. Stopping at {stock['symbol']}")
            break
        quarterly_data = get_alpha_vantage_quarterly(stock['symbol'])
        
        if not quarterly_data:
            print(f"✗ No quarterly data for {stock['symbol']}")
            failed += 1
            continue
        quarters_inserted = 0
        for quarter_info in quarterly_data:
            try:
                revenue = quarter_info['revenue']
                ebitda = quarter_info['ebitda']
                net_profit = quarter_info['net_profit']
                
                cur.execute("""
                    INSERT IGNORE INTO quarterly_finance
                    (stock_id, quarter, year, revenue, ebitda, net_profit)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    stock["stock_id"],
                    quarter_info['quarter'],
                    quarter_info['year'],
                    revenue,
                    ebitda,
                    net_profit
                ))
                
                quarters_inserted += 1
                total_quarters += 1
                
            except Exception as e:
                print(f"  ⚠️ Error inserting quarter: {str(e)}")
                continue
        
        if quarters_inserted > 0:
            print(f"✓ {stock['symbol']} - {quarters_inserted} quarters inserted")
            successful += 1
        else:
            print(f"✗ No valid quarters for {stock['symbol']}")
            failed += 1        
        print(f"  📊 API requests used: {ALPHA_REQUESTS_MADE}/{MAX_ALPHA_REQUESTS}")
        time.sleep(12) 
    db.commit()
    cur.close()
    db.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Quarterly financials ingestion completed!")
    print(f"✓ Successful stocks: {successful}")
    print(f"✗ Failed stocks: {failed}")
    print(f"📊 Total quarters processed: {total_quarters}")
    print(f"📈 Average quarters per stock: {total_quarters/successful:.1f}" if successful > 0 else "")
    print(f"🌐 Alpha Vantage requests used: {ALPHA_REQUESTS_MADE}/{MAX_ALPHA_REQUESTS}")
    print(f"{'='*60}")

if __name__ == "__main__":
    ingest_quarterly()