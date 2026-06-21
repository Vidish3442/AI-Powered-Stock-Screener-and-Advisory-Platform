import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.auth import get_current_user
from backend.database import get_db
from backend.alert_checker import AlertChecker, check_alerts_now
from backend.security import rate_limiter
import mysql.connector
from datetime import datetime

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)

class AlertCreate(BaseModel):
    stock_id: int = Field(gt=0)
    portfolio_id: int = Field(gt=0)
    metric: str = Field(min_length=1, max_length=50)
    operator: str = Field(min_length=1, max_length=2)
    threshold: float = Field(ge=0, allow_inf_nan=False)

class AlertResponse(BaseModel):
    alert_id: int
    user_id: int
    stock_id: int
    portfolio_id: int
    symbol: str
    company_name: str
    metric: str
    operator: str
    threshold: float
    is_active: bool
    created_at: datetime
    times_triggered: int
    last_triggered: Optional[datetime]

class AlertEventResponse(BaseModel):
    event_id: int
    alert_id: int
    stock_id: int
    symbol: str
    company_name: str
    metric: str
    operator: str
    threshold: float
    triggered_value: float
    triggered_at: datetime

@router.get("/", response_model=List[AlertResponse])
async def get_user_alerts(current_user: dict = Depends(get_current_user)):
    """Get all alerts for the current user."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                a.alert_id,
                a.user_id,
                a.stock_id,
                a.portfolio_id,
                s.symbol,
                s.company_name,
                a.metric,
                a.operator,
                a.threshold,
                a.is_active,
                a.created_at,
                COUNT(ae.event_id) as times_triggered,
                MAX(ae.triggered_at) as last_triggered
            FROM alerts a
            JOIN stocks s ON a.stock_id = s.stock_id
            LEFT JOIN alert_event ae ON a.alert_id = ae.alert_id
            WHERE a.user_id = %s
            GROUP BY a.alert_id, a.user_id, a.stock_id, a.portfolio_id, s.symbol, s.company_name, 
                     a.metric, a.operator, a.threshold, a.is_active, a.created_at
            ORDER BY a.created_at DESC
        """, (current_user["user_id"],))
        
        alerts = cursor.fetchall()
        return alerts
        
    except mysql.connector.Error:
        logger.exception("Failed to list alerts")
        raise HTTPException(status_code=500, detail="Unable to load alerts")
    finally:
        cursor.close()
        db.close()

@router.post("/", response_model=dict)
async def create_alert(alert: AlertCreate, current_user: dict = Depends(get_current_user)):
    """Create a new alert for the current user."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        valid_operators = ['>', '<', '>=', '<=', '=']
        if alert.operator not in valid_operators:
            raise HTTPException(status_code=400, detail=f"Invalid operator. Must be one of: {', '.join(valid_operators)}")
        
        valid_metrics = ['price', 'pe_ratio', 'market_cap', 'eps', 'roe', 'dividend_yield']
        if alert.metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}")
        
        cursor.execute("SELECT stock_id FROM stocks WHERE stock_id = %s", (alert.stock_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Stock not found")
        
        cursor.execute("SELECT portfolio_id FROM portfolio WHERE portfolio_id = %s AND user_id = %s", 
                      (alert.portfolio_id, current_user["user_id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found or doesn't belong to you")
        
        cursor.execute("""
            INSERT INTO alerts (user_id, stock_id, portfolio_id, metric, operator, threshold, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (current_user["user_id"], alert.stock_id, alert.portfolio_id, alert.metric, alert.operator, alert.threshold))
        
        alert_id = cursor.lastrowid
        db.commit()
        
        return {"alert_id": alert_id, "message": "Alert created successfully"}
        
    except mysql.connector.Error:
        logger.exception("Failed to create alert")
        raise HTTPException(status_code=500, detail="Unable to create alert")
    finally:
        cursor.close()
        db.close()

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, current_user: dict = Depends(get_current_user)):
    """Delete an alert."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT alert_id FROM alerts 
            WHERE alert_id = %s AND user_id = %s
        """, (alert_id, current_user["user_id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Alert not found")
        
        cursor.execute("DELETE FROM alerts WHERE alert_id = %s", (alert_id,))
        db.commit()
        
        return {"message": "Alert deleted successfully"}
        
    except mysql.connector.Error:
        logger.exception("Failed to delete alert")
        raise HTTPException(status_code=500, detail="Unable to delete alert")
    finally:
        cursor.close()
        db.close()

@router.patch("/{alert_id}/toggle")
async def toggle_alert(alert_id: int, current_user: dict = Depends(get_current_user)):
    """Toggle alert active status."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT is_active FROM alerts 
            WHERE alert_id = %s AND user_id = %s
        """, (alert_id, current_user["user_id"]))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        new_status = not result[0]
        cursor.execute("""
            UPDATE alerts SET is_active = %s 
            WHERE alert_id = %s
        """, (new_status, alert_id))
        db.commit()
        
        return {"message": f"Alert {'activated' if new_status else 'deactivated'} successfully", "is_active": new_status}
        
    except mysql.connector.Error:
        logger.exception("Failed to toggle alert")
        raise HTTPException(status_code=500, detail="Unable to update alert")
    finally:
        cursor.close()
        db.close()

