import sys
import time
from datetime import datetime
import yfinance as yf

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Environment variables loaded")
except ImportError:
    print("⚠️ python-dotenv not installed, relying on system environment")
except Exception as e:
    print(f"⚠️ Error loading environment: {str(e)}")

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    """Print a formatted step."""
    print(f"\n[STEP {step_num}] {title}")
    print("-" * 40)

def check_data_sources():
    """Check availability of both yfinance and Alpha Vantage."""
    sources = {'yfinance': False, 'alpha_vantage': False}    
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if info and 'symbol' in info:
            print("✓ yfinance is available and working")
            sources['yfinance'] = True
        else:
            print("⚠️ yfinance installed but not responding properly")
    except ImportError:
        print("⚠️ yfinance not installed")
    except Exception as e:
        print(f"⚠️ yfinance error: {str(e)}")
    
    try:
        import os
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if api_key and api_key.strip():
            print(f"✓ Alpha Vantage API key found: {api_key[:8]}...")
            sources['alpha_vantage'] = True
        else:
            print("⚠️ Alpha Vantage API key not found or empty in .env file")
            print("  Please check ALPHA_VANTAGE_API_KEY in your .env file")
    except Exception as e:
        print(f"⚠️ Error checking Alpha Vantage: {str(e)}")
    
    return sources

def main():
    """Run complete data ingestion pipeline using hybrid approach."""
    start_time = datetime.now()
    
    print_header("STOCK SCREENER DATA INGESTION PIPELINE (Hybrid)")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 Using yfinance (primary) + Alpha Vantage (fallback)")
    
    sources = check_data_sources()
    
    if not sources['yfinance'] and not sources['alpha_vantage']:
        print("\n❌ No data sources available!")
        print("Please install yfinance: pip install yfinance")
        print("And/or add ALPHA_VANTAGE_API_KEY to your .env file")
        sys.exit(1)
    
    if sources['yfinance'] and sources['alpha_vantage']:
        print("\n✅ Hybrid mode: yfinance (primary) + Alpha Vantage (fallback)")
    elif sources['yfinance']:
        print("\n📊 yfinance-only mode (Alpha Vantage not available)")
    else:
        print("\n📡 Alpha Vantage-only mode (yfinance not available)")
    try:
        from db import get_db
        db = get_db()
        db.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("Please check your database configuration in .env file")
        sys.exit(1)
    
    try:
        print_step(1, "Ingesting Stock Information")
        from ingest_stocks import ingest_stocks
        ingest_stocks()
        
        print("\nWaiting 3 seconds before next step...")
        time.sleep(3)
        
        print_step(2, "Ingesting Fundamental Data")
        from ingest_fundamentals import ingest_fundamentals
        ingest_fundamentals()
        
        
        print("\nWaiting 3 seconds before next step...")
        time.sleep(3)
        
        print_step(3, "Ingesting Quarterly Financial Data")
        from ingest_quarterly_financials import ingest_quarterly
        ingest_quarterly()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print_header("INGESTION PIPELINE COMPLETED")
        print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print("\n✅ All data ingestion completed successfully!")
        print("\nYour stock screener database is now populated with:")
        print("  • Stock information (50 major companies) - yfinance + Alpha Vantage")
        print("  • Comprehensive fundamental metrics - yfinance + Alpha Vantage fallback")
        print("  • Historical quarterly financial data - Alpha Vantage (more reliable)")
        print("  • Multi-region coverage (US, India, China, Europe)")
        print("  • Optimized hybrid approach for maximum data quality")
        
        print("\n🚀 You can now use your AI stock screener!")
        print("💡 Try queries like:")
        print("  • 'Tech stocks with PE < 25'")
        print("  • 'Financial stocks with positive profit last 4 quarters'")
        print("  • 'Large cap stocks with dividend yield > 2%'")
        print("  • 'Healthcare stocks with profit margins > 15%'")
        print("  • 'International ADRs with beta < 1.5'")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ingestion interrupted by user (Ctrl+C)")
        print("You can resume by running individual scripts:")
        print("  python ingest_stocks.py")
        print("  python ingest_fundamentals.py")
        print("  python ingest_quarterly_financials.py")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Error during ingestion: {str(e)}")
        print("Check the error above and try running individual scripts:")
        print("  python ingest_stocks.py")
        print("  python ingest_fundamentals.py")
        print("  python ingest_quarterly_financials.py")
        sys.exit(1)

if __name__ == "__main__":
    main()