"""
Unit tests for service utility functions

Tests SKU generation, price calculation with markup, and tax calculation.
"""

from decimal import Decimal
from django.test import TestCase
from services.utils import (
    generate_sku,
    calculate_price_with_markup,
    calculate_tax,
    calculate_total_with_tax,
)


class TestSKUGeneration(TestCase):
    """Test cases for SKU generation utility"""
    
    def test_sku_generation_with_default_prefix(self):
        """Test SKU generation with default prefix"""
        sku = generate_sku()
        self.assertTrue(sku.startswith("SKU-"))
        self.assertEqual(len(sku.split("-")), 3)
    
    def test_sku_generation_with_custom_prefix(self):
        """Test SKU generation with custom prefix"""
        sku = generate_sku("SHIRT")
        self.assertTrue(sku.startswith("SHIRT-"))
        self.assertEqual(len(sku.split("-")), 3)
    
    def test_sku_uniqueness(self):
        """Test that generated SKUs are unique"""
        skus = set()
        for _ in range(100):
            sku = generate_sku()
            skus.add(sku)
        
        # All 100 SKUs should be unique
        self.assertEqual(len(skus), 100)
    
    def test_sku_format(self):
        """Test SKU format contains timestamp and unique ID"""
        sku = generate_sku("TEST")
        parts = sku.split("-")
        
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "TEST")
        # Timestamp should be 8 digits (YYYYMMDD)
        self.assertEqual(len(parts[1]), 8)
        self.assertTrue(parts[1].isdigit())
        # Unique ID should be 8 characters
        self.assertEqual(len(parts[2]), 8)


class TestPriceCalculation(TestCase):
    """Test cases for price calculation with markup"""
    
    def test_price_with_zero_markup(self):
        """Test price calculation with 0% markup"""
        base_price = Decimal('100.00')
        markup = Decimal('0.00')
        result = calculate_price_with_markup(base_price, markup)
        self.assertEqual(result, Decimal('100.00'))
    
    def test_price_with_10_percent_markup(self):
        """Test price calculation with 10% markup"""
        base_price = Decimal('100.00')
        markup = Decimal('10.00')
        result = calculate_price_with_markup(base_price, markup)
        self.assertEqual(result, Decimal('110.00'))
    
    def test_price_with_25_percent_markup(self):
        """Test price calculation with 25% markup"""
        base_price = Decimal('200.00')
        markup = Decimal('25.00')
        result = calculate_price_with_markup(base_price, markup)
        self.assertEqual(result, Decimal('250.00'))
    
    def test_price_with_fractional_markup(self):
        """Test price calculation with fractional markup percentage"""
        base_price = Decimal('100.00')
        markup = Decimal('12.50')
        result = calculate_price_with_markup(base_price, markup)
        self.assertEqual(result, Decimal('112.50'))
    
    def test_price_rounding(self):
        """Test that price is rounded to 2 decimal places"""
        base_price = Decimal('99.99')
        markup = Decimal('10.00')
        result = calculate_price_with_markup(base_price, markup)
        # 99.99 * 1.10 = 109.989, should round to 109.99
        self.assertEqual(result, Decimal('109.99'))
    
    def test_negative_base_price_raises_error(self):
        """Test that negative base price raises ValueError"""
        with self.assertRaises(ValueError) as context:
            calculate_price_with_markup(Decimal('-100.00'), Decimal('10.00'))
        self.assertIn("Base price cannot be negative", str(context.exception))
    
    def test_negative_markup_raises_error(self):
        """Test that negative markup percentage raises ValueError"""
        with self.assertRaises(ValueError) as context:
            calculate_price_with_markup(Decimal('100.00'), Decimal('-10.00'))
        self.assertIn("Markup percentage cannot be negative", str(context.exception))


class TestTaxCalculation(TestCase):
    """Test cases for tax calculation"""
    
    def test_tax_with_18_percent_gst(self):
        """Test tax calculation with 18% GST"""
        amount = Decimal('1000.00')
        tax_rate = Decimal('18.00')
        result = calculate_tax(amount, tax_rate)
        self.assertEqual(result, Decimal('180.00'))
    
    def test_tax_with_zero_rate(self):
        """Test tax calculation with 0% tax rate"""
        amount = Decimal('1000.00')
        tax_rate = Decimal('0.00')
        result = calculate_tax(amount, tax_rate)
        self.assertEqual(result, Decimal('0.00'))
    
    def test_tax_with_fractional_rate(self):
        """Test tax calculation with fractional tax rate"""
        amount = Decimal('1000.00')
        tax_rate = Decimal('12.50')
        result = calculate_tax(amount, tax_rate)
        self.assertEqual(result, Decimal('125.00'))
    
    def test_tax_rounding(self):
        """Test that tax is rounded to 2 decimal places"""
        amount = Decimal('99.99')
        tax_rate = Decimal('18.00')
        result = calculate_tax(amount, tax_rate)
        # 99.99 * 0.18 = 17.9982, should round to 18.00
        self.assertEqual(result, Decimal('18.00'))
    
    def test_tax_on_small_amount(self):
        """Test tax calculation on small amounts"""
        amount = Decimal('10.00')
        tax_rate = Decimal('5.00')
        result = calculate_tax(amount, tax_rate)
        self.assertEqual(result, Decimal('0.50'))
    
    def test_negative_amount_raises_error(self):
        """Test that negative amount raises ValueError"""
        with self.assertRaises(ValueError) as context:
            calculate_tax(Decimal('-1000.00'), Decimal('18.00'))
        self.assertIn("Amount cannot be negative", str(context.exception))
    
    def test_negative_tax_rate_raises_error(self):
        """Test that negative tax rate raises ValueError"""
        with self.assertRaises(ValueError) as context:
            calculate_tax(Decimal('1000.00'), Decimal('-18.00'))
        self.assertIn("Tax percentage cannot be negative", str(context.exception))


class TestTotalWithTaxCalculation(TestCase):
    """Test cases for total with tax calculation"""
    
    def test_total_with_tax(self):
        """Test calculation of tax and total together"""
        subtotal = Decimal('1000.00')
        tax_rate = Decimal('18.00')
        tax, total = calculate_total_with_tax(subtotal, tax_rate)
        
        self.assertEqual(tax, Decimal('180.00'))
        self.assertEqual(total, Decimal('1180.00'))
    
    def test_total_with_zero_tax(self):
        """Test total calculation with zero tax"""
        subtotal = Decimal('500.00')
        tax_rate = Decimal('0.00')
        tax, total = calculate_total_with_tax(subtotal, tax_rate)
        
        self.assertEqual(tax, Decimal('0.00'))
        self.assertEqual(total, Decimal('500.00'))
    
    def test_total_with_fractional_values(self):
        """Test total calculation with fractional values"""
        subtotal = Decimal('99.99')
        tax_rate = Decimal('12.50')
        tax, total = calculate_total_with_tax(subtotal, tax_rate)
        
        self.assertEqual(tax, Decimal('12.50'))
        self.assertEqual(total, Decimal('112.49'))