@router.get("/events", response_model=List[AlertEventResponse])
async def get_alert_events(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Get most recent alert event for each alert."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                ae.event_id,
                ae.alert_id,
                ae.stock_id,
                s.symbol,
                s.company_name,
                a.metric,
                a.operator,
                a.threshold,
                ae.triggered_value,
                ae.triggered_at
            FROM alert_event ae
            JOIN alerts a ON ae.alert_id = a.alert_id
            JOIN stocks s ON ae.stock_id = s.stock_id
            WHERE a.user_id = %s
            AND ae.triggered_at = (
                SELECT MAX(ae2.triggered_at)
                FROM alert_event ae2
                WHERE ae2.alert_id = ae.alert_id
            )
            ORDER BY ae.triggered_at DESC
            LIMIT %s
        """, (current_user["user_id"], limit))
        
        events = cursor.fetchall()
        return events
        
    except mysql.connector.Error:
        logger.exception("Failed to load alert events")
        raise HTTPException(status_code=500, detail="Unable to load alert events")
    finally:
        cursor.close()
        db.close()

@router.get("/stocks/search")
async def search_stock_by_symbol(
    symbol: str = Query(min_length=1, max_length=20),
    current_user: dict = Depends(get_current_user),
):
    """Search for a stock by symbol."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT stock_id, symbol, company_name 
            FROM stocks 
            WHERE symbol = %s
        """, (symbol.upper(),))
        
        stock = cursor.fetchone()
        if stock:
            return stock
        else:
            raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")
        
    except mysql.connector.Error:
        logger.exception("Failed to search stocks")
        raise HTTPException(status_code=500, detail="Unable to search stocks")
    finally:
        cursor.close()
        db.close()

@router.get("/stocks/list")
async def list_all_stocks(current_user: dict = Depends(get_current_user)):
    """Get all stocks for dropdown selection."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT stock_id, symbol, company_name 
            FROM stocks 
            ORDER BY symbol
        """)
        
        stocks = cursor.fetchall()
        return stocks
        
    except mysql.connector.Error:
        logger.exception("Failed to list stocks")
        raise HTTPException(status_code=500, detail="Unable to list stocks")
    finally:
        cursor.close()
        db.close()

@router.get("/summary")
async def get_alert_summary(current_user: dict = Depends(get_current_user)):
    """Get alert summary for the current user."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT a.alert_id) as total_alerts,
                SUM(CASE WHEN a.is_active = TRUE THEN 1 ELSE 0 END) as active_alerts,
                COUNT(DISTINCT ae.event_id) as total_triggers,
                COUNT(DISTINCT a.stock_id) as stocks_monitored
            FROM alerts a
            LEFT JOIN alert_event ae ON a.alert_id = ae.alert_id
            WHERE a.user_id = %s
        """, (current_user["user_id"],))
        
        summary = cursor.fetchone()
        return summary
        
    except mysql.connector.Error:
        logger.exception("Failed to load alert summary")
        raise HTTPException(status_code=500, detail="Unable to load alert summary")
    finally:
        cursor.close()
        db.close()

@router.post("/check")
async def check_alerts(request: Request, current_user: dict = Depends(get_current_user)):
    """Manually trigger alert checking for the authenticated user."""
    rate_limiter.check(
        f"alert-check:user:{current_user['user_id']}",
        limit=10,
        window_seconds=60,
    )
    try:
        results = check_alerts_now(current_user["user_id"])
        return {
            "message": "Alert check completed",
            "results": results
        }
    except Exception:
        logger.exception("Alert check failed")
        raise HTTPException(status_code=500, detail="Unable to check alerts")

@router.get("/notifications")
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get recent alert notifications for the current user."""
    checker = AlertChecker()
    try:
        notifications = checker.get_user_triggered_alerts(current_user["user_id"], limit)
        return notifications
    except Exception:
        logger.exception("Failed to load notifications")
        raise HTTPException(status_code=500, detail="Unable to load notifications")
