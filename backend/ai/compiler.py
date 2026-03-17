from backend.database import get_db
import mysql.connector

def compile_and_run(dsl):
    """Compile and execute DSL with simplified query."""
    db = None
    cursor = None
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        base_sql = """
        SELECT DISTINCT
            s.stock_id,
            s.symbol,
            s.company_name,
            f.pe_ratio,
            f.market_cap,
            f.current_price,
            MAX(at.recommendation) as recommendation,
            CASE 
                WHEN MAX(at.target_price) IS NOT NULL AND f.current_price IS NOT NULL AND f.current_price > 0 THEN
                    CASE 
                        WHEN ((MAX(at.target_price) - f.current_price) / f.current_price * 100) > 20 THEN 'Strong Upside'
                        WHEN ((MAX(at.target_price) - f.current_price) / f.current_price * 100) BETWEEN 0 AND 20 THEN 'Moderate Upside'
                        WHEN ((MAX(at.target_price) - f.current_price) / f.current_price * 100) < 0 THEN 'Target Below Price'
                        ELSE 'No Target'
                    END
                ELSE 'No Target'
            END as upside_category
        FROM fundamentals f
        INNER JOIN stocks s ON f.stock_id = s.stock_id
        LEFT JOIN analyst_targets at ON s.stock_id = at.stock_id
        """
        
        where_clause, params = build_where_clause(dsl)
        if where_clause:
            base_sql += f" WHERE {where_clause}"
        
        base_sql += """ GROUP BY s.stock_id, s.symbol, s.company_name, f.pe_ratio, f.market_cap, f.current_price
                        ORDER BY s.symbol LIMIT 500"""
        
        cursor.execute(base_sql, params)
        results = cursor.fetchall()
        needs_quarterly = has_quarterly_conditions(dsl)
        quarterly_data = {}
        
        if needs_quarterly and results:
            quarterly_data = get_optimized_quarterly_data(cursor, results, dsl)
        
        return {
            'stocks': results,
            'quarterly_data': quarterly_data,
            'has_quarterly': needs_quarterly
        }
        
    except mysql.connector.Error as e:
        print(f"❌ Database error in compiler: {e}")
        raise Exception("Database connection issue. Please try again.")
    except Exception as e:
        print(f"❌ Compiler error: {e}")
        raise Exception(f"Query processing error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def get_optimized_quarterly_data(cursor, results, dsl):
    """Get quarterly data using optimized query with indexes."""
    if not results:
        return {}
    
    stock_ids = [result['stock_id'] for result in results]
    max_quarters = get_max_quarters_requested(dsl)
    
    quarterly_sql = """
    SELECT 
        q.stock_id,
        s.symbol,
        q.quarter,
        q.year,
        q.revenue,
        q.ebitda,
        q.net_profit
    FROM quarterly_finance q
    INNER JOIN stocks s ON q.stock_id = s.stock_id
    WHERE q.stock_id IN ({})
    ORDER BY q.stock_id, q.year DESC, q.quarter DESC
    """.format(','.join(['%s'] * len(stock_ids)))
    
    cursor.execute(quarterly_sql, stock_ids)
    all_quarterly_results = cursor.fetchall()
    
    
    quarterly_data = {}
    stock_quarter_counts = {}
    
    for row in all_quarterly_results:
        stock_id = row['stock_id']
        
        if stock_id not in stock_quarter_counts:
            stock_quarter_counts[stock_id] = 0
            quarterly_data[stock_id] = []
            
        if stock_quarter_counts[stock_id] < max_quarters:
            quarterly_data[stock_id].append({
                'symbol': row['symbol'],
                'quarter': row['quarter'],
                'year': row['year'],
                'revenue': row['revenue'],
                'ebitda': row['ebitda'],
                'net_profit': row['net_profit']
            })
            stock_quarter_counts[stock_id] += 1
    
    return quarterly_data
def build_where_clause(dsl):
    """Recursively build WHERE clause from DSL."""
    if dsl.get("type") == "group":
        return build_group_clause(dsl)
    elif "conditions" in dsl:
        return build_legacy_clause(dsl)    
    else:
        return "", []

def build_group_clause(group):
    """Build WHERE clause for nested group."""
    conditions = []
    params = []
    logic = group.get("logic", "AND")
    
    for item in group["conditions"]:
        item_type = item.get("type")
        
        if item_type == "condition":
            clause, item_params = build_condition_clause(item)
            if clause:
                conditions.append(clause)
                params.extend(item_params)
        
        elif item_type == "quarterly":
            clause, item_params = build_quarterly_clause(item)
            if clause:
                conditions.append(clause)
                params.extend(item_params)
        
        elif item_type == "group":
            clause, item_params = build_group_clause(item)
            if clause:
                conditions.append(f"({clause})")
                params.extend(item_params)
    
    if conditions:
        return f" {logic} ".join(conditions), params
    else:
        return "", []

def build_legacy_clause(dsl):
    """Build WHERE clause for legacy format."""
    conditions = []
    params = []
    logic = dsl.get("logic", "AND")
    
    for cond in dsl["conditions"]:
        if "operator" in cond:
            clause, item_params = build_condition_clause(cond)
        elif cond.get("type") == "quarterly":
            clause, item_params = build_quarterly_clause(cond)
        else:
            continue
            
        if clause:
            conditions.append(clause)
            params.extend(item_params)
    
    if conditions:
        return f" {logic} ".join(conditions), params
    else:
        return "", []

def build_condition_clause(cond):
    """Build optimized clause for a simple condition using indexes effectively."""
    field = cond["field"]
    operator = cond["operator"]
    value = cond["value"]
    if field == "pe_ratio":
        if operator == ">" and value < 100:
            return f"f.pe_ratio BETWEEN %s AND 1000", [value]
        elif operator == "<" and value > 0:
            return f"f.pe_ratio BETWEEN 0 AND %s", [value]
        else:
            return f"f.pe_ratio {operator} %s", [value]
    
    elif field == "price_to_book":
        if operator == ">" and value < 50:
            return f"f.price_to_book BETWEEN %s AND 100", [value]
        elif operator == "<" and value > 0:
            return f"f.price_to_book BETWEEN 0 AND %s", [value]
        else:
            return f"f.price_to_book {operator} %s", [value]
    
    elif field == "dividend_yield":
        return f"f.dividend_yield {operator} %s", [value]
    elif field == "beta":
        return f"f.beta {operator} %s", [value]
    elif field == "profit_margin":
        return f"f.profit_margin {operator} %s", [value]
    elif field == "roe":
        return f"f.roe {operator} %s", [value]
    elif field == "current_price":
        return f"f.current_price {operator} %s", [value]
    elif field == "market_cap":
        return f"f.market_cap {operator} %s", [value]
    elif field == "eps":
        return f"f.eps {operator} %s", [value]
    
    elif field == "market_cap_category":
        return f"s.market_cap_category {operator} %s", [value]
    elif field == "country":
        return f"s.country {operator} %s", [value]
    elif field == "is_adr":
        return f"s.is_adr {operator} %s", [value]
    elif field == "sector":
        return f"s.sector {operator} %s", [value]
    elif field == "industry":
        return f"s.industry {operator} %s", [value]
    
    elif field == "target_price":
        return f"at.target_price {operator} %s", [value]
    elif field == "recommendation":
        return f"at.recommendation {operator} %s", [value]
    elif field == "upside":
        if operator == ">":
            return f"((at.target_price - f.current_price) / f.current_price * 100) {operator} %s", [value]
        else:
            return f"((at.target_price - f.current_price) / f.current_price * 100) {operator} %s", [value]
    
    return "", []

def build_quarterly_clause(cond):
    """Build optimized clause for quarterly condition using net_profit index."""
    field = cond["field"]
    condition = cond["condition"]
    last_n = cond["last_n"]
    
    if field == "net_profit":
        if condition == "positive":
            clause = """
            s.stock_id IN (
                SELECT stock_id
                FROM quarterly_finance
                WHERE net_profit > 0
                GROUP BY stock_id
                HAVING COUNT(*) >= %s
            )
            """
        else:  
            clause = """
            s.stock_id IN (
                SELECT stock_id
                FROM quarterly_finance
                WHERE net_profit < 0
                GROUP BY stock_id
                HAVING COUNT(*) >= %s
            )
            """
        return clause, [last_n]
    
    elif field == "revenue":
        if condition == "positive":
            clause = """
            s.stock_id IN (
                SELECT stock_id
                FROM quarterly_finance
                WHERE revenue > 0
                GROUP BY stock_id
                HAVING COUNT(*) >= %s
            )
            """
            return clause, [last_n]
    
    return "", []

def has_quarterly_conditions(dsl):
    """Check if DSL contains quarterly conditions."""
    if dsl.get("type") == "group":
        return check_group_for_quarterly(dsl)
    elif "conditions" in dsl:
        for cond in dsl["conditions"]:
            if cond.get("type") == "quarterly":
                return True
        return False
    
    return False

def check_group_for_quarterly(group):
    """Recursively check group for quarterly conditions."""
    for item in group["conditions"]:
        item_type = item.get("type")
        
        if item_type == "quarterly":
            return True
        elif item_type == "group":
            if check_group_for_quarterly(item):
                return True
    
    return False

def get_max_quarters_requested(dsl):
    """Get the maximum number of quarters requested in any quarterly condition."""
    if dsl.get("type") == "group":
        return get_max_quarters_from_group(dsl)
    elif "conditions" in dsl:
        max_quarters = 0
        for cond in dsl["conditions"]:
            if cond.get("type") == "quarterly":
                max_quarters = max(max_quarters, cond.get("last_n", 0))
        return max_quarters if max_quarters > 0 else 8  
    return 8 

def get_max_quarters_from_group(group):
    """Recursively get max quarters from nested group."""
    max_quarters = 0
    
    for item in group["conditions"]:
        item_type = item.get("type")
        
        if item_type == "quarterly":
            max_quarters = max(max_quarters, item.get("last_n", 0))
        elif item_type == "group":
            group_max = get_max_quarters_from_group(item)
            max_quarters = max(max_quarters, group_max)
    
    return max_quarters if max_quarters > 0 else 8  
