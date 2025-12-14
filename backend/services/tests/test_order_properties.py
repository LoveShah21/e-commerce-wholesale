"""
Property-Based Tests for Order Service

Tests correctness properties for order operations using Hypothesis.
Feature: complete-ecommerce-platform
"""

from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import uuid

from apps.orders.models import Cart, CartItem, Order, OrderItem
from apps.products.models import (
    Product, ProductVariant, VariantSize, Size, Stock,
    Fabric, Color, Pattern, Sleeve, Pocket
)
from apps.users.models import Address, Country, State, City, PostalCode
from services.order_service import OrderService
from services.cart_service import CartService


User = get_user_model()


def create_test_variant_size(stock_quantity, base_price=Decimal('500.00')):
    """Helper to create a VariantSize with Stock for testing"""
    unique_id = uuid.uuid4().hex[:6]
    
    fabric = Fabric.objects.create(fabric_name=f"Fabric_{unique_id}")
    color = Color.objects.create(color_name=f"Color_{unique_id}")
    pattern = Pattern.objects.create(pattern_name=f"Pattern_{unique_id}")
    sleeve = Sleeve.objects.create(sleeve_type=f"Sleeve_{unique_id}")
    pocket = Pocket.objects.create(pocket_type=f"Pocket_{unique_id}")
    size = Size.objects.create(
        size_code=f"S{unique_id}",
        size_name='Medium',
        size_markup_percentage=Decimal('10.00')
    )
    
    product = Product.objects.create(
        product_name=f"Product_{unique_id}",
        description='Test product'
    )
    
    variant = ProductVariant.objects.create(
        product=product,
        fabric=fabric,
        color=color,
        pattern=pattern,
        sleeve=sleeve,
        pocket=pocket,
        base_price=base_price
    )
    
    variant_size = VariantSize.objects.create(
        variant=variant,
        size=size,
        stock_quantity=stock_quantity
    )
    
    Stock.objects.create(
        variant_size=variant_size,
        quantity_in_stock=stock_quantity,
        quantity_reserved=0
    )
    
    return variant_size


def create_test_address(user):
    """Helper to create an Address for testing"""
    unique_id = uuid.uuid4().hex[:6]
    
    country = Country.objects.create(country_name=f"Country_{unique_id}")
    state = State.objects.create(
        country=country,
        state_name=f"State_{unique_id}"
    )
    city = City.objects.create(
        state=state,
        city_name=f"City_{unique_id}"
    )
    postal_code = PostalCode.objects.create(
        city=city,
        postal_code=f"12345{unique_id[:1]}"
    )
    
    address = Address.objects.create(
        user=user,
        address_line1=f"123 Test St {unique_id}",
        postal_code=postal_code,
        address_type='home'
    )
    
    return address


def cleanup_variant_size(variant_size):
    """Helper to cleanup test data"""
    product = variant_size.variant.product
    fabric = variant_size.variant.fabric
    color = variant_size.variant.color
    pattern = variant_size.variant.pattern
    sleeve = variant_size.variant.sleeve
    pocket = variant_size.variant.pocket
    size = variant_size.size
    
    product.delete()
    fabric.delete()
    color.delete()
    pattern.delete()
    sleeve.delete()
    pocket.delete()
    size.delete()


def cleanup_address(address):
    """Helper to cleanup address test data"""
    postal_code = address.postal_code
    city = postal_code.city
    state = city.state
    country = state.country
    
    address.delete()
    postal_code.delete()
    city.delete()
    state.delete()
    country.delete()


