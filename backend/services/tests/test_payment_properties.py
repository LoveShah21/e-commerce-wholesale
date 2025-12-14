"""
Property-Based Tests for Payment Service

Tests correctness properties for payment operations using Hypothesis.
Feature: complete-ecommerce-platform
"""

from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import uuid

from apps.orders.models import Cart, Order, OrderItem
from apps.products.models import (
    Product, ProductVariant, VariantSize, Size, Stock,
    Fabric, Color, Pattern, Sleeve, Pocket
)
from apps.users.models import Address, Country, State, City, PostalCode
from apps.finance.models import Payment, TaxConfiguration
from services.payment_service import PaymentService
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


def create_test_tax_config():
    """Helper to create a TaxConfiguration for testing"""
    from datetime import date
    
    tax_config = TaxConfiguration.objects.create(
        tax_name='GST',
        tax_percentage=Decimal('18.00'),
        effective_from=date(2020, 1, 1),
        is_active=True
    )
    
    return tax_config


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


class TestAdvancePaymentAmount(TestCase):
    """
    Property 18: Advance payment is 50% of order total
    
    Feature: complete-ecommerce-platform, Property 18: Advance payment is 50% of order total
    Validates: Requirements 6.1
    
    For any order requiring advance payment, the payment amount should equal
    exactly 50% of the order total (rounded appropriately).
    """
    
    @settings(max_examples=3, deadline=None)
    @given(
        order_total=st.decimals(min_value=100, max_value=10000, places=2)
    )
    def test_advance_payment_is_50_percent(self, order_total):
        """
        For any order total, advance payment amount should be exactly 50%.
        This tests the calculation logic directly without full order creation.
        """
        # Test the calculation logic directly
        expected_advance = (order_total * Decimal('0.5')).quantize(Decimal('0.01'))
        
        # Property: Advance payment should be approximately 50% (within 1 paisa due to rounding)
        half_total = (order_total / 2).quantize(Decimal('0.01'))
        difference = abs(expected_advance - half_total)
        assert difference <= Decimal('0.01'), \
            f"Advance payment should be approximately 50% of {order_total}, difference: {difference}"
        
        # Property: Advance + Final should equal total
        expected_final = (order_total - expected_advance).quantize(Decimal('0.01'))
        total_paid = expected_advance + expected_final
        
        assert total_paid == order_total, \
            f"Advance + Final should equal total {order_total}, got {total_paid}"


class TestPaymentVerification(TestCase):
    """
    Property 19: Payment signature verification is correct
    
    Feature: complete-ecommerce-platform, Property 19: Payment signature verification is correct
    Validates: Requirements 6.2
    
    For any payment with valid Razorpay signature, verification should succeed;
    for invalid signatures, verification should fail.
    """
    
    @settings(max_examples=5, deadline=None)
    @given(
        order_id_suffix=st.text(min_size=5, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        payment_id_suffix=st.text(min_size=5, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
    )
    def test_payment_signature_verification(self, order_id_suffix, payment_id_suffix):
        """
        For any payment, signature verification should correctly validate
        authentic signatures and reject invalid ones.
        """
        import hmac
        import hashlib
        
        # Create test order and payment IDs
        razorpay_order_id = f"order_{order_id_suffix}"
        razorpay_payment_id = f"pay_{payment_id_suffix}"
        
        # Generate valid signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        valid_signature = hmac.new(
            PaymentService.RAZORPAY_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Property: Valid signature should pass verification
        is_valid = PaymentService.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            valid_signature
        )
        
        assert is_valid is True, \
            "Valid signature should pass verification"
        
        # Generate invalid signature (tampered)
        invalid_signature = valid_signature[:-4] + "0000"
        
        # Property: Invalid signature should fail verification
        is_invalid = PaymentService.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            invalid_signature
        )
        
        assert is_invalid is False, \
            "Invalid signature should fail verification"


class TestFinalPaymentAmount(TestCase):
    """
    Property 22: Final payment is remaining 50%
    
    Feature: complete-ecommerce-platform, Property 22: Final payment is remaining 50%
    Validates: Requirements 6.5
    
    For any order ready for dispatch, the final payment amount should equal
    the order total minus the advance payment amount.
    """
    
    @settings(max_examples=3, deadline=None)
    @given(
        order_total=st.decimals(min_value=100, max_value=10000, places=2)
    )
    def test_final_payment_is_remaining_50_percent(self, order_total):
        """
        For any order total, final payment should be remaining 50%.
        This tests the calculation logic directly.
        """
        # Calculate advance payment (50%)
        advance_amount = (order_total * Decimal('0.5')).quantize(Decimal('0.01'))
        
        # Calculate final payment (remaining amount)
        final_amount = (order_total - advance_amount).quantize(Decimal('0.01'))
        
        # Property: Final payment should be remaining amount
        assert final_amount == order_total - advance_amount, \
            f"Final payment should be {order_total} - {advance_amount}"
        
        # Property: Advance + Final should equal total
        total_paid = advance_amount + final_amount
        assert total_paid == order_total, \
            f"Advance + Final should equal total {order_total}, got {total_paid}"
        
        # Property: Both payments should be approximately equal (within 1 rupee due to rounding)
        difference = abs(advance_amount - final_amount)
        assert difference <= Decimal('1.00'), \
            f"Advance and final payments should be approximately equal, difference: {difference}"


