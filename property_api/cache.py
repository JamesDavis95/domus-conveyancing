"""
Property Data Cache System
Manages caching for all property API data with configurable TTL and storage backends
"""
import asyncio
import json
import hashlib
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import aiofiles
import os
from pathlib import Path


class PropertyDataCache:
    """
    Flexible cache system for property data with multiple storage backends
    """
    
    def __init__(
        self, 
        cache_name: str,
        ttl_hours: int = 24,
        backend: str = 'file',
        max_size_mb: int = 100
    ):
        """
        Initialize cache system
        
        Args:
            cache_name: Name/namespace for this cache
            ttl_hours: Time to live in hours
            backend: Storage backend ('file', 'memory', 'redis')
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_name = cache_name
        self.ttl_hours = ttl_hours
        self.backend = backend
        self.max_size_mb = max_size_mb
        
        # File-based cache settings
        self.cache_dir = Path("/tmp/domus_property_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, datetime] = {}
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        
        try:
            if self.backend == 'file':
                return await self._get_from_file(key)
            elif self.backend == 'memory':
                return await self._get_from_memory(key)
            else:  # Redis or other backends
                return await self._get_from_redis(key)
                
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            self.stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_hours: Custom TTL, defaults to instance TTL
            
        Returns:
            True if successfully cached
        """
        
        try:
            ttl = ttl_hours or self.ttl_hours
            
            if self.backend == 'file':
                success = await self._set_to_file(key, value, ttl)
            elif self.backend == 'memory':
                success = await self._set_to_memory(key, value, ttl)
            else:  # Redis or other backends
                success = await self._set_to_redis(key, value, ttl)
            
            if success:
                self.stats['sets'] += 1
            
            return success
            
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successfully deleted
        """
        
        try:
            if self.backend == 'file':
                return await self._delete_from_file(key)
            elif self.backend == 'memory':
                return await self._delete_from_memory(key)
            else:
                return await self._delete_from_redis(key)
                
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cache entries for this cache name
        
        Returns:
            True if successfully cleared
        """
        
        try:
            if self.backend == 'file':
                return await self._clear_file_cache()
            elif self.backend == 'memory':
                return await self._clear_memory_cache()
            else:
                return await self._clear_redis_cache()
                
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        hit_rate = (
            self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) * 100
            if (self.stats['hits'] + self.stats['misses']) > 0 else 0
        )
        
        cache_size = await self._get_cache_size()
        
        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size_mb': round(cache_size, 2),
            'backend': self.backend,
            'ttl_hours': self.ttl_hours
        }
    
    def _generate_cache_key(self, key: str) -> str:
        """Generate standardized cache key"""
        full_key = f"{self.cache_name}:{key}"
        # Hash long keys to avoid filesystem limitations
        if len(full_key) > 200:
            return hashlib.md5(full_key.encode()).hexdigest()
        return full_key.replace('/', '_').replace('\\', '_')
    
    def _generate_cache_path(self, key: str) -> Path:
        """Generate file path for cache key"""
        cache_key = self._generate_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"
    
    async def _get_from_file(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        
        cache_path = self._generate_cache_path(key)
        
        if not cache_path.exists():
            self.stats['misses'] += 1
            return None
        
        try:
            async with aiofiles.open(cache_path, 'r') as f:
                content = await f.read()
                cache_data = json.loads(content)
            
            # Check expiry
            expiry = datetime.fromisoformat(cache_data['expires'])
            if datetime.now() > expiry:
                # Expired - delete file
                cache_path.unlink(missing_ok=True)
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            return cache_data['value']
            
        except Exception as e:
            # Clean up corrupted cache file
            cache_path.unlink(missing_ok=True)
            self.stats['misses'] += 1
            return None
    
    async def _set_to_file(self, key: str, value: Any, ttl_hours: int) -> bool:
        """Set value in file cache"""
        
        cache_path = self._generate_cache_path(key)
        expires = datetime.now() + timedelta(hours=ttl_hours)
        
        cache_data = {
            'value': value,
            'expires': expires.isoformat(),
            'created': datetime.now().isoformat(),
            'ttl_hours': ttl_hours
        }
        
        try:
            async with aiofiles.open(cache_path, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
            
            # Clean up old cache files if approaching size limit
            await self._cleanup_file_cache()
            
            return True
            
        except Exception as e:
            print(f"Error writing cache file: {e}")
            return False
    
    async def _delete_from_file(self, key: str) -> bool:
        """Delete from file cache"""
        
        cache_path = self._generate_cache_path(key)
        
        try:
            cache_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False
    
    async def _clear_file_cache(self) -> bool:
        """Clear file cache for this cache name"""
        
        try:
            pattern = f"{self.cache_name}:*"
            for cache_file in self.cache_dir.glob(f"{self.cache_name}_*.json"):
                cache_file.unlink(missing_ok=True)
            return True
        except Exception:
            return False
    
    async def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        
        cache_key = self._generate_cache_key(key)
        
        if cache_key not in self._memory_cache:
            self.stats['misses'] += 1
            return None
        
        cache_entry = self._memory_cache[cache_key]
        expiry = datetime.fromisoformat(cache_entry['expires'])
        
        if datetime.now() > expiry:
            # Expired
            del self._memory_cache[cache_key]
            self._access_times.pop(cache_key, None)
            self.stats['misses'] += 1
            return None
        
        # Update access time for LRU eviction
        self._access_times[cache_key] = datetime.now()
        
        self.stats['hits'] += 1
        return cache_entry['value']
    
    async def _set_to_memory(self, key: str, value: Any, ttl_hours: int) -> bool:
        """Set value in memory cache"""
        
        cache_key = self._generate_cache_key(key)
        expires = datetime.now() + timedelta(hours=ttl_hours)
        
        cache_entry = {
            'value': value,
            'expires': expires.isoformat(),
            'created': datetime.now().isoformat()
        }
        
        self._memory_cache[cache_key] = cache_entry
        self._access_times[cache_key] = datetime.now()
        
        # Clean up memory if needed
        await self._cleanup_memory_cache()
        
        return True
    
    async def _delete_from_memory(self, key: str) -> bool:
        """Delete from memory cache"""
        
        cache_key = self._generate_cache_key(key)
        
        self._memory_cache.pop(cache_key, None)
        self._access_times.pop(cache_key, None)
        
        return True
    
    async def _clear_memory_cache(self) -> bool:
        """Clear memory cache for this cache name"""
        
        keys_to_delete = [
            k for k in self._memory_cache.keys() 
            if k.startswith(f"{self.cache_name}:")
        ]
        
        for key in keys_to_delete:
            del self._memory_cache[key]
            self._access_times.pop(key, None)
        
        return True
    
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache (placeholder)"""
        # This would implement Redis integration
        # For now, fall back to memory cache
        return await self._get_from_memory(key)
    
    async def _set_to_redis(self, key: str, value: Any, ttl_hours: int) -> bool:
        """Set value in Redis cache (placeholder)"""
        # This would implement Redis integration
        # For now, fall back to memory cache
        return await self._set_to_memory(key, value, ttl_hours)
    
    async def _delete_from_redis(self, key: str) -> bool:
        """Delete from Redis cache (placeholder)"""
        # This would implement Redis integration
        return await self._delete_from_memory(key)
    
    async def _clear_redis_cache(self) -> bool:
        """Clear Redis cache (placeholder)"""
        # This would implement Redis integration
        return await self._clear_memory_cache()
    
    async def _cleanup_file_cache(self):
        """Clean up old file cache entries"""
        
        try:
            cache_size = await self._get_cache_size()
            
            if cache_size > self.max_size_mb:
                # Get all cache files with their modification times
                cache_files = []
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        stat = cache_file.stat()
                        cache_files.append((cache_file, stat.st_mtime))
                    except:
                        continue
                
                # Sort by modification time (oldest first)
                cache_files.sort(key=lambda x: x[1])
                
                # Delete oldest files until under size limit
                for cache_file, _ in cache_files:
                    if await self._get_cache_size() <= self.max_size_mb * 0.8:
                        break
                    
                    cache_file.unlink(missing_ok=True)
                    self.stats['evictions'] += 1
                    
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
    
    async def _cleanup_memory_cache(self):
        """Clean up old memory cache entries"""
        
        # Rough memory usage estimation (simplified)
        if len(self._memory_cache) > 1000:  # Arbitrary limit
            
            # Remove expired entries first
            current_time = datetime.now()
            expired_keys = []
            
            for key, entry in self._memory_cache.items():
                expiry = datetime.fromisoformat(entry['expires'])
                if current_time > expiry:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_cache[key]
                self._access_times.pop(key, None)
                self.stats['evictions'] += 1
            
            # If still too large, remove LRU entries
            if len(self._memory_cache) > 800:
                sorted_keys = sorted(
                    self._access_times.items(),
                    key=lambda x: x[1]
                )
                
                keys_to_remove = sorted_keys[:200]  # Remove 200 oldest
                
                for key, _ in keys_to_remove:
                    self._memory_cache.pop(key, None)
                    self._access_times.pop(key, None)
                    self.stats['evictions'] += 1
    
    async def _get_cache_size(self) -> float:
        """Get cache size in MB"""
        
        if self.backend == 'file':
            total_size = 0
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    total_size += cache_file.stat().st_size
                except:
                    continue
            return total_size / (1024 * 1024)  # Convert to MB
        
        elif self.backend == 'memory':
            # Rough estimation
            import sys
            total_size = sum(
                sys.getsizeof(entry) for entry in self._memory_cache.values()
            )
            return total_size / (1024 * 1024)
        
        else:
            return 0.0


class CacheManager:
    """
    Central manager for all property API caches
    """
    
    def __init__(self):
        self.caches: Dict[str, PropertyDataCache] = {}
        
        # Default cache configurations
        self.cache_configs = {
            'land_registry': {'ttl_hours': 24, 'backend': 'file'},
            'epc_data': {'ttl_hours': 12, 'backend': 'file'},
            'flood_risk': {'ttl_hours': 24, 'backend': 'file'},
            'planning_history': {'ttl_hours': 6, 'backend': 'file'},  # More frequent updates
            'postcode_geocoding': {'ttl_hours': 168, 'backend': 'memory'},  # 7 days, rarely changes
            'property_aggregated': {'ttl_hours': 2, 'backend': 'memory'}  # Short-lived aggregated data
        }
    
    def get_cache(self, cache_name: str) -> PropertyDataCache:
        """
        Get or create cache instance
        
        Args:
            cache_name: Name of the cache
            
        Returns:
            PropertyDataCache instance
        """
        
        if cache_name not in self.caches:
            config = self.cache_configs.get(cache_name, {})
            
            self.caches[cache_name] = PropertyDataCache(
                cache_name=cache_name,
                ttl_hours=config.get('ttl_hours', 24),
                backend=config.get('backend', 'file'),
                max_size_mb=config.get('max_size_mb', 100)
            )
        
        return self.caches[cache_name]
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        
        stats = {}
        for cache_name, cache in self.caches.items():
            stats[cache_name] = await cache.get_stats()
        
        return stats
    
    async def clear_all_caches(self) -> Dict[str, bool]:
        """Clear all caches"""
        
        results = {}
        for cache_name, cache in self.caches.items():
            results[cache_name] = await cache.clear()
        
        return results
    
    async def cleanup_all_caches(self):
        """Run cleanup on all caches"""
        
        cleanup_tasks = []
        for cache in self.caches.values():
            if cache.backend == 'file':
                cleanup_tasks.append(cache._cleanup_file_cache())
            elif cache.backend == 'memory':
                cleanup_tasks.append(cache._cleanup_memory_cache())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions
def get_cache(cache_name: str) -> PropertyDataCache:
    """Get cache instance"""
    return cache_manager.get_cache(cache_name)


async def cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get all cache statistics"""
    return await cache_manager.get_all_stats()


async def clear_all_caches() -> Dict[str, bool]:
    """Clear all caches"""
    return await cache_manager.clear_all_caches()


# Cache decorators
def cached(cache_name: str, ttl_hours: int = 24, key_func=None):
    """
    Decorator to cache function results
    
    Args:
        cache_name: Name of the cache to use
        ttl_hours: Time to live in hours
        key_func: Function to generate cache key from args
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Simple key based on function name and args
                import hashlib
                key_parts = [func.__name__] + [str(arg) for arg in args]
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = hashlib.md5('_'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cache = get_cache(cache_name)
            cached_result = await cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            if result is not None:
                await cache.set(cache_key, result, ttl_hours)
            
            return result
        
        return wrapper
    return decorator