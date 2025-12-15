"""
Cache Service

Provides centralized caching functionality for the e-commerce platform.
Implements caching strategies for:
- Product catalog
- Dashboard statistics
- Tax configuration
- Inventory data
"""

from django.core.cache import cache
from django.db.models import QuerySet
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
from utils.query_cache import generate_cache_key, get_cache_timeout
import logging

logger = logging.getLogger('services.cache_service')


class CacheService:
    """
    Centralized cache service for managing application-wide caching.
    """
    
    # Cache key prefixes
    PRODUCT_LIST_PREFIX = 'product_list'
    PRODUCT_DETAIL_PREFIX = 'product_detail'
    DASHBOARD_STATS_PREFIX = 'dashboard_stats'
    TAX_CONFIG_PREFIX = 'tax_config'
    INVENTORY_PREFIX = 'inventory'
    
    @staticmethod
    def get_product_list_cache(filters: Optional[Dict] = None) -> Optional[List]:
        """
        Get cached product list.
        
        Args:
            filters: Dictionary of filter parameters (fabric, color, pattern, search)
        
        Returns:
            Cached product list or None if not cached
        """
        cache_key = generate_cache_key(
            CacheService.PRODUCT_LIST_PREFIX,
            filters=filters or {}
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_product_list_cache(data: List, filters: Optional[Dict] = None) -> None:
        """
        Cache product list.
        
        Args:
            data: Product list data to cache
            filters: Dictionary of filter parameters used
        """
        cache_key = generate_cache_key(
            CacheService.PRODUCT_LIST_PREFIX,
            filters=filters or {}
        )
        timeout = get_cache_timeout('product_catalog')
        cache.set(cache_key, data, timeout)
        logger.debug(f"Cached product list with key: {cache_key}")
    
    @staticmethod
    def get_product_detail_cache(product_id: int) -> Optional[Dict]:
        """
        Get cached product detail.
        
        Args:
            product_id: Product ID
        
        Returns:
            Cached product detail or None if not cached
        """
        cache_key = generate_cache_key(
            CacheService.PRODUCT_DETAIL_PREFIX,
            product_id=product_id
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_product_detail_cache(product_id: int, data: Dict) -> None:
        """
        Cache product detail.
        
        Args:
            product_id: Product ID
            data: Product detail data to cache
        """
        cache_key = generate_cache_key(
            CacheService.PRODUCT_DETAIL_PREFIX,
            product_id=product_id
        )
        timeout = get_cache_timeout('product_detail')
        cache.set(cache_key, data, timeout)
        logger.debug(f"Cached product detail for ID {product_id}")
    
    @staticmethod
    def invalidate_product_cache(product_id: Optional[int] = None) -> None:
        """
        Invalidate product caches.
        
        Args:
            product_id: Specific product ID to invalidate, or None for all products
        """
        if product_id:
            # Invalidate specific product detail
            cache_key = generate_cache_key(
                CacheService.PRODUCT_DETAIL_PREFIX,
                product_id=product_id
            )
            cache.delete(cache_key)
            logger.info(f"Invalidated cache for product ID {product_id}")
        
        # Always invalidate product list cache when any product changes
        # Since we can't easily pattern match with locmem cache,
        # we'll use a version key approach
        cache.delete('product_list_version')
        logger.info("Invalidated product list cache")
    
    @staticmethod
    def get_dashboard_stats_cache(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
        threshold: int = 10
    ) -> Optional[Dict]:
        """
        Get cached dashboard statistics.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            days: Number of days for trend
            threshold: Low stock threshold
        
        Returns:
            Cached dashboard stats or None if not cached
        """
        cache_key = generate_cache_key(
            CacheService.DASHBOARD_STATS_PREFIX,
            start_date=start_date,
            end_date=end_date,
            days=days,
            threshold=threshold
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_dashboard_stats_cache(
        data: Dict,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 7,
        threshold: int = 10
    ) -> None:
        """
        Cache dashboard statistics.
        
        Args:
            data: Dashboard stats data to cache
            start_date: Start date filter used
            end_date: End date filter used
            days: Number of days for trend
            threshold: Low stock threshold used
        """
        cache_key = generate_cache_key(
            CacheService.DASHBOARD_STATS_PREFIX,
            start_date=start_date,
            end_date=end_date,
            days=days,
            threshold=threshold
        )
        timeout = get_cache_timeout('dashboard_stats')
        cache.set(cache_key, data, timeout)
        logger.debug("Cached dashboard statistics")
    
    @staticmethod
    def invalidate_dashboard_cache() -> None:
        """
        Invalidate all dashboard caches.
        This should be called when orders, payments, or inventory changes.
        """
        # Use version key approach for dashboard
        cache.delete('dashboard_version')
        logger.info("Invalidated dashboard cache")
    
    @staticmethod
    def get_active_tax_config_cache() -> Optional[Dict]:
        """
        Get cached active tax configuration.
        
        Returns:
            Cached tax config or None if not cached
        """
        cache_key = f"{CacheService.TAX_CONFIG_PREFIX}:active"
        return cache.get(cache_key)
    
    @staticmethod
    def set_active_tax_config_cache(data: Dict) -> None:
        """
        Cache active tax configuration.
        
        Args:
            data: Tax configuration data to cache
        """
        cache_key = f"{CacheService.TAX_CONFIG_PREFIX}:active"
        timeout = get_cache_timeout('tax_config')
        cache.set(cache_key, data, timeout)
        logger.debug("Cached active tax configuration")
    
    @staticmethod
    def get_tax_config_by_date_cache(date: datetime) -> Optional[Dict]:
        """
        Get cached tax configuration for a specific date.
        
        Args:
            date: Date to get tax config for
        
        Returns:
            Cached tax config or None if not cached
        """
        cache_key = generate_cache_key(
            CacheService.TAX_CONFIG_PREFIX,
            date=date.strftime('%Y-%m-%d')
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_tax_config_by_date_cache(date: datetime, data: Dict) -> None:
        """
        Cache tax configuration for a specific date.
        
        Args:
            date: Date the tax config applies to
            data: Tax configuration data to cache
        """
        cache_key = generate_cache_key(
            CacheService.TAX_CONFIG_PREFIX,
            date=date.strftime('%Y-%m-%d')
        )
        timeout = get_cache_timeout('tax_config')
        cache.set(cache_key, data, timeout)
        logger.debug(f"Cached tax configuration for date {date}")
    
    @staticmethod
    def invalidate_tax_config_cache() -> None:
        """
        Invalidate all tax configuration caches.
        This should be called when tax configuration is updated.
        """
        cache.delete(f"{CacheService.TAX_CONFIG_PREFIX}:active")
        # Use version key for date-specific configs
        cache.delete('tax_config_version')
        logger.info("Invalidated tax configuration cache")
    
    @staticmethod
    def get_inventory_cache(material_id: Optional[int] = None) -> Optional[Any]:
        """
        Get cached inventory data.
        
        Args:
            material_id: Specific material ID or None for all inventory
        
        Returns:
            Cached inventory data or None if not cached
        """
        cache_key = generate_cache_key(
            CacheService.INVENTORY_PREFIX,
            material_id=material_id
        )
        return cache.get(cache_key)
    
    @staticmethod
    def set_inventory_cache(data: Any, material_id: Optional[int] = None) -> None:
        """
        Cache inventory data.
        
        Args:
            data: Inventory data to cache
            material_id: Specific material ID or None for all inventory
        """
        cache_key = generate_cache_key(
            CacheService.INVENTORY_PREFIX,
            material_id=material_id
        )
        timeout = get_cache_timeout('inventory')
        cache.set(cache_key, data, timeout)
        logger.debug(f"Cached inventory data")
    
    @staticmethod
    def invalidate_inventory_cache(material_id: Optional[int] = None) -> None:
        """
        Invalidate inventory caches.
        
        Args:
            material_id: Specific material ID to invalidate, or None for all
        """
        if material_id:
            cache_key = generate_cache_key(
                CacheService.INVENTORY_PREFIX,
                material_id=material_id
            )
            cache.delete(cache_key)
            logger.info(f"Invalidated cache for material ID {material_id}")
        
        # Invalidate general inventory cache
        cache.delete('inventory_version')
        logger.info("Invalidated inventory cache")
    
    @staticmethod
    def clear_all_caches() -> None:
        """
        Clear all application caches.
        Use with caution - typically only for maintenance or testing.
        """
        cache.clear()
        logger.warning("Cleared all application caches")


# Convenience functions for common cache operations

def cache_product_list(filters: Optional[Dict] = None):
    """
    Decorator to cache product list results.
    
    Usage:
        @cache_product_list(filters={'fabric': 'cotton'})
        def get_products():
            return Product.objects.all()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_data = CacheService.get_product_list_cache(filters)
            if cached_data is not None:
                return cached_data
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheService.set_product_list_cache(result, filters)
            return result
        return wrapper
    return decorator


def cache_product_detail(product_id: int):
    """
    Decorator to cache product detail results.
    
    Usage:
        @cache_product_detail(product_id=1)
        def get_product_detail():
            return Product.objects.get(id=1)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_data = CacheService.get_product_detail_cache(product_id)
            if cached_data is not None:
                return cached_data
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheService.set_product_detail_cache(product_id, result)
            return result
        return wrapper
    return decorator


def invalidate_on_change(cache_type: str):
    """
    Decorator to invalidate cache after a function executes.
    
    Args:
        cache_type: Type of cache to invalidate ('product', 'dashboard', 'tax', 'inventory')
    
    Usage:
        @invalidate_on_change('product')
        def update_product(product_id, data):
            # Update product logic
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate appropriate cache
            if cache_type == 'product':
                CacheService.invalidate_product_cache()
            elif cache_type == 'dashboard':
                CacheService.invalidate_dashboard_cache()
            elif cache_type == 'tax':
                CacheService.invalidate_tax_config_cache()
            elif cache_type == 'inventory':
                CacheService.invalidate_inventory_cache()
            
            return result
        return wrapper
    return decorator