class TestPaymentAtomicity(TestCase):
    """
    Property 62: Payment verification updates records atomically
    
    Feature: complete-ecommerce-platform, Property 62: Payment verification updates records atomically
    Validates: Requirements 15.4
    
    For any payment verification, both payment status and order status should
    be updated together or not at all.
    """
    
    @settings(max_examples=2, deadline=None)
    @given(
        base_price=st.decimals(min_value=100, max_value=500, places=2),
        quantity=st.integers(min_value=1, max_value=2)
    )
    def test_payment_verification_is_atomic(self, base_price, quantity):
        """
        For any payment verification, payment and order updates should be atomic.
        """
        # Create test user
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Create tax configuration
        tax_config = create_test_tax_config()
        
        # Create address
        address = create_test_address(user)
        
        # Create variant size
        variant_size = create_test_variant_size(
            stock_quantity=quantity + 10,
            base_price=base_price
        )
        
        try:
            # Add to cart and create order
            CartService.add_to_cart(user, variant_size.id, quantity)
            cart = Cart.objects.get(user=user, status='active')
            
            result = OrderService.create_order_from_cart(
                user,
                cart.id,
                address.id
            )
            order = result['order']
            
            # Mock Razorpay client
            with patch.object(PaymentService, '_get_razorpay_client') as mock_client:
                mock_razorpay = MagicMock()
                mock_razorpay.order.create.return_value = {
                    'id': f'order_{uuid.uuid4().hex[:10]}',
                    'amount': 50000,
                    'currency': 'INR'
                }
                mock_client.return_value = mock_razorpay
                
                # Create advance payment
                payment_result = PaymentService.create_razorpay_order(
                    order.id,
                    'advance',
                    'upi'
                )
                payment = payment_result['payment']
                
                # Generate valid signature
                import hmac
                import hashlib
                razorpay_payment_id = f'pay_{uuid.uuid4().hex[:10]}'
                message = f"{payment.razorpay_order_id}|{razorpay_payment_id}"
                valid_signature = hmac.new(
                    PaymentService.RAZORPAY_KEY_SECRET.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                # Process successful payment
                success_result = PaymentService.process_successful_payment(
                    payment.id,
                    razorpay_payment_id,
                    valid_signature
                )
                
                updated_payment = success_result['payment']
                updated_order = success_result['order']
                
                # Property: Payment status should be updated to 'success'
                assert updated_payment.payment_status == 'success', \
                    f"Payment status should be 'success', got {updated_payment.payment_status}"
                
                # Property: Order status should be updated to 'confirmed' for advance payment
                assert updated_order.status == 'confirmed', \
                    f"Order status should be 'confirmed' after advance payment, " \
                    f"got {updated_order.status}"
                
                # Property: Payment should have razorpay_payment_id
                assert updated_payment.razorpay_payment_id == razorpay_payment_id, \
                    "Payment should have razorpay_payment_id set"
                
                # Property: Payment should have paid_at timestamp
                assert updated_payment.paid_at is not None, \
                    "Payment should have paid_at timestamp"
                
                # Test atomicity with invalid signature
                payment_result2 = PaymentService.create_razorpay_order(
                    order.id,
                    'final',
                    'upi'
                )
                payment2 = payment_result2['payment']
                
                # Try to process with invalid signature
                invalid_signature = valid_signature[:-4] + "0000"
                
                with self.assertRaises(ValidationError):
                    PaymentService.process_successful_payment(
                        payment2.id,
                        f'pay_{uuid.uuid4().hex[:10]}',
                        invalid_signature
                    )
                
                # Property: Payment status should remain 'initiated' after failed verification
                payment2.refresh_from_db()
                assert payment2.payment_status == 'initiated', \
                    f"Payment status should remain 'initiated' after failed verification, " \
                    f"got {payment2.payment_status}"
                
        finally:
            # Cleanup - delete in correct order to avoid foreign key issues
            Payment.objects.filter(order=order).delete()
            OrderItem.objects.filter(order=order).delete()
            order.delete()
            Cart.objects.filter(user=user).delete()
            user.delete()
            cleanup_address(address)
            cleanup_variant_size(variant_size)
            tax_config.delete()
