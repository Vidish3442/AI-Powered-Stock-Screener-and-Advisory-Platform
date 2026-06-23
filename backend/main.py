import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import router as auth_router
from backend.ai.routes import router as ai_router
from backend.portfolio import router as portfolio_router
from backend.alerts import router as alerts_router
from backend.cache import cache
from backend.security import client_ip, rate_limiter

app = FastAPI(title="AI Stock Screener")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(portfolio_router)
app.include_router(alerts_router)


def require_cache_admin(
    request: Request,
    x_admin_token: str | None = Header(default=None),
):
    """Require a separate secret for destructive cache administration."""
    rate_limiter.check(f"cache-admin:{client_ip(request)}", limit=10, window_seconds=60)
    expected = os.getenv("CACHE_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache administration is disabled",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cache administrator authorization required",
        )

@app.get("/health")
def health_check():
    """Health check endpoint with cache status."""
    return {
        "status": "healthy",
        "cache_enabled": cache.is_available(),
        "cache_type": "upstash" if cache.is_available() else "none"
    }

@app.post("/cache/clear", dependencies=[Depends(require_cache_admin)])
def clear_cache():
    """Clear all cache (admin endpoint)."""
    if cache.is_available():
        cache.clear_all()
        return {"message": "Cache cleared successfully"}
    return {"message": "Cache not available"}

@app.get("/cache/stats", dependencies=[Depends(require_cache_admin)])
def cache_stats():
    """Get cache statistics."""
    return cache.get_stats()
