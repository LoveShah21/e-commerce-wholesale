"""
Tests for admin order management views.

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 10.5
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.orders.models import Order, OrderItem, Cart, CartItem
from apps.products.models import (
    Product, ProductVariant, VariantSize, Size, Stock,
    Fabric, Color, Pattern, Sleeve, Pocket
)
from apps.users.models import Address, Country, State, City, PostalCode
from apps.finance.models import Payment, TaxConfiguration
from apps.manufacturing.models import (
    RawMaterial, MaterialType, ManufacturingSpecification
)

User = get_user_model()


class AdminOrderViewsTestCase(TestCase):
    """Test admin order management views"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            user_type='admin'
        )
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123',
            full_name='Customer User',
            user_type='customer'
        )
        
        # Create address components
        self.country = Country.objects.create(country_name='India', country_code='IN')
        self.state = State.objects.create(state_name='Maharashtra', state_code='MH', country=self.country)
        self.city = City.objects.create(city_name='Mumbai', state=self.state)
        self.postal_code = PostalCode.objects.create(postal_code='400001', city=self.city)
        
        # Create delivery address
        self.address = Address.objects.create(
            user=self.customer_user,
            address_line1='123 Test St',
            postal_code=self.postal_code
        )
        
        # Create product attributes
        self.fabric = Fabric.objects.create(fabric_name='Cotton')
        self.color = Color.objects.create(color_name='Blue', hex_code='#0000FF')
        self.pattern = Pattern.objects.create(pattern_name='Solid')
        self.sleeve = Sleeve.objects.create(sleeve_type='Full Sleeve')
        self.pocket = Pocket.objects.create(pocket_type='Single Pocket')
        self.size = Size.objects.create(size_code='M', size_name='Medium', size_markup_percentage=Decimal('0.00'))
        
        # Create product
        self.product = Product.objects.create(
            product_name='Test Shirt',
            description='A test shirt'
        )
        
        # Create variant
        self.variant = ProductVariant.objects.create(
            product=self.product,
            fabric=self.fabric,
            color=self.color,
            pattern=self.pattern,
            sleeve=self.sleeve,
            pocket=self.pocket,
            base_price=Decimal('500.00'),
            sku='TEST-SHIRT-001'
        )
        
        # Create variant size
        self.variant_size = VariantSize.objects.create(
            variant=self.variant,
            size=self.size
        )
        
        # Create stock
        self.stock = Stock.objects.create(
            variant_size=self.variant_size,
            quantity_in_stock=100,
            quantity_reserved=0
        )
        
        # Create order
        self.order = Order.objects.create(
            user=self.customer_user,
            delivery_address=self.address,
            status='pending'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            variant_size=self.variant_size,
            quantity=2,
            snapshot_unit_price=Decimal('500.00')
        )
        
        # Create tax configuration
        self.tax_config = TaxConfiguration.objects.create(
            tax_name='GST',
            tax_percentage=Decimal('18.00'),
            effective_from='2024-01-01',
            is_active=True
        )
        
        # Create material type and raw material for testing
        self.material_type = MaterialType.objects.create(
            material_type_name='Fabric',
            unit_of_measurement='meters'
        )
        
        self.raw_material = RawMaterial.objects.create(
            material_name='Cotton Fabric',
            material_type=self.material_type,
            unit_price=Decimal('50.00'),
            current_quantity=Decimal('1000.00')
        )
        
        # Create manufacturing specification
        self.spec = ManufacturingSpecification.objects.create(
            variant_size=self.variant_size,
            material=self.raw_material,
            quantity_required=Decimal('2.5')
        )
        
        self.client = Client()
    
    def test_admin_order_list_view_requires_admin(self):
        """Test that order list view requires admin access"""
        # Try to access without login
        response = self.client.get(reverse('admin-order-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Try to access as customer
        self.client.login(email='customer@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-list'))
        self.assertEqual(response.status_code, 302)  # Redirect with error
        
        # Access as admin should work
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-list'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_order_list_view_displays_orders(self):
        """Test that order list view displays orders"""
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Orders')
        self.assertContains(response, self.customer_user.full_name)
        self.assertContains(response, f'#{self.order.id}')
    
    def test_admin_order_list_view_filters_by_status(self):
        """Test that order list view filters by status"""
        # Create another order with different status
        order2 = Order.objects.create(
            user=self.customer_user,
            delivery_address=self.address,
            status='confirmed'
        )
        
        self.client.login(email='admin@test.com', password='testpass123')
        
        # Filter by pending status
        response = self.client.get(reverse('admin-order-list') + '?status=pending')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'#{self.order.id}')
        self.assertNotContains(response, f'#{order2.id}')
        
        # Filter by confirmed status
        response = self.client.get(reverse('admin-order-list') + '?status=confirmed')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f'#{self.order.id}')
        self.assertContains(response, f'#{order2.id}')
    
    def test_admin_order_detail_view_displays_order_info(self):
        """Test that order detail view displays order information"""
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-detail', args=[self.order.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Order #{self.order.id}')
        self.assertContains(response, self.customer_user.full_name)
        self.assertContains(response, self.product.product_name)
        self.assertContains(response, 'Order Items')
        self.assertContains(response, 'Payment Status')
    
    def test_admin_order_detail_view_displays_material_requirements(self):
        """Test that order detail view displays material requirements"""
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-detail', args=[self.order.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Material Requirements')
        self.assertContains(response, self.raw_material.material_name)
    
    def test_admin_order_detail_view_update_status(self):
        """Test that order status can be updated"""
        self.client.login(email='admin@test.com', password='testpass123')
        
        # Update status to confirmed
        response = self.client.post(
            reverse('admin-order-detail', args=[self.order.id]),
            {
                'action': 'update_status',
                'status': 'confirmed',
                'notes': 'Test update'
            }
        )
        
        # Should redirect back to detail page
        self.assertEqual(response.status_code, 302)
        
        # Check that status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
    
    def test_admin_material_requirements_view(self):
        """Test that material requirements view displays correctly"""
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-materials', args=[self.order.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Material Requirements')
        self.assertContains(response, self.raw_material.material_name)
        self.assertContains(response, 'Required Quantity')
        self.assertContains(response, 'Available Quantity')
    
    def test_admin_order_list_pagination(self):
        """Test that order list pagination works"""
        # Create 25 orders to test pagination (20 per page)
        for i in range(25):
            Order.objects.create(
                user=self.customer_user,
                delivery_address=self.address,
                status='pending'
            )
        
        self.client.login(email='admin@test.com', password='testpass123')
        
        # First page should have 20 orders
        response = self.client.get(reverse('admin-order-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['orders']), 20)
        
        # Second page should have remaining orders
        response = self.client.get(reverse('admin-order-list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context['orders']), 0)
    
    def test_admin_order_payment_status_display(self):
        """Test that payment status is displayed correctly"""
        # Create advance payment
        Payment.objects.create(
            order=self.order,
            amount=Decimal('590.00'),  # 50% of total with tax
            payment_type='advance',
            payment_method='upi',
            payment_status='success'
        )
        
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-detail', args=[self.order.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advance Payment')
        self.assertContains(response, 'Paid')


class AdminOrderFilterTestCase(TestCase):
    """Test admin order filtering functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            user_type='admin'
        )
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123',
            full_name='Test Customer',
            user_type='customer'
        )
        
        # Create minimal required data
        self.country = Country.objects.create(country_name='India', country_code='IN')
        self.state = State.objects.create(state_name='Maharashtra', state_code='MH', country=self.country)
        self.city = City.objects.create(city_name='Mumbai', state=self.state)
        self.postal_code = PostalCode.objects.create(postal_code='400001', city=self.city)
        
        self.address = Address.objects.create(
            user=self.customer_user,
            address_line1='123 Test St',
            postal_code=self.postal_code
        )
        
        self.client = Client()
    
    def test_search_by_order_id(self):
        """Test searching orders by order ID"""
        order1 = Order.objects.create(
            user=self.customer_user,
            delivery_address=self.address,
            status='pending'
        )
        order2 = Order.objects.create(
            user=self.customer_user,
            delivery_address=self.address,
            status='pending'
        )
        
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin-order-list') + f'?search={order1.id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'#{order1.id}')
        self.assertNotContains(response, f'#{order2.id}')
    
    def test_search_by_customer_name(self):
        """Test searching orders by customer name"""
        self.client.login(email='admin@test.com', password='testpass123')
        
        order = Order.objects.create(
            user=self.customer_user,
            delivery_address=self.address,
            status='pending'
        )
        
        response = self.client.get(reverse('admin-order-list') + '?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Customer')
