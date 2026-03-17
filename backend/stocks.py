from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt
import os
from backend.database import get_db

router = APIRouter(prefix="/stocks", tags=["Stocks"])
security = HTTPBearer()

def get_user(token=Depends(security)):
    try:
        return jwt.decode(
            token.credentials,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )["email"] 
    except:
        raise HTTPException(401, "Invalid token")

@router.get("/")
def list_stocks(user=Depends(get_user)):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT s.symbol, s.company_name, s.sector,
               f.pe_ratio, f.eps, f.roe
        FROM stocks s
        LEFT JOIN fundamentals f ON s.stock_id = f.stock_id
        ORDER BY s.company_name
    """)

    rows = cur.fetchall()
    cur.close()
    db.close()

    return [
        {
            "symbol": r[0],
            "company": r[1],
            "sector": r[2],
            "pe_ratio": r[3],
            "eps": r[4],
            "roe": r[5]
        } for r in rows
    ]