class TestStockReservation(TestCase):
    """
    Property 15: Order creation reserves stock atomically
    
    Feature: complete-ecommerce-platform, Property 15: Order creation reserves stock atomically
    Validates: Requirements 5.3
    
    For any order created from a cart, the stock quantity_reserved should
    increase by the order quantity for all items, and this should happen
    atomically (all or nothing).
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_items=st.integers(min_value=1, max_value=3),
        quantities=st.lists(st.integers(min_value=1, max_value=5), min_size=1, max_size=3)
    )
    def test_order_creation_reserves_stock_atomically(self, num_items, quantities):
        """
        For any order created from a cart, stock should be reserved atomically
        for all items.
        """
        # Ensure we have matching quantities for items
        quantities = quantities[:num_items]
        if len(quantities) < num_items:
            quantities.extend([1] * (num_items - len(quantities)))
        
        # Create test user
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Create address
        address = create_test_address(user)
        
        # Create variant sizes and add to cart
        variant_sizes = []
        stock_records_before = []
        
        try:
            for i in range(num_items):
                variant_size = create_test_variant_size(stock_quantity=quantities[i] + 10)
                variant_sizes.append(variant_size)
                
                # Record stock before
                stock = Stock.objects.get(variant_size=variant_size)
                stock_records_before.append({
                    'variant_size_id': variant_size.id,
                    'quantity_reserved': stock.quantity_reserved,
                    'quantity_in_stock': stock.quantity_in_stock
                })
                
                # Add to cart
                CartService.add_to_cart(user, variant_size.id, quantities[i])
            
            # Get cart
            cart = Cart.objects.get(user=user, status='active')
            
            # Create order
            result = OrderService.create_order_from_cart(
                user,
                cart.id,
                address.id
            )
            order = result['order']
            
            # Property: Stock should be reserved for all items
            for i, variant_size in enumerate(variant_sizes):
                stock_after = Stock.objects.get(variant_size=variant_size)
                stock_before = stock_records_before[i]
                
                expected_reserved = stock_before['quantity_reserved'] + quantities[i]
                
                assert stock_after.quantity_reserved == expected_reserved, \
                    f"Stock reserved should increase by {quantities[i]}: " \
                    f"expected {expected_reserved}, got {stock_after.quantity_reserved}"
                
                # Property: quantity_in_stock should remain unchanged
                assert stock_after.quantity_in_stock == stock_before['quantity_in_stock'], \
                    "quantity_in_stock should not change during reservation"
            
            # Property: Order should have correct number of items
            order_items_count = OrderItem.objects.filter(order=order).count()
            assert order_items_count == num_items, \
                f"Order should have {num_items} items, got {order_items_count}"
            
        finally:
            # Cleanup - delete orders first due to RESTRICT constraint
            Order.objects.filter(user=user).delete()
            user.delete()
            cleanup_address(address)
            for vs in variant_sizes:
                cleanup_variant_size(vs)


class TestPriceSnapshotting(TestCase):
    """
    Property 16: Order items snapshot prices
    
    Feature: complete-ecommerce-platform, Property 16: Order items snapshot prices
    Validates: Requirements 5.4
    
    For any order item, the snapshot_unit_price should remain constant even
    if the product variant base_price changes later.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        initial_price=st.decimals(min_value=100, max_value=500, places=2),
        new_price=st.decimals(min_value=100, max_value=500, places=2),
        quantity=st.integers(min_value=1, max_value=5)
    )
    def test_order_items_snapshot_prices(self, initial_price, new_price, quantity):
        """
        For any order item, snapshot_unit_price should remain constant even
        if base_price changes.
        """
        # Create test user
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Create address
        address = create_test_address(user)
        
        # Create variant size with initial price
        variant_size = create_test_variant_size(
            stock_quantity=quantity + 10,
            base_price=initial_price
        )
        
        try:
            # Add to cart
            CartService.add_to_cart(user, variant_size.id, quantity)
            
            # Get cart
            cart = Cart.objects.get(user=user, status='active')
            
            # Create order
            result = OrderService.create_order_from_cart(
                user,
                cart.id,
                address.id
            )
            order = result['order']
            
            # Get order item
            order_item = OrderItem.objects.get(order=order, variant_size=variant_size)
            snapshot_price = order_item.snapshot_unit_price
            
            # Property: Snapshot price should be calculated from initial price
            # snapshot_price = base_price * (1 + markup_percentage / 100)
            # markup_percentage = 10.00
            expected_snapshot = initial_price * Decimal('1.10')
            expected_snapshot = expected_snapshot.quantize(Decimal('0.01'))
            
            assert snapshot_price == expected_snapshot, \
                f"Snapshot price should be {expected_snapshot}, got {snapshot_price}"
            
            # Change the base price
            variant = variant_size.variant
            variant.base_price = new_price
            variant.save()
            
            # Refresh order item from database
            order_item.refresh_from_db()
            
            # Property: Snapshot price should remain unchanged
            assert order_item.snapshot_unit_price == snapshot_price, \
                f"Snapshot price should remain {snapshot_price} after base_price change, " \
                f"got {order_item.snapshot_unit_price}"
            
        finally:
            # Cleanup - delete orders first due to RESTRICT constraint
            Order.objects.filter(user=user).delete()
            user.delete()
            cleanup_address(address)
            cleanup_variant_size(variant_size)


