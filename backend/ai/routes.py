import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from backend.ai.engine import run_engine
from backend.auth import get_current_user
from backend.cache import cache
from backend.security import rate_limiter

router = APIRouter(prefix="/ai", tags=["AI"])
logger = logging.getLogger(__name__)

@router.post("/screener")
def screener(
    request: Request,
    query: str = Query(min_length=1, max_length=500),
    current_user=Depends(get_current_user),
):
    rate_limiter.check(
        f"ai-screener:user:{current_user['user_id']}",
        limit=20,
        window_seconds=60,
    )
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        query_normalized = query.strip().lower()        
        # Version the cache because screener responses now always include
        # quarterly data, including for non-quarterly filters.
        cache_key = cache.generate_key("screener_v2", query_normalized)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            print(f"[ai] Returning cached result for query: {query_normalized}")
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
            logger.exception("Screener processing failed")
            raise HTTPException(status_code=500, detail="Unable to process the screener query")
