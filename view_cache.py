#!/usr/bin/env python3
"""
Redis Cache Viewer - View and manage cached data
Usage: python view_cache.py [command]
"""

import redis
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

# Load environment variables
load_dotenv()

class CacheViewer:
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password if self.redis_password else None,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.client.ping()
            self.connected = True
            print(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
            print()
        except redis.ConnectionError:
            print(f"❌ Cannot connect to Redis at {self.redis_host}:{self.redis_port}")
            print("Make sure Redis is running:")
            print("  WSL: sudo service redis-server start")
            print("  Docker: docker start redis")
            self.connected = False
            sys.exit(1)
    
    def list_all_keys(self):
        """List all keys in Redis."""
        if not self.connected:
            return
        
        keys = self.client.keys("*")
        
        if not keys:
            print("📭 No keys found in cache")
            return
        
        print(f"📊 Total Keys: {len(keys)}")
        print("=" * 80)
        
        for i, key in enumerate(keys, 1):
            ttl = self.client.ttl(key)
            key_type = self.client.type(key)
            
            ttl_str = f"{ttl}s" if ttl > 0 else "No expiry" if ttl == -1 else "Expired"
            
            print(f"{i}. {key}")
            print(f"   Type: {key_type} | TTL: {ttl_str}")
            print()
    
    def view_key(self, key_pattern=None):
        """View content of specific key(s)."""
        if not self.connected:
            return
        
        if key_pattern:
            keys = self.client.keys(key_pattern)
        else:
            keys = self.client.keys("*")
        
        if not keys:
            print(f"❌ No keys found matching: {key_pattern or '*'}")
            return
        
        for key in keys:
            print("=" * 80)
            print(f"🔑 Key: {key}")
            print("-" * 80)
            
            ttl = self.client.ttl(key)
            ttl_str = f"{ttl}s ({ttl//60}m {ttl%60}s)" if ttl > 0 else "No expiry" if ttl == -1 else "Expired"
            print(f"⏱️  TTL: {ttl_str}")
            
            key_type = self.client.type(key)
            print(f"📝 Type: {key_type}")
            
            try:
                value = self.client.get(key)
                if value:
                    # Try to parse as JSON for pretty printing
                    try:
                        data = json.loads(value)
                        print(f"📦 Value:")
                        print(json.dumps(data, indent=2))
                        
                        # Show summary for screener results
                        if isinstance(data, dict) and 'results' in data:
                            print(f"\n📊 Summary:")
                            print(f"   - Results: {len(data.get('results', []))} stocks")
                            print(f"   - Has Quarterly: {data.get('has_quarterly', False)}")
                            if data.get('dsl'):
                                print(f"   - DSL: {data['dsl']}")
                    except json.JSONDecodeError:
                        print(f"📦 Value: {value}")
                else:
                    print("📦 Value: (empty)")
            except Exception as e:
                print(f"❌ Error reading value: {e}")
            
            print()
    
    def get_stats(self):
        """Get Redis statistics."""
        if not self.connected:
            return
        
        info = self.client.info()
        
        print("📊 Redis Statistics")
        print("=" * 80)
        print(f"Version: {info.get('redis_version', 'N/A')}")
        print(f"Uptime: {info.get('uptime_in_days', 0)} days")
        print(f"Connected Clients: {info.get('connected_clients', 0)}")
        print()
        
        print("💾 Memory")
        print("-" * 80)
        print(f"Used Memory: {info.get('used_memory_human', 'N/A')}")
        print(f"Peak Memory: {info.get('used_memory_peak_human', 'N/A')}")
        print(f"Memory Fragmentation: {info.get('mem_fragmentation_ratio', 'N/A')}")
        print()
        
        print("🗄️ Database")
        print("-" * 80)
        print(f"Total Keys: {self.client.dbsize()}")
        print(f"Expired Keys: {info.get('expired_keys', 0)}")
        print(f"Evicted Keys: {info.get('evicted_keys', 0)}")
        print()
        
        print("⚡ Performance")
        print("-" * 80)
        print(f"Total Commands: {info.get('total_commands_processed', 0):,}")
        print(f"Commands/sec: {info.get('instantaneous_ops_per_sec', 0)}")
        print(f"Keyspace Hits: {info.get('keyspace_hits', 0):,}")
        print(f"Keyspace Misses: {info.get('keyspace_misses', 0):,}")
        
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        if hits + misses > 0:
            hit_rate = (hits / (hits + misses)) * 100
            print(f"Hit Rate: {hit_rate:.2f}%")
        print()
    
    def search_keys(self, pattern):
        """Search for keys matching pattern."""
        if not self.connected:
            return
        
        keys = self.client.keys(pattern)
        
        if not keys:
            print(f"❌ No keys found matching: {pattern}")
            return
        
        print(f"🔍 Found {len(keys)} key(s) matching '{pattern}':")
        print("=" * 80)
        
        for i, key in enumerate(keys, 1):
            ttl = self.client.ttl(key)
            ttl_str = f"{ttl}s" if ttl > 0 else "No expiry" if ttl == -1 else "Expired"
            print(f"{i}. {key} (TTL: {ttl_str})")
        print()
    
    def delete_key(self, key_pattern):
        """Delete key(s) matching pattern."""
        if not self.connected:
            return
        
        keys = self.client.keys(key_pattern)
        
        if not keys:
            print(f"❌ No keys found matching: {key_pattern}")
            return
        
        print(f"⚠️  Found {len(keys)} key(s) to delete:")
        for key in keys:
            print(f"   - {key}")
        
        confirm = input("\nAre you sure you want to delete these keys? (yes/no): ")
        if confirm.lower() == 'yes':
            deleted = self.client.delete(*keys)
            print(f"✅ Deleted {deleted} key(s)")
        else:
            print("❌ Deletion cancelled")
    
    def clear_all(self):
        """Clear all cache."""
        if not self.connected:
            return
        
        total_keys = self.client.dbsize()
        
        if total_keys == 0:
            print("📭 Cache is already empty")
            return
        
        print(f"⚠️  WARNING: This will delete ALL {total_keys} keys in the cache!")
        confirm = input("Are you sure? Type 'DELETE ALL' to confirm: ")
        
        if confirm == 'DELETE ALL':
            self.client.flushdb()
            print("✅ All cache cleared")
        else:
            print("❌ Clear cancelled")
    
    def monitor_cache(self):
        """Monitor cache in real-time."""
        if not self.connected:
            return
        
        print("🔴 Monitoring Redis cache (Press Ctrl+C to stop)...")
        print("=" * 80)
        
        try:
            pubsub = self.client.pubsub()
            
            # Monitor all commands
            print("Watching all Redis commands...")
            print()
            
            # Use MONITOR command
            with self.client.monitor() as monitor:
                for command in monitor:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {command}")
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
        except Exception as e:
            print(f"❌ Error: {e}")


def print_help():
    """Print help message."""
    print("""
Redis Cache Viewer - View and manage cached data

Usage: python view_cache.py [command] [args]

Commands:
  list              List all keys in cache
  view [pattern]    View content of key(s) (default: all keys)
  search <pattern>  Search for keys matching pattern
  stats             Show Redis statistics
  delete <pattern>  Delete key(s) matching pattern
  clear             Clear all cache
  monitor           Monitor cache in real-time
  help              Show this help message

Examples:
  python view_cache.py list
  python view_cache.py view screener:*
  python view_cache.py search "screener:*"
  python view_cache.py stats
  python view_cache.py delete "screener:pe*"
  python view_cache.py clear

Patterns:
  *         Match any characters
  ?         Match single character
  [abc]     Match a, b, or c
  [a-z]     Match any character from a to z
    """)


def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_help()
        return
    
    viewer = CacheViewer()
    
    if command == "list":
        viewer.list_all_keys()
    
    elif command == "view":
        pattern = sys.argv[2] if len(sys.argv) > 2 else None
        viewer.view_key(pattern)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ Error: search requires a pattern")
            print("Usage: python view_cache.py search <pattern>")
            return
        viewer.search_keys(sys.argv[2])
    
    elif command == "stats":
        viewer.get_stats()
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Error: delete requires a pattern")
            print("Usage: python view_cache.py delete <pattern>")
            return
        viewer.delete_key(sys.argv[2])
    
    elif command == "clear":
        viewer.clear_all()
    
    elif command == "monitor":
        viewer.monitor_cache()
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