class TestInsufficientStock(TestCase):
    """
    Property 17: Insufficient stock prevents order creation
    
    Feature: complete-ecommerce-platform, Property 17: Insufficient stock prevents order creation
    Validates: Requirements 5.5
    
    For any cart with items where quantity exceeds available stock, order
    creation should fail and return an error.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        stock_quantity=st.integers(min_value=1, max_value=5),
        requested_quantity=st.integers(min_value=6, max_value=10)
    )
    def test_insufficient_stock_prevents_order_creation(self, stock_quantity, requested_quantity):
        """
        For any cart with items exceeding available stock, order creation
        should fail.
        """
        # Ensure requested > stock
        assume(requested_quantity > stock_quantity)
        
        # Create test user
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Create address
        address = create_test_address(user)
        
        # Create variant size with limited stock
        variant_size = create_test_variant_size(stock_quantity=stock_quantity)
        
        try:
            # Manually create cart and cart item (bypassing stock validation)
            cart = Cart.objects.create(user=user, status='active')
            CartItem.objects.create(
                cart=cart,
                variant_size=variant_size,
                quantity=requested_quantity
            )
            
            # Property: Order creation should fail with ValidationError
            with self.assertRaises(ValidationError) as context:
                OrderService.create_order_from_cart(
                    user,
                    cart.id,
                    address.id
                )
            
            # Property: Error should mention insufficient stock
            error_message = str(context.exception)
            assert 'stock' in error_message.lower(), \
                f"Error should mention stock issue: {error_message}"
            
            # Property: No order should be created
            order_count = Order.objects.filter(user=user).count()
            assert order_count == 0, \
                f"No order should be created when stock is insufficient, found {order_count}"
            
            # Property: Stock should not be reserved
            stock = Stock.objects.get(variant_size=variant_size)
            assert stock.quantity_reserved == 0, \
                f"Stock should not be reserved on failed order, got {stock.quantity_reserved}"
            
        finally:
            # Cleanup - no orders created in this test, so just delete user
            user.delete()
            cleanup_address(address)
            cleanup_variant_size(variant_size)


class TestOrderProcessingAtomicity(TestCase):
    """
    Property 59: Order processing is atomic
    
    Feature: complete-ecommerce-platform, Property 59: Order processing is atomic
    Validates: Requirements 15.1
    
    For any order creation attempt, if any step fails (cart validation, order
    creation, stock reservation, payment initiation), all database changes
    should be rolled back.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        quantity=st.integers(min_value=1, max_value=5)
    )
    def test_order_processing_is_atomic(self, quantity):
        """
        For any order creation that fails, all database changes should be
        rolled back (atomicity).
        """
        # Create test user
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Create variant size
        variant_size = create_test_variant_size(stock_quantity=quantity + 10)
        
        try:
            # Add to cart
            CartService.add_to_cart(user, variant_size.id, quantity)
            
            # Get cart
            cart = Cart.objects.get(user=user, status='active')
            
            # Record initial state
            initial_cart_status = cart.status
            initial_stock = Stock.objects.get(variant_size=variant_size)
            initial_reserved = initial_stock.quantity_reserved
            initial_order_count = Order.objects.filter(user=user).count()
            
            # Property: Using invalid address ID should cause failure
            invalid_address_id = 999999
            
            with self.assertRaises(ValidationError):
                OrderService.create_order_from_cart(
                    user,
                    cart.id,
                    invalid_address_id
                )
            
            # Property: Cart status should remain unchanged (rollback)
            cart.refresh_from_db()
            assert cart.status == initial_cart_status, \
                f"Cart status should remain {initial_cart_status} after failed order, " \
                f"got {cart.status}"
            
            # Property: Stock reservation should remain unchanged (rollback)
            stock_after = Stock.objects.get(variant_size=variant_size)
            assert stock_after.quantity_reserved == initial_reserved, \
                f"Stock reserved should remain {initial_reserved} after failed order, " \
                f"got {stock_after.quantity_reserved}"
            
            # Property: No order should be created (rollback)
            final_order_count = Order.objects.filter(user=user).count()
            assert final_order_count == initial_order_count, \
                f"Order count should remain {initial_order_count} after failed order, " \
                f"got {final_order_count}"
            
            # Property: No order items should be created (rollback)
            order_items_count = OrderItem.objects.filter(
                order__user=user
            ).count()
            assert order_items_count == 0, \
                f"No order items should exist after failed order, found {order_items_count}"
            
        finally:
            # Cleanup - no orders created in this test, so just delete user
            user.delete()
            cleanup_variant_size(variant_size)
