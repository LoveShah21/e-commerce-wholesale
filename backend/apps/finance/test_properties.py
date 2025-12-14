"""
Property-Based Tests for Invoice Generation

These tests verify universal properties that should hold across all inputs
using the Hypothesis library for property-based testing.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.core.exceptions import ValidationError
from apps.finance.models import Invoice, TaxConfiguration, Payment
from apps.orders.models import Order, OrderItem
from apps.users.models import User, Address, Country, State, City, PostalCode
from apps.products.models import (
    Product, ProductVariant, VariantSize, Stock, Fabric, Color, Pattern,
    Sleeve, Pocket, Size
)
from services.invoice_service import InvoiceService
from services.utils import generate_sku


class InvoicePropertyTests(TestCase):
    """Property-based tests for invoice generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create location data using get_or_create to avoid duplicates
        self.country, _ = Country.objects.get_or_create(
            country_code="IN",
            defaults={'country_name': "India"}
        )
        self.state, _ = State.objects.get_or_create(
            state_code="MH",
            country=self.country,
            defaults={'state_name': "Maharashtra"}
        )
        self.city, _ = City.objects.get_or_create(
            city_name="Mumbai",
            state=self.state
        )
        self.postal_code, _ = PostalCode.objects.get_or_create(
            postal_code="400001",
            city=self.city
        )
        
        # Create user using get_or_create to avoid duplicates across test runs
        self.user, created = User.objects.get_or_create(
            username="testuser",
            defaults={
                'email': "test@example.com",
                'full_name': "Test User",
                'user_type': "customer"
            }
        )
        if created:
            self.user.set_password("testpass123")
            self.user.save()
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            address_line1="123 Test St",
            postal_code=self.postal_code,
            address_type='home'
        )
        
        # Create product attributes using get_or_create to avoid duplicates
        self.fabric, _ = Fabric.objects.get_or_create(fabric_name="Cotton")
        self.color, _ = Color.objects.get_or_create(color_name="Blue")
        self.pattern, _ = Pattern.objects.get_or_create(pattern_name="Solid")
        self.sleeve, _ = Sleeve.objects.get_or_create(sleeve_type="Full Sleeve")
        self.pocket, _ = Pocket.objects.get_or_create(pocket_type="Single Pocket")
        self.size, _ = Size.objects.get_or_create(
            size_code="M",
            defaults={
                'size_name': "Medium",
                'size_markup_percentage': Decimal('0.00')
            }
        )
        
        # Create product and variant
        self.product = Product.objects.create(
            product_name="Test Shirt",
            description="Test Description"
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            fabric=self.fabric,
            color=self.color,
            pattern=self.pattern,
            sleeve=self.sleeve,
            pocket=self.pocket,
            base_price=Decimal('500.00'),
            sku=generate_sku('SHIRT')
        )
        
        self.variant_size = VariantSize.objects.create(
            variant=self.variant,
            size=self.size,
            stock_quantity=100
        )
        
        Stock.objects.create(
            variant_size=self.variant_size,
            quantity_in_stock=100,
            quantity_reserved=0
        )
        
        # Create tax configuration using get_or_create to avoid duplicates
        effective_from_date = datetime.now().date() - timedelta(days=30)
        self.tax_config, _ = TaxConfiguration.objects.get_or_create(
            tax_name="GST",
            effective_from=effective_from_date,
            defaults={
                'tax_percentage': Decimal('18.00'),
                'effective_to': None,
                'is_active': True
            }
        )
    
    @settings(max_examples=10)
    @given(
        num_invoices=st.integers(min_value=2, max_value=10)
    )
    def test_property_23_invoice_numbers_are_unique(self, num_invoices):
        """
        Feature: complete-ecommerce-platform, Property 23: Invoice numbers are unique
        Validates: Requirements 7.1
        
        For any two invoices, their invoice_number values should be different.
        """
        invoice_numbers = set()
        invoices = []
        
        # Create multiple orders and invoices
        for i in range(num_invoices):
            # Create order
            order = Order.objects.create(
                user=self.user,
                delivery_address=self.address,
                status='confirmed'
            )
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                variant_size=self.variant_size,
                quantity=1,
                snapshot_unit_price=Decimal('500.00')
            )
            
            # Generate invoice
            invoice = InvoiceService.generate_invoice(order.id)
            invoices.append(invoice)
            
            # Check uniqueness
            self.assertNotIn(
                invoice.invoice_number,
                invoice_numbers,
                f"Invoice number {invoice.invoice_number} is not unique"
            )
            invoice_numbers.add(invoice.invoice_number)
        
        # Verify all invoice numbers are unique
        self.assertEqual(
            len(invoice_numbers),
            num_invoices,
            "All invoice numbers should be unique"
        )
        
        # Verify database constraint: invoice_number is unique
        all_invoices = Invoice.objects.filter(id__in=[inv.id for inv in invoices])
        unique_invoice_numbers = all_invoices.values_list('invoice_number', flat=True).distinct()
        self.assertEqual(
            len(unique_invoice_numbers),
            num_invoices,
            "Database should enforce invoice number uniqueness"
        )
    
    @settings(max_examples=10)
    @given(
        tax_percentage=st.decimals(min_value=Decimal('0'), max_value=Decimal('30'), places=2),
        item_price=st.decimals(min_value=Decimal('100'), max_value=Decimal('10000'), places=2),
        quantity=st.integers(min_value=1, max_value=10)
    )
    def test_property_25_invoice_applies_correct_tax_rate(self, tax_percentage, item_price, quantity):
        """
        Feature: complete-ecommerce-platform, Property 25: Invoice applies correct tax rate
        Validates: Requirements 7.3
        
        For any invoice generated on a specific date, the tax rate should match 
        the active TaxConfiguration for that date.
        """
        # Update tax configuration with test tax percentage
        self.tax_config.tax_percentage = tax_percentage
        self.tax_config.save()
        
        # Create order
        order = Order.objects.create(
            user=self.user,
            delivery_address=self.address,
            status='confirmed'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            variant_size=self.variant_size,
            quantity=quantity,
            snapshot_unit_price=item_price
        )
        
        # Calculate expected values
        subtotal = item_price * quantity
        expected_tax = (subtotal * tax_percentage / Decimal('100')).quantize(Decimal('0.01'))
        expected_total = subtotal + expected_tax
        
        # Generate invoice
        invoice = InvoiceService.generate_invoice(order.id)
        
        # Calculate invoice totals
        totals = InvoiceService.calculate_invoice_totals(order.id)
        
        # Verify tax percentage matches active configuration
        self.assertEqual(
            totals['tax_percentage'],
            tax_percentage,
            f"Invoice should use tax rate {tax_percentage}% from active configuration"
        )
        
        # Verify tax calculation is correct
        self.assertEqual(
            totals['subtotal'],
            subtotal,
            "Subtotal should match order items total"
        )
        
        self.assertEqual(
            totals['tax_amount'],
            expected_tax,
            f"Tax amount should be {expected_tax} (subtotal {subtotal} * {tax_percentage}%)"
        )
        
        self.assertEqual(
            totals['total_amount'],
            expected_total,
            f"Total should be {expected_total} (subtotal {subtotal} + tax {expected_tax})"
        )
        
        # Verify invoice total matches calculated total
        self.assertEqual(
            invoice.total_amount,
            expected_total,
            "Invoice total_amount should match calculated total with tax"
        )
    
    @settings(max_examples=10)
    @given(
        num_items=st.integers(min_value=1, max_value=5),
        base_price=st.decimals(min_value=Decimal('100'), max_value=Decimal('5000'), places=2)
    )
    def test_property_61_invoice_generation_includes_tax_calculation(self, num_items, base_price):
        """
        Feature: complete-ecommerce-platform, Property 61: Invoice generation includes tax calculation
        Validates: Requirements 15.3
        
        For any invoice, the total_amount should equal subtotal plus (subtotal × tax_percentage).
        """
        # Create order
        order = Order.objects.create(
            user=self.user,
            delivery_address=self.address,
            status='confirmed'
        )
        
        # Create multiple order items
        subtotal = Decimal('0.00')
        for i in range(num_items):
            quantity = i + 1  # 1, 2, 3, etc.
            item_price = base_price + Decimal(str(i * 10))  # Vary prices slightly
            
            OrderItem.objects.create(
                order=order,
                variant_size=self.variant_size,
                quantity=quantity,
                snapshot_unit_price=item_price
            )
            
            subtotal += item_price * quantity
        
        # Get active tax configuration
        tax_config = InvoiceService.get_active_tax_config()
        self.assertIsNotNone(tax_config, "Active tax configuration should exist")
        
        # Calculate expected tax and total
        expected_tax = (subtotal * tax_config.tax_percentage / Decimal('100')).quantize(Decimal('0.01'))
        expected_total = subtotal + expected_tax
        
        # Generate invoice
        invoice = InvoiceService.generate_invoice(order.id)
        
        # Verify the formula: total_amount = subtotal + (subtotal × tax_percentage)
        self.assertEqual(
            invoice.total_amount,
            expected_total,
            f"Invoice total should equal subtotal ({subtotal}) + tax ({expected_tax}) = {expected_total}"
        )
        
        # Verify using calculate_invoice_totals
        totals = InvoiceService.calculate_invoice_totals(order.id)
        
        self.assertEqual(
            totals['subtotal'],
            subtotal,
            "Calculated subtotal should match sum of order items"
        )
        
        self.assertEqual(
            totals['tax_amount'],
            expected_tax,
            f"Tax should be {expected_tax} ({tax_config.tax_percentage}% of {subtotal})"
        )
        
        self.assertEqual(
            totals['total_amount'],
            expected_total,
            "Total should equal subtotal + tax"
        )
        
        # Verify the mathematical relationship
        calculated_total = totals['subtotal'] + totals['tax_amount']
        self.assertEqual(
            totals['total_amount'],
            calculated_total,
            "Total amount should equal subtotal plus tax amount"
        )
