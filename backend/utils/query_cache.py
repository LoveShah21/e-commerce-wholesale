"""
Query Result Caching Utilities

Provides caching decorators and utilities for optimizing database queries.
Uses Django's cache framework with configurable backends.
"""

from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Callable, Optional


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a unique cache key based on function arguments.
    
    Args:
        prefix: Cache key prefix (usually function name)
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Unique cache key string
    """
    # Create a string representation of arguments
    key_data = {
        'args': str(args),
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    
    # Hash the key string for consistent length
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"


def cache_query_result(timeout: int = 300, key_prefix: Optional[str] = None):
    """
    Decorator to cache query results.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Optional custom cache key prefix
    
    Usage:
        @cache_query_result(timeout=600, key_prefix='product_list')
        def get_products(category=None):
            return Product.objects.filter(category=category)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            prefix = key_prefix or f"query:{func.__module__}.{func.__name__}"
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            
            if result is not None:
                return result
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs) -> None:
    """
    Invalidate a specific cache entry.
    
    Args:
        key_prefix: Cache key prefix to invalidate
        *args: Positional arguments used in original cache key
        **kwargs: Keyword arguments used in original cache key
    """
    cache_key = generate_cache_key(key_prefix, *args, **kwargs)
    cache.delete(cache_key)


def invalidate_cache_pattern(pattern: str) -> None:
    """
    Invalidate all cache entries matching a pattern.
    
    Note: This requires Redis or Memcached backend with pattern support.
    For simple cache backends, use specific invalidation.
    
    Args:
        pattern: Cache key pattern (e.g., 'product:*')
    """
    try:
        # This works with Redis backend
        cache.delete_pattern(pattern)
    except AttributeError:
        # Fallback for backends without pattern support
        pass


class CachedQuerySet:
    """
    Context manager for caching queryset results.
    
    Usage:
        with CachedQuerySet('products', timeout=600) as cached:
            products = cached.get_or_set(
                lambda: Product.objects.filter(active=True)
            )
    """
    
    def __init__(self, cache_prefix: str, timeout: int = 300):
        self.cache_prefix = cache_prefix
        self.timeout = timeout
        self.cache_key = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def get_or_set(self, query_func: Callable, *args, **kwargs) -> Any:
        """
        Get cached result or execute query and cache it.
        
        Args:
            query_func: Function that returns queryset
            *args: Arguments for cache key generation
            **kwargs: Keyword arguments for cache key generation
        
        Returns:
            Query result (from cache or fresh)
        """
        self.cache_key = generate_cache_key(self.cache_prefix, *args, **kwargs)
        
        result = cache.get(self.cache_key)
        
        if result is None:
            result = query_func()
            cache.set(self.cache_key, result, self.timeout)
        
        return result
    
    def invalidate(self):
        """Invalidate the current cache entry."""
        if self.cache_key:
            cache.delete(self.cache_key)


# Predefined cache timeouts for different data types
CACHE_TIMEOUTS = {
    'product_catalog': 600,      # 10 minutes
    'product_detail': 300,       # 5 minutes
    'dashboard_stats': 180,      # 3 minutes
    'tax_config': 3600,          # 1 hour
    'user_profile': 300,         # 5 minutes
    'cart': 60,                  # 1 minute
    'order_list': 120,           # 2 minutes
    'inventory': 300,            # 5 minutes
}


def get_cache_timeout(cache_type: str) -> int:
    """
    Get predefined cache timeout for a data type.
    
    Args:
        cache_type: Type of data being cached
    
    Returns:
        Timeout in seconds
    """
    return CACHE_TIMEOUTS.get(cache_type, 300)


# Cache invalidation helpers for common operations

def invalidate_product_cache(product_id: Optional[int] = None):
    """Invalidate product-related caches."""
    if product_id:
        invalidate_cache_pattern(f"query:*product*:{product_id}:*")
    else:
        invalidate_cache_pattern("query:*product*")


def invalidate_order_cache(user_id: Optional[int] = None):
    """Invalidate order-related caches."""
    if user_id:
        invalidate_cache_pattern(f"query:*order*:{user_id}:*")
    else:
        invalidate_cache_pattern("query:*order*")


def invalidate_dashboard_cache():
    """Invalidate dashboard statistics cache."""
    invalidate_cache_pattern("query:*dashboard*")


def invalidate_inventory_cache():
    """Invalidate inventory-related caches."""
    invalidate_cache_pattern("query:*inventory*")
    invalidate_cache_pattern("query:*material*")
