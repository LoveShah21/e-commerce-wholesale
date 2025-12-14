"""
Property-Based Tests for Cart Service

Tests correctness properties for shopping cart operations using Hypothesis.
Feature: complete-ecommerce-platform
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import uuid

from apps.orders.models import Cart, CartItem
from apps.products.models import (
    Product, ProductVariant, VariantSize, Size, Stock,
    Fabric, Color, Pattern, Sleeve, Pocket
)
from apps.finance.models import TaxConfiguration
from services.cart_service import CartService


User = get_user_model()


def create_test_variant_size(stock_quantity):
    """Helper to create a VariantSize with Stock for testing"""
    unique_id = uuid.uuid4().hex[:6]  # Shorter ID to fit in size_code field
    
    fabric = Fabric.objects.create(fabric_name=f"Fabric_{unique_id}")
    color = Color.objects.create(color_name=f"Color_{unique_id}")
    pattern = Pattern.objects.create(pattern_name=f"Pattern_{unique_id}")
    sleeve = Sleeve.objects.create(sleeve_type=f"Sleeve_{unique_id}")
    pocket = Pocket.objects.create(pocket_type=f"Pocket_{unique_id}")
    size = Size.objects.create(
        size_code=f"S{unique_id}",  # Shorter prefix
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
        base_price=Decimal('500.00')
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


class TestCartIdempotency(TestCase):
    """
    Property 10: Cart item creation is idempotent
    
    Feature: complete-ecommerce-platform, Property 10: Cart item creation is idempotent
    Validates: Requirements 4.1
    
    For any cart and variant_size, adding the same item twice should update
    the quantity rather than create duplicate items.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        quantity1=st.integers(min_value=1, max_value=10),
        quantity2=st.integers(min_value=1, max_value=10)
    )
    def test_adding_same_item_twice_updates_quantity(self, quantity1, quantity2):
        """
        For any cart and variant_size, adding the same item twice should
        update the quantity rather than create duplicate items.
        """
        # Create test data
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        variant_size = create_test_variant_size(stock_quantity=quantity1 + quantity2 + 10)
        
        try:
            # Add item first time
            result1 = CartService.add_to_cart(user, variant_size.id, quantity1)
            cart_item_1 = result1['cart_item']
            
            # Add same item second time
            result2 = CartService.add_to_cart(user, variant_size.id, quantity2)
            cart_item_2 = result2['cart_item']
            
            # Property: Should be the same cart item (idempotent)
            assert cart_item_1.id == cart_item_2.id, \
                "Adding the same item twice should update existing item, not create duplicate"
            
            # Property: Quantity should be sum of both additions
            assert cart_item_2.quantity == quantity1 + quantity2, \
                f"Expected quantity {quantity1 + quantity2}, got {cart_item_2.quantity}"
            
            # Property: Should only have one cart item for this variant_size
            cart = Cart.objects.get(user=user, status='active')
            cart_items_count = CartItem.objects.filter(
                cart=cart,
                variant_size=variant_size
            ).count()
            assert cart_items_count == 1, \
                f"Expected 1 cart item, found {cart_items_count} duplicates"
        finally:
            # Cleanup
            user.delete()
            cleanup_variant_size(variant_size)


class TestCartStockValidation(TestCase):
    """
    Property 11: Cart updates validate stock availability
    
    Feature: complete-ecommerce-platform, Property 11: Cart updates validate stock availability
    Validates: Requirements 4.2
    
    For any cart item quantity update, if the requested quantity exceeds
    available stock, the update should be rejected.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        initial_quantity=st.integers(min_value=1, max_value=10),
        stock_quantity=st.integers(min_value=5, max_value=20)
    )
    def test_cart_update_validates_stock(self, initial_quantity, stock_quantity):
        """
        For any cart item, updating quantity beyond available stock should fail.
        """
        # Ensure initial quantity is within stock
        if initial_quantity > stock_quantity:
            return  # Skip this test case
        
        # Create test data
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        variant_size = create_test_variant_size(stock_quantity=stock_quantity)
        
        try:
            # Add item to cart with initial quantity
            result = CartService.add_to_cart(user, variant_size.id, initial_quantity)
            cart_item = result['cart_item']
            
            # Property: Updating to quantity within stock should succeed
            if initial_quantity < stock_quantity:
                valid_quantity = min(initial_quantity + 1, stock_quantity)
                updated_item = CartService.update_cart_item(cart_item.id, valid_quantity, user)
                assert updated_item.quantity == valid_quantity, \
                    "Update within stock should succeed"
            
            # Property: Updating to quantity exceeding stock should fail
            invalid_quantity = stock_quantity + 1
            with self.assertRaises(ValidationError) as context:
                CartService.update_cart_item(cart_item.id, invalid_quantity, user)
            
            self.assertIn("Insufficient stock", str(context.exception),
                          "Update exceeding stock should raise ValidationError with 'Insufficient stock'")
        finally:
            # Cleanup
            user.delete()
            cleanup_variant_size(variant_size)


class TestCartPersistence(TestCase):
    """
    Property 14: Cart persists across sessions
    
    Feature: complete-ecommerce-platform, Property 14: Cart persists across sessions
    Validates: Requirements 4.5
    
    For any user with an active cart, after logout and login, the cart should
    contain the same items with the same quantities.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_items=st.integers(min_value=1, max_value=5),
        quantities=st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=5)
    )
    def test_cart_persists_across_sessions(self, num_items, quantities):
        """
        For any user with items in cart, the cart should persist across sessions.
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
        
        # Create multiple variant sizes and add to cart
        variant_sizes = []
        try:
            for i in range(num_items):
                variant_size = create_test_variant_size(stock_quantity=quantities[i] + 10)
                variant_sizes.append(variant_size)
                
                # Add to cart
                CartService.add_to_cart(user, variant_size.id, quantities[i])
            
            # Get cart before "logout"
            cart_before = Cart.objects.get(user=user, status='active')
            items_before = list(cart_before.items.values('variant_size_id', 'quantity'))
            
            # Simulate session end by getting cart again (simulating new session)
            # In Django, the cart persists because it's tied to the user, not the session
            cart_after = CartService.get_or_create_cart(user)
            items_after = list(cart_after.items.values('variant_size_id', 'quantity'))
            
            # Property: Cart ID should be the same
            assert cart_before.id == cart_after.id, \
                "Cart should persist across sessions"
            
            # Property: Same number of items
            assert len(items_before) == len(items_after), \
                f"Expected {len(items_before)} items, found {len(items_after)}"
            
            # Property: Same items with same quantities
            items_before_sorted = sorted(items_before, key=lambda x: x['variant_size_id'])
            items_after_sorted = sorted(items_after, key=lambda x: x['variant_size_id'])
            
            for before, after in zip(items_before_sorted, items_after_sorted):
                assert before['variant_size_id'] == after['variant_size_id'], \
                    "Cart items should have same variant_size_id"
                assert before['quantity'] == after['quantity'], \
                    f"Cart item quantity should persist: expected {before['quantity']}, got {after['quantity']}"
        finally:
            # Cleanup
            user.delete()
            for vs in variant_sizes:
                cleanup_variant_size(vs)
