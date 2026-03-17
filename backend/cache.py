import redis
import json
import os
from typing import Optional, Any
from functools import wraps
import hashlib

class RedisCache:
    """Redis cache manager with graceful fallback when Redis is unavailable."""
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.default_ttl = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default
        
        self.client = None
        self.enabled = True
        self._connect()
    
    def _connect(self):
        """Connect to Redis server with graceful fallback."""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password if self.redis_password else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.client.ping()
            self.enabled = True
            print(f"✅ Redis cache enabled at {self.redis_host}:{self.redis_port}")
        except redis.ConnectionError:
            print(f"⚠️ Redis not available at {self.redis_host}:{self.redis_port}")
            print("📊 Application will run without caching (direct database queries)")
            self.client = None
            self.enabled = False
        except Exception as e:
            print(f"⚠️ Redis initialization error: {e}")
            print("📊 Application will run without caching (direct database queries)")
            self.client = None
            self.enabled = False
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.enabled or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            self.enabled = False
            print("⚠️ Redis connection lost. Falling back to direct database queries.")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None if cache unavailable or key not found."""
        if not self.is_available():
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.RedisError:
            self.enabled = False
            print("⚠️ Redis error during get. Falling back to database.")
            return None
        except json.JSONDecodeError:
            self.delete(key)
            return None
        except Exception as e:
            print(f"⚠️ Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL. Returns False if cache unavailable."""
        if not self.is_available():
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            return True
        except redis.RedisError as e:
            self.enabled = False
            print(f"⚠️ Redis error during set: {e}. Continuing without cache.")
            return False
        except (TypeError, ValueError) as e:
            # Serialization error
            print(f"⚠️ Cannot serialize value for caching: {e}")
            print(f"   Key: {key}")
            print(f"   Value type: {type(value)}")
            return False
        except Exception as e:
            print(f"⚠️ Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache. Returns False if cache unavailable."""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(key)
            return True
        except redis.RedisError:
            self.enabled = False
            return False
        except Exception as e:
            print(f"⚠️ Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern. Returns 0 if cache unavailable."""
        if not self.is_available():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError:
            self.enabled = False
            return 0
        except Exception as e:
            print(f"⚠️ Cache delete pattern error: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache. Returns False if cache unavailable."""
        if not self.is_available():
            return False
        
        try:
            self.client.flushdb()
            return True
        except redis.RedisError:
            self.enabled = False
            return False
        except Exception as e:
            print(f"⚠️ Cache clear error: {e}")
            return False
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]        
        for arg in args:
            key_parts.append(str(arg))        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        key = ":".join(key_parts)
        if len(key) > 200:
            hash_obj = hashlib.md5(key.encode())
            key = f"{prefix}:{hash_obj.hexdigest()}"
        
        return key


cache = RedisCache()

def cached(prefix: str, ttl: Optional[int] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.is_available():
                return func(*args, **kwargs)            
            cache_key = cache.generate_key(prefix, *args, **kwargs)            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                print(f"✅ Cache hit: {cache_key}")
                return cached_result            
            result = func(*args, **kwargs)            
            if cache.is_available():
                cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
