from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import router as auth_router
from backend.ai.routes import router as ai_router
from backend.portfolio import router as portfolio_router
from backend.alerts import router as alerts_router
from backend.cache import cache

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

@app.get("/health")
def health_check():
    """Health check endpoint with cache status."""
    return {
        "status": "healthy",
        "cache_enabled": cache.is_available(),
        "cache_type": "redis" if cache.is_available() else "none"
    }

@app.post("/cache/clear")
def clear_cache():
    """Clear all cache (admin endpoint)."""
    if cache.is_available():
        cache.clear_all()
        return {"message": "Cache cleared successfully"}
    return {"message": "Cache not available"}

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics."""
    if cache.is_available():
        try:
            info = cache.client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "total_keys": cache.client.dbsize(),
                "uptime_days": info.get("uptime_in_days", 0)
            }
        except:
            return {"enabled": False, "error": "Cannot retrieve stats"}
    return {"enabled": False, "message": "Cache not available"}
