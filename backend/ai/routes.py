from fastapi import APIRouter, Depends, HTTPException
from backend.ai.engine import run_engine
from backend.auth import get_current_user
from backend.cache import cache

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/screener")
def screener(query: str, current_user=Depends(get_current_user)):
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        query_normalized = query.strip().lower()        
        cache_key = cache.generate_key("screener", query_normalized)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            print(f"✅ Returning cached result for query: {query_normalized}")
            return cached_result
        dsl, result_data = run_engine(query.strip())
        response = {
            "dsl": dsl, 
            "results": result_data.get('stocks', []),
            "quarterly_data": result_data.get('quarterly_data', {}),
            "has_quarterly": result_data.get('has_quarterly', False)
        }        
        cache.set(cache_key, response, ttl=600)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        if "Database connection issue" in error_msg:
            raise HTTPException(status_code=503, detail="Database connection issue. Please try again.")
        else:
            raise HTTPException(status_code=500, detail=f"Processing error: {error_msg}")