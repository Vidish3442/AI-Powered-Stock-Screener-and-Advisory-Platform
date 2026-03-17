from db import get_db

def generate_analyst_recommendations(symbol, pe_ratio=None, current_price=None):
    """Generate realistic analyst recommendations based on stock fundamentals."""
    try:
        if pe_ratio is not None:
            pe_ratio = float(pe_ratio)
        if current_price is not None:
            current_price = float(current_price)
        
        if not current_price or current_price <= 0:
            price_seed = sum(ord(c) for c in symbol) % 100
            current_price = 20 + (price_seed * 2.5)
            
        if not pe_ratio or pe_ratio <= 0:
            pe_seed = sum(ord(c) * i for i, c in enumerate(symbol)) % 50
            pe_ratio = 8 + (pe_seed * 0.6)  
            
        recommendation_seed = (sum(ord(c) for c in symbol) * 7) % 100
        
        if pe_ratio < 15:
            target_multiplier = 1.10 + (recommendation_seed % 20) * 0.005
            recommendation = 'Buy'
        elif pe_ratio < 25:
            target_multiplier = 1.00 + (recommendation_seed % 10) * 0.005
            recommendation = 'Hold'
        else:
            target_multiplier = 0.90 + (recommendation_seed % 15) * 0.004  
            recommendation = 'Sell'
        
        target_price = float(current_price) * target_multiplier        
        firms = ['Goldman Sachs', 'Morgan Stanley', 'JP Morgan', 'Bank of America', 'Citigroup', 
                'Wells Fargo', 'Deutsche Bank', 'Credit Suisse', 'Barclays', 'UBS']
        firm_index = sum(ord(c) for c in symbol) % len(firms)
        analyst_firm = firms[firm_index]
        
        return {
            'target_price': round(target_price, 2),
            'current_price': round(current_price, 2),
            'recommendation': recommendation,
            'analyst_firm': analyst_firm
        }
        
    except Exception as e:
        print(f"  ⚠️ Error generating analyst data: {str(e)}")
        return None

def ingest_analyst_targets():
    """Ingest analyst target data for all stocks in database."""
    print("Starting analyst targets")
    db = None
    cur = None
    
    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        cur.execute("""
            SELECT s.stock_id, s.symbol, f.pe_ratio, f.current_price 
            FROM stocks s 
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id 
            ORDER BY s.stock_id
        """)
        stocks = cur.fetchall()
        
        if not stocks:
            print("No stocks found. Run ingest_stocks.py first.")
            return
        
        successful = 0
        failed = 0
        
        for i, stock in enumerate(stocks):
            print(f"\nProcessing analyst targets for {stock['symbol']} ({i+1}/{len(stocks)})...")
            
            analyst_data = generate_analyst_recommendations(
                stock['symbol'], 
                stock.get('pe_ratio'), 
                stock.get('current_price')
            )
            
            if not analyst_data:
                print(f"✗ No analyst data for {stock['symbol']}")
                failed += 1
                continue
            cur.execute("""
                INSERT INTO analyst_targets
                (stock_id, target_price, current_price, recommendation, analyst_firm, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    target_price=VALUES(target_price),
                    current_price=VALUES(current_price),
                    recommendation=VALUES(recommendation),
                    analyst_firm=VALUES(analyst_firm),
                    updated_at=NOW()
            """, (
                stock["stock_id"],
                analyst_data['target_price'],
                analyst_data['current_price'],
                analyst_data['recommendation'],
                analyst_data['analyst_firm']
            ))
            if analyst_data['current_price'] > 0:
                upside = ((analyst_data['target_price'] - analyst_data['current_price']) / analyst_data['current_price']) * 100
                upside_str = f"{upside:+.1f}%"
            else:
                upside_str = "N/A"
            
            print(f"✓ {stock['symbol']} - {analyst_data['recommendation']} "
                  f"(Target: ${analyst_data['target_price']:.2f}, "
                  f"Current: ${analyst_data['current_price']:.2f}, "
                  f"Upside: {upside_str})")
            
            successful += 1
        
        db.commit()
        print(f"✅ Analyst targets ingestion completed!")
        print(f"✓ Successful: {successful}")
        print(f"✗ Failed: {failed}")
        print(f"⚠️  DISCLAIMER: This data is for demonstration only - NOT financial advice!")
        
    except Exception as e:
        print(f"\n❌ Database error: {str(e)}")
        if db:
            db.rollback()
        return False
        
    finally:
        if cur:
            cur.close()
        if db:
            db.close()
    
    return True

if __name__ == "__main__":
    ingest_analyst_targets()