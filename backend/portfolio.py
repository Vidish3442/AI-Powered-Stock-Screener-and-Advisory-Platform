from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from backend.auth import get_current_user
from backend.database import get_db
import mysql.connector
from datetime import datetime

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

class PortfolioCreate(BaseModel):
    name: str

class PortfolioResponse(BaseModel):
    portfolio_id: int
    user_id: int
    name: str
    created_at: datetime
    total_holdings: int
    total_value: float

class HoldingCreate(BaseModel):
    stock_id: int
    quantity: int
    avg_price: float

class HoldingResponse(BaseModel):
    holding_id: int
    portfolio_id: int
    stock_id: int
    symbol: str
    company_name: str
    quantity: int
    avg_price: float
    current_price: Optional[float]
    total_value: float
    gain_loss: Optional[float]
    gain_loss_percent: Optional[float]
    created_at: datetime
    updated_at: datetime

@router.get("/", response_model=List[PortfolioResponse])
async def get_user_portfolios(current_user: dict = Depends(get_current_user)):
    """Get all portfolios for the current user."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                p.portfolio_id,
                p.user_id,
                p.name,
                p.created_at,
                COUNT(ph.holding_id) as total_holdings,
                COALESCE(SUM(ph.quantity * ph.avg_price), 0) as total_value
            FROM portfolio p
            LEFT JOIN portfolio_holdings ph ON p.portfolio_id = ph.portfolio_id
            WHERE p.user_id = %s
            GROUP BY p.portfolio_id, p.user_id, p.name, p.created_at
            ORDER BY p.created_at DESC
        """, (current_user["user_id"],))
        
        portfolios = cursor.fetchall()
        return portfolios
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.post("/", response_model=dict)
async def create_portfolio(portfolio: PortfolioCreate, current_user: dict = Depends(get_current_user)):
    """Create a new portfolio for the current user."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO portfolio (user_id, name)
            VALUES (%s, %s)
        """, (current_user["user_id"], portfolio.name))
        
        portfolio_id = cursor.lastrowid
        db.commit()
        
        return {"portfolio_id": portfolio_id, "message": "Portfolio created successfully"}
        
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Portfolio name already exists for this user")
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
async def get_portfolio_holdings(portfolio_id: int, current_user: dict = Depends(get_current_user)):
    """Get all holdings for a specific portfolio."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT portfolio_id FROM portfolio 
            WHERE portfolio_id = %s AND user_id = %s
        """, (portfolio_id, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        cursor.execute("""
            SELECT 
                ph.holding_id,
                ph.portfolio_id,
                ph.stock_id,
                s.symbol,
                s.company_name,
                ph.quantity,
                ph.avg_price,
                f.current_price,
                ph.quantity * ph.avg_price as total_value,
                CASE 
                    WHEN f.current_price IS NOT NULL THEN
                        (f.current_price - ph.avg_price) * ph.quantity
                    ELSE NULL
                END as gain_loss,
                CASE 
                    WHEN f.current_price IS NOT NULL AND ph.avg_price > 0 THEN
                        ((f.current_price - ph.avg_price) / ph.avg_price) * 100
                    ELSE NULL
                END as gain_loss_percent,
                ph.created_at,
                ph.updated_at
            FROM portfolio_holdings ph
            JOIN stocks s ON ph.stock_id = s.stock_id
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
            WHERE ph.portfolio_id = %s
            ORDER BY s.symbol
        """, (portfolio_id,))
        
        holdings = cursor.fetchall()
        return holdings
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.post("/{portfolio_id}/holdings", response_model=dict)
async def add_holding(portfolio_id: int, holding: HoldingCreate, current_user: dict = Depends(get_current_user)):
    """Add a new holding to a portfolio."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT portfolio_id FROM portfolio 
            WHERE portfolio_id = %s AND user_id = %s
        """, (portfolio_id, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        cursor.execute("""
            INSERT INTO portfolio_holdings (portfolio_id, stock_id, quantity, avg_price)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                quantity = quantity + VALUES(quantity),
                avg_price = ((quantity * avg_price) + (VALUES(quantity) * VALUES(avg_price))) / (quantity + VALUES(quantity))
        """, (portfolio_id, holding.stock_id, holding.quantity, holding.avg_price))
        
        holding_id = cursor.lastrowid
        db.commit()
        
        return {"holding_id": holding_id, "message": "Holding added successfully"}
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a portfolio and all its holdings."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT portfolio_id FROM portfolio 
            WHERE portfolio_id = %s AND user_id = %s
        """, (portfolio_id, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        cursor.execute("DELETE FROM portfolio WHERE portfolio_id = %s", (portfolio_id,))
        db.commit()
        
        return {"message": "Portfolio deleted successfully"}
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.put("/{portfolio_id}/holdings/{holding_id}")
async def update_holding(portfolio_id: int, holding_id: int, holding: HoldingCreate, current_user: dict = Depends(get_current_user)):
    """Update a specific holding in a portfolio."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT ph.holding_id 
            FROM portfolio_holdings ph
            JOIN portfolio p ON ph.portfolio_id = p.portfolio_id
            WHERE ph.holding_id = %s AND ph.portfolio_id = %s AND p.user_id = %s
        """, (holding_id, portfolio_id, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Holding not found")
        
        # Update the holding
        cursor.execute("""
            UPDATE portfolio_holdings 
            SET quantity = %s, avg_price = %s, updated_at = NOW()
            WHERE holding_id = %s
        """, (holding.quantity, holding.avg_price, holding_id))
        
        db.commit()
        
        return {"message": "Holding updated successfully"}
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.delete("/{portfolio_id}/holdings/{holding_id}")
async def delete_holding(portfolio_id: int, holding_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a specific holding from a portfolio."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT ph.holding_id 
            FROM portfolio_holdings ph
            JOIN portfolio p ON ph.portfolio_id = p.portfolio_id
            WHERE ph.holding_id = %s AND ph.portfolio_id = %s AND p.user_id = %s
        """, (holding_id, portfolio_id, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Holding not found")
        
        cursor.execute("DELETE FROM portfolio_holdings WHERE holding_id = %s", (holding_id,))
        db.commit()
        
        return {"message": "Holding deleted successfully"}
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()
@router.put("/{portfolio_id}/holdings/{holding_id}")
async def update_holding(portfolio_id: int, holding_id: int, holding: HoldingCreate, current_user: dict = Depends(get_current_user)):
    """Update a specific holding in a portfolio."""
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT ph.holding_id
            FROM portfolio_holdings ph
            JOIN portfolio p ON ph.portfolio_id = p.portfolio_id
            WHERE ph.holding_id = %s AND ph.portfolio_id = %s AND p.user_id = %s
        """, (holding_id, portfolio_id, current_user["user_id"]))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Holding not found")

        cursor.execute("""
            UPDATE portfolio_holdings
            SET quantity = %s, avg_price = %s, updated_at = NOW()
            WHERE holding_id = %s
        """, (holding.quantity, holding.avg_price, holding_id))

        db.commit()

        return {"message": "Holding updated successfully"}

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.get("/stocks/search")
async def search_stock_by_symbol(symbol: str, current_user: dict = Depends(get_current_user)):
    """Search for a stock by symbol for adding to portfolio."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                s.stock_id, 
                s.symbol, 
                s.company_name,
                f.current_price
            FROM stocks s
            LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
            WHERE s.symbol = %s
        """, (symbol.upper(),))
        
        stock = cursor.fetchone()
        if stock:
            return stock
        else:
            raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()

@router.get("/summary")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)):
    """Get portfolio summary for the current user."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT p.portfolio_id) as total_portfolios,
                COUNT(ph.holding_id) as total_holdings,
                COALESCE(SUM(ph.quantity * ph.avg_price), 0) as total_invested,
                COALESCE(SUM(ph.quantity * f.current_price), 0) as current_value,
                COALESCE(SUM(ph.quantity * f.current_price) - SUM(ph.quantity * ph.avg_price), 0) as total_gain_loss
            FROM portfolio p
            LEFT JOIN portfolio_holdings ph ON p.portfolio_id = ph.portfolio_id
            LEFT JOIN fundamentals f ON ph.stock_id = f.stock_id
            WHERE p.user_id = %s
        """, (current_user["user_id"],))
        
        summary = cursor.fetchone()
        
        if summary['total_invested'] > 0:
            summary['gain_loss_percent'] = (summary['total_gain_loss'] / summary['total_invested']) * 100
        else:
            summary['gain_loss_percent'] = 0
            
        return summary
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        db.close()