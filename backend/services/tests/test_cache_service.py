"""
Unit tests for Cache Service

Tests the caching functionality for products, dashboard, tax configuration, and inventory.
"""

import unittest
from django.test import TestCase
from django.core.cache import cache
from datetime import datetime
from decimal import Decimal
from services.cache_service import CacheService


class CacheServiceTestCase(TestCase):
    """Test cases for CacheService"""
    
    def setUp(self):
        """Clear cache before each test"""
        cache.clear()
    
    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()
    
    def test_product_list_cache(self):
        """Test product list caching"""
        # Test data
        filters = {'fabric': 'cotton', 'color': 'blue'}
        product_data = [
            {'id': 1, 'name': 'Product 1'},
            {'id': 2, 'name': 'Product 2'}
        ]
        
        # Initially, cache should be empty
        cached = CacheService.get_product_list_cache(filters)
        self.assertIsNone(cached)
        
        # Set cache
        CacheService.set_product_list_cache(product_data, filters)
        
        # Retrieve from cache
        cached = CacheService.get_product_list_cache(filters)
        self.assertIsNotNone(cached)
        self.assertEqual(cached, product_data)
        
        # Different filters should return None
        different_filters = {'fabric': 'silk'}
        cached = CacheService.get_product_list_cache(different_filters)
        self.assertIsNone(cached)
    
    def test_product_detail_cache(self):
        """Test product detail caching"""
        product_id = 1
        product_data = {
            'id': 1,
            'name': 'Test Product',
            'description': 'Test Description'
        }
        
        # Initially, cache should be empty
        cached = CacheService.get_product_detail_cache(product_id)
        self.assertIsNone(cached)
        
        # Set cache
        CacheService.set_product_detail_cache(product_id, product_data)
        
        # Retrieve from cache
        cached = CacheService.get_product_detail_cache(product_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached, product_data)
        
        # Different product ID should return None
        cached = CacheService.get_product_detail_cache(999)
        self.assertIsNone(cached)
    
    def test_product_cache_invalidation(self):
        """Test product cache invalidation"""
        product_id = 1
        product_data = {'id': 1, 'name': 'Test Product'}
        
        # Set cache
        CacheService.set_product_detail_cache(product_id, product_data)
        
        # Verify cache exists
        cached = CacheService.get_product_detail_cache(product_id)
        self.assertIsNotNone(cached)
        
        # Invalidate cache
        CacheService.invalidate_product_cache(product_id)
        
        # Cache should be cleared
        cached = CacheService.get_product_detail_cache(product_id)
        self.assertIsNone(cached)
    
    def test_dashboard_stats_cache(self):
        """Test dashboard statistics caching"""
        stats_data = {
            'total_sales': 10000.00,
            'total_orders': 50,
            'pending_orders': 5
        }
        
        # Initially, cache should be empty
        cached = CacheService.get_dashboard_stats_cache()
        self.assertIsNone(cached)
        
        # Set cache
        CacheService.set_dashboard_stats_cache(stats_data)
        
        # Retrieve from cache
        cached = CacheService.get_dashboard_stats_cache()
        self.assertIsNotNone(cached)
        self.assertEqual(cached, stats_data)
    
    def test_dashboard_cache_with_parameters(self):
        """Test dashboard caching with different parameters"""
        stats_data_1 = {'total_sales': 10000.00}
        stats_data_2 = {'total_sales': 15000.00}
        
        # Set cache with different parameters
        CacheService.set_dashboard_stats_cache(
            stats_data_1,
            start_date='2024-01-01',
            end_date='2024-01-31'
        )
        CacheService.set_dashboard_stats_cache(
            stats_data_2,
            start_date='2024-02-01',
            end_date='2024-02-28'
        )
        
        # Retrieve with matching parameters
        cached_1 = CacheService.get_dashboard_stats_cache(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )
        cached_2 = CacheService.get_dashboard_stats_cache(
            start_date='2024-02-01',
            end_date='2024-02-28'
        )
        
        self.assertEqual(cached_1, stats_data_1)
        self.assertEqual(cached_2, stats_data_2)
    
    def test_tax_config_cache(self):
        """Test tax configuration caching"""
        tax_data = {
            'id': 1,
            'tax_name': 'GST',
            'tax_percentage': 18.0,
            'effective_from': datetime.now().date(),
            'is_active': True
        }
        
        # Initially, cache should be empty
        cached = CacheService.get_active_tax_config_cache()
        self.assertIsNone(cached)
        
        # Set cache
        CacheService.set_active_tax_config_cache(tax_data)
        
        # Retrieve from cache
        cached = CacheService.get_active_tax_config_cache()
        self.assertIsNotNone(cached)
        self.assertEqual(cached['tax_name'], 'GST')
        self.assertEqual(cached['tax_percentage'], 18.0)
    
    def test_tax_config_by_date_cache(self):
        """Test tax configuration caching by date"""
        date = datetime(2024, 1, 1)
        tax_data = {
            'id': 1,
            'tax_name': 'GST',
            'tax_percentage': 18.0,
            'effective_from': date.date(),
            'is_active': True
        }
        
        # Set cache
        CacheService.set_tax_config_by_date_cache(date, tax_data)
        
        # Retrieve from cache
        cached = CacheService.get_tax_config_by_date_cache(date)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['tax_name'], 'GST')
    
    def test_tax_config_cache_invalidation(self):
        """Test tax configuration cache invalidation"""
        tax_data = {
            'id': 1,
            'tax_name': 'GST',
            'tax_percentage': 18.0
        }
        
        # Set cache
        CacheService.set_active_tax_config_cache(tax_data)
        
        # Verify cache exists
        cached = CacheService.get_active_tax_config_cache()
        self.assertIsNotNone(cached)
        
        # Invalidate cache
        CacheService.invalidate_tax_config_cache()
        
        # Cache should be cleared
        cached = CacheService.get_active_tax_config_cache()
        self.assertIsNone(cached)
    
    def test_inventory_cache(self):
        """Test inventory caching"""
        material_id = 1
        inventory_data = {
            'id': 1,
            'name': 'Cotton Fabric',
            'quantity': 1000,
            'reorder_level': 100
        }
        
        # Initially, cache should be empty
        cached = CacheService.get_inventory_cache(material_id)
        self.assertIsNone(cached)
        
        # Set cache
        CacheService.set_inventory_cache(inventory_data, material_id)
        
        # Retrieve from cache
        cached = CacheService.get_inventory_cache(material_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached, inventory_data)
    
    def test_inventory_cache_invalidation(self):
        """Test inventory cache invalidation"""
        material_id = 1
        inventory_data = {'id': 1, 'quantity': 1000}
        
        # Set cache
        CacheService.set_inventory_cache(inventory_data, material_id)
        
        # Verify cache exists
        cached = CacheService.get_inventory_cache(material_id)
        self.assertIsNotNone(cached)
        
        # Invalidate cache
        CacheService.invalidate_inventory_cache(material_id)
        
        # Cache should be cleared
        cached = CacheService.get_inventory_cache(material_id)
        self.assertIsNone(cached)
    
    def test_clear_all_caches(self):
        """Test clearing all caches"""
        # Set multiple caches
        CacheService.set_product_detail_cache(1, {'id': 1})
        CacheService.set_dashboard_stats_cache({'total_sales': 1000})
        CacheService.set_active_tax_config_cache({'tax_name': 'GST'})
        CacheService.set_inventory_cache({'quantity': 100}, 1)
        
        # Verify caches exist
        self.assertIsNotNone(CacheService.get_product_detail_cache(1))
        self.assertIsNotNone(CacheService.get_dashboard_stats_cache())
        self.assertIsNotNone(CacheService.get_active_tax_config_cache())
        self.assertIsNotNone(CacheService.get_inventory_cache(1))
        
        # Clear all caches
        CacheService.clear_all_caches()
        
        # All caches should be cleared
        self.assertIsNone(CacheService.get_product_detail_cache(1))
        self.assertIsNone(CacheService.get_dashboard_stats_cache())
        self.assertIsNone(CacheService.get_active_tax_config_cache())
        self.assertIsNone(CacheService.get_inventory_cache(1))
    
    def test_cache_with_none_filters(self):
        """Test caching with None filters"""
        product_data = [{'id': 1, 'name': 'Product 1'}]
        
        # Set cache with None filters
        CacheService.set_product_list_cache(product_data, None)
        
        # Retrieve with None filters
        cached = CacheService.get_product_list_cache(None)
        self.assertIsNotNone(cached)
        self.assertEqual(cached, product_data)
        
        # Retrieve with empty dict should return the same (both treated as no filters)
        cached = CacheService.get_product_list_cache({})
        self.assertIsNotNone(cached)  # Same as None since both mean "no filters"
        self.assertEqual(cached, product_data)


if __name__ == '__main__':
    unittest.main()
