"""
Cache layer using Upstash Redis (TLS, via REDIS_URL).
Falls back gracefully to no-cache if the URL is missing or connection fails.
"""

import os
import json
import hashlib
import redis
from typing import Optional, Any
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class RedisCache:
    """
    Redis cache backed by Upstash (or any Redis-compatible server).
    Reads REDIS_URL from env — supports rediss:// (TLS) and redis:// (plain).
    Gracefully falls back to no-cache on connection failure.
    """

    def __init__(self):
        self.default_ttl = int(os.getenv("CACHE_TTL", 3600))
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        self._connect()

    def _connect(self):
        url = os.getenv("REDIS_URL", "")
        if not url:
            print("[cache] REDIS_URL not set — running without cache")
            return
        try:
            self.client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            self.client.ping()
            self.enabled = True
            host = url.split("@")[-1] if "@" in url else url
            print(f"[cache] Upstash Redis connected  →  {host}")
        except redis.AuthenticationError:
            print("[cache] Redis auth failed — check REDIS_URL password")
        except redis.ConnectionError as e:
            print(f"[cache] Redis connection failed: {e}")
        except Exception as e:
            print(f"[cache] Redis init error: {e}")

    # ── Public interface ────────────────────────────────────────────────────

    def is_available(self) -> bool:
        if not self.enabled or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            self.enabled = False
            return False

    def get(self, key: str) -> Optional[Any]:
        if not self.is_available():
            return None
        try:
            raw = self.client.get(key)
            return json.loads(raw) if raw else None
        except (redis.RedisError, json.JSONDecodeError) as e:
            print(f"[cache] GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.is_available():
            return False
        try:
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl or self.default_ttl, serialized)
            return True
        except (TypeError, ValueError) as e:
            print(f"[cache] Serialization error for key '{key}': {e}")
            return False
        except redis.RedisError as e:
            print(f"[cache] SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self.is_available():
            return False
        try:
            self.client.delete(key)
            return True
        except redis.RedisError:
            return False

    def delete_pattern(self, pattern: str) -> int:
        if not self.is_available():
            return 0
        try:
            keys = self.client.keys(pattern)
            return self.client.delete(*keys) if keys else 0
        except redis.RedisError:
            return 0

    def clear_all(self) -> bool:
        if not self.is_available():
            return False
        try:
            self.client.flushdb()
            return True
        except redis.RedisError:
            return False

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        parts = [prefix] + [str(a) for a in args]
        parts += [f"{k}:{v}" for k, v in sorted(kwargs.items())]
        key = ":".join(parts)
        if len(key) > 200:
            key = f"{prefix}:{hashlib.md5(key.encode()).hexdigest()}"
        return key

    def get_stats(self) -> dict:
        if not self.is_available():
            return {"enabled": False, "message": "Cache not available"}
        try:
            info = self.client.info()
            return {
                "enabled":      True,
                "type":         "upstash",
                "total_keys":   self.client.dbsize(),
                "used_memory":  info.get("used_memory_human", "N/A"),
                "uptime_days":  info.get("uptime_in_days", 0),
                "hit_rate":     _hit_rate(info),
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


def _hit_rate(info: dict) -> str:
    hits   = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total  = hits + misses
    return f"{hits / total * 100:.1f}%" if total > 0 else "N/A"


# Singleton used across the whole backend
cache = RedisCache()
