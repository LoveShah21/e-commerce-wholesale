"""
Integration tests for caching functionality

Tests the caching implementation across different components.
"""

from django.test import TestCase
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.products.models import Product, ProductVariant, Fabric, Color, Pattern, Sleeve, Pocket
from apps.finance.models import TaxConfiguration
from services.cache_service import CacheService
from datetime import datetime, timedelta

User = get_user_model()


class CacheIntegrationTestCase(TestCase):
    """Integration tests for caching"""
    
    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            user_type='admin'
        )
        
        # Create product attributes
        self.fabric = Fabric.objects.create(fabric_name='Cotton')
        self.color = Color.objects.create(color_name='Blue')
        self.pattern = Pattern.objects.create(pattern_name='Solid')
        self.sleeve = Sleeve.objects.create(sleeve_type='Full')
        self.pocket = Pocket.objects.create(pocket_type='Single')
        
        # Create test product
        self.product = Product.objects.create(
            product_name='Test Shirt',
            description='A test shirt'
        )
        
        # Create tax configuration
        self.tax_config = TaxConfiguration.objects.create(
            tax_name='GST',
            tax_percentage=18.0,
            effective_from=datetime.now().date() - timedelta(days=30),
            is_active=True
        )
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
    
    def test_product_cache_lifecycle(self):
        """Test complete product cache lifecycle"""
        # Initially, cache should be empty
        cached = CacheService.get_product_detail_cache(self.product.id)
        self.assertIsNone(cached)
        
        # Simulate caching product data
        product_data = {
            'id': self.product.id,
            'product_name': self.product.product_name,
            'description': self.product.description
        }
        CacheService.set_product_detail_cache(self.product.id, product_data)
        
        # Verify cache hit
        cached = CacheService.get_product_detail_cache(self.product.id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['product_name'], 'Test Shirt')
        
        # Update product (should invalidate cache)
        self.product.product_name = 'Updated Shirt'
        self.product.save()
        CacheService.invalidate_product_cache(self.product.id)
        
        # Cache should be cleared
        cached = CacheService.get_product_detail_cache(self.product.id)
        self.assertIsNone(cached)
    
    def test_tax_config_cache_with_real_data(self):
        """Test tax configuration caching with real database data"""
        from services.invoice_service import InvoiceService
        
        # First call should hit database and cache result
        tax_config = InvoiceService.get_active_tax_config()
        self.assertIsNotNone(tax_config)
        self.assertEqual(tax_config.tax_name, 'GST')
        self.assertEqual(float(tax_config.tax_percentage), 18.0)
        
        # Verify it's cached
        cached = CacheService.get_active_tax_config_cache()
        self.assertIsNotNone(cached)
        self.assertEqual(cached['tax_name'], 'GST')
        
        # Second call should hit cache
        tax_config_2 = InvoiceService.get_active_tax_config()
        self.assertEqual(tax_config_2.tax_name, 'GST')
    
    def test_cache_invalidation_on_model_changes(self):
        """Test that cache is properly invalidated when models change"""
        # Cache product data
        product_data = {'id': self.product.id, 'name': 'Test'}
        CacheService.set_product_detail_cache(self.product.id, product_data)
        
        # Verify cached
        self.assertIsNotNone(CacheService.get_product_detail_cache(self.product.id))
        
        # Simulate product update
        CacheService.invalidate_product_cache(self.product.id)
        
        # Cache should be cleared
        self.assertIsNone(CacheService.get_product_detail_cache(self.product.id))
    
    def test_multiple_cache_types_coexist(self):
        """Test that different cache types don't interfere with each other"""
        # Set multiple cache types
        product_data = {'id': 1, 'name': 'Product'}
        dashboard_data = {'total_sales': 1000}
        tax_data = {'tax_name': 'GST', 'tax_percentage': 18.0}
        
        CacheService.set_product_detail_cache(1, product_data)
        CacheService.set_dashboard_stats_cache(dashboard_data)
        CacheService.set_active_tax_config_cache(tax_data)
        
        # All should be retrievable
        self.assertIsNotNone(CacheService.get_product_detail_cache(1))
        self.assertIsNotNone(CacheService.get_dashboard_stats_cache())
        self.assertIsNotNone(CacheService.get_active_tax_config_cache())
        
        # Invalidate one type
        CacheService.invalidate_product_cache(1)
        
        # Only product cache should be cleared
        self.assertIsNone(CacheService.get_product_detail_cache(1))
        self.assertIsNotNone(CacheService.get_dashboard_stats_cache())
        self.assertIsNotNone(CacheService.get_active_tax_config_cache())
    
    def test_cache_with_filters(self):
        """Test caching with different filter combinations"""
        filters_1 = {'fabric': 'cotton', 'color': 'blue'}
        filters_2 = {'fabric': 'silk', 'color': 'red'}
        
        data_1 = [{'id': 1, 'name': 'Product 1'}]
        data_2 = [{'id': 2, 'name': 'Product 2'}]
        
        # Cache with different filters
        CacheService.set_product_list_cache(data_1, filters_1)
        CacheService.set_product_list_cache(data_2, filters_2)
        
        # Both should be retrievable independently
        cached_1 = CacheService.get_product_list_cache(filters_1)
        cached_2 = CacheService.get_product_list_cache(filters_2)
        
        self.assertEqual(cached_1, data_1)
        self.assertEqual(cached_2, data_2)
        
        # Different filters should return None
        cached_3 = CacheService.get_product_list_cache({'fabric': 'linen'})
        self.assertIsNone(cached_3)
