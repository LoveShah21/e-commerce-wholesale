"""
Property-based tests for dashboard analytics.

These tests verify universal properties that should hold across all inputs.
"""
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid
from apps.orders.models import Order, OrderItem
from apps.finance.models import Payment
from apps.products.models import (
    Product, ProductVariant, VariantSize, Stock, Size,
    Fabric, Color, Pattern, Sleeve, Pocket
)
from apps.users.models import Address, Country, State, City, PostalCode

User = get_user_model()


class DashboardPropertiesTest(TestCase):
    """Property-based tests for dashboard analytics."""
    
    def setUp(self):
        """Set up test data that's needed for all tests."""
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Create admin user
        self.admin = User.objects.create_user(
            username=f'admin_{unique_id}',
            email=f'admin_{unique_id}@test.com',
            password='testpass123',
            full_name='Admin User',
            user_type='admin'
        )
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()
        
        # Create customer user
        self.customer = User.objects.create_user(
            username=f'customer_{unique_id}',
            email=f'customer_{unique_id}@test.com',
            password='testpass123',
            full_name='Customer User',
            user_type='customer'
        )
        
        # Create address components
        self.country = Country.objects.create(country_name=f'Country_{unique_id}', country_code=f'C{unique_id[:1]}')
        self.state = State.objects.create(state_name=f'State_{unique_id}', state_code=f'S{unique_id[:2]}', country=self.country)
        self.city = City.objects.create(city_name=f'City_{unique_id}', state=self.state)
        self.postal_code = PostalCode.objects.create(postal_code=f'{unique_id[:6]}', city=self.city)
        
        # Create delivery address
        self.address = Address.objects.create(
            user=self.customer,
            address_line1='123 Test St',
            postal_code=self.postal_code,
            is_default=True
        )
        
        # Create product attributes
        self.fabric = Fabric.objects.create(fabric_name=f'Fabric_{unique_id}')
        self.color = Color.objects.create(color_name=f'Color_{unique_id}', hex_code='#0000FF')
        self.pattern = Pattern.objects.create(pattern_name=f'Pattern_{unique_id}')
        self.sleeve = Sleeve.objects.create(sleeve_type=f'Sleeve_{unique_id}')
        self.pocket = Pocket.objects.create(pocket_type=f'Pocket_{unique_id}')
        self.size = Size.objects.create(size_code=f'S{unique_id[:3]}', size_name='Medium')
        
        # Create product
        self.product = Product.objects.create(
            product_name=f'Test Shirt {unique_id}',
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
            sku=f'TEST-SHIRT-{unique_id}'
        )
        
        # Create variant size
        self.variant_size = VariantSize.objects.create(
            variant=self.variant,
            size=self.size,
            stock_quantity=100
        )
        
        # Create stock
        self.stock = Stock.objects.create(
            variant_size=self.variant_size,
            quantity_in_stock=100,
            quantity_reserved=0
        )
    
    @given(
        num_orders=st.integers(min_value=0, max_value=20),
        num_successful_payments=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_32_dashboard_metrics_are_accurate(self, num_orders, num_successful_payments):
        """
        Feature: complete-ecommerce-platform, Property 32: Dashboard metrics are accurate
        
        For any dashboard request, total_sales should equal the sum of all successful payments,
        and total_orders should equal the count of all orders.
        
        Validates: Requirements 9.1
        """
        # Clear existing data
        Payment.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        
        # Create orders
        orders = []
        for i in range(num_orders):
            order = Order.objects.create(
                user=self.customer,
                delivery_address=self.address,
                status='pending'
            )
            orders.append(order)
            
            # Create order item (this will trigger stock reservation via signal)
            OrderItem.objects.create(
                order=order,
                variant_size=self.variant_size,
                quantity=1,
                snapshot_unit_price=Decimal('500.00')
            )
        
        # Create successful payments with varying amounts
        expected_total_sales = Decimal('0.00')
        for i in range(num_successful_payments):
            if orders:  # Only create payments if we have orders
                order = orders[i % len(orders)] if orders else orders[0]
                amount = Decimal(str(100.00 + i * 50.00))
                Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_type='advance',
                    payment_method='upi',
                    payment_status='success'
                )
                expected_total_sales += amount
            else:
                # If no orders, we can't create payments (FK constraint)
                break
        
        # Import the view and make request
        from apps.dashboard.views import DashboardStatsView
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/api/dashboard/stats/')
        request.user = self.admin
        
        view = DashboardStatsView.as_view()
        response = view(request)
        
        # Check if response has error
        if response.status_code != 200:
            self.fail(f"Dashboard API returned error: {response.status_code} - {response.data}")
        
        # Verify property: total_sales equals sum of successful payments
        actual_total_sales = Decimal(str(response.data['total_sales']))
        self.assertEqual(
            actual_total_sales,
            expected_total_sales,
            f"Total sales should equal sum of successful payments. "
            f"Expected: {expected_total_sales}, Got: {actual_total_sales}"
        )
        
        # Verify property: total_orders equals count of all orders
        actual_total_orders = response.data['total_orders']
        self.assertEqual(
            actual_total_orders,
            num_orders,
            f"Total orders should equal count of all orders. "
            f"Expected: {num_orders}, Got: {actual_total_orders}"
        )

    @given(
        days=st.integers(min_value=1, max_value=30)
    )
    @settings(max_examples=10, deadline=None)
    def test_property_33_sales_trend_covers_correct_period(self, days):
        """
        Feature: complete-ecommerce-platform, Property 33: Sales trend covers correct period
        
        For any sales trend request for N days, the response should contain exactly N data points,
        one for each day.
        
        Validates: Requirements 9.2
        """
        # Import the view and make request
        from apps.dashboard.views import DashboardStatsView
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/dashboard/stats/?days={days}')
        request.user = self.admin
        
        view = DashboardStatsView.as_view()
        response = view(request)
        
        # Check if response has error
        if response.status_code != 200:
            self.fail(f"Dashboard API returned error: {response.status_code} - {response.data}")
        
        # Verify property: sales_trend contains exactly N data points
        sales_trend = response.data['sales_trend']
        self.assertEqual(
            len(sales_trend),
            days,
            f"Sales trend should contain exactly {days} data points. "
            f"Got: {len(sales_trend)}"
        )
        
        # Verify each data point has required fields
        for i, data_point in enumerate(sales_trend):
            self.assertIn('date', data_point, f"Data point {i} should have 'date' field")
            self.assertIn('sales', data_point, f"Data point {i} should have 'sales' field")
        
        # Verify dates are consecutive and in correct order
        if days > 1:
            from datetime import datetime
            for i in range(len(sales_trend) - 1):
                current_date = datetime.strptime(sales_trend[i]['date'], '%Y-%m-%d').date()
                next_date = datetime.strptime(sales_trend[i + 1]['date'], '%Y-%m-%d').date()
                expected_next_date = current_date + timedelta(days=1)
                self.assertEqual(
                    next_date,
                    expected_next_date,
                    f"Dates should be consecutive. Date at index {i}: {current_date}, "
                    f"Date at index {i+1}: {next_date}, Expected: {expected_next_date}"
                )
