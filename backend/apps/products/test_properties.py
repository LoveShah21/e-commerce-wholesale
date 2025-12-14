"""
Property-Based Tests for Product Management

These tests verify universal properties that should hold across all inputs
using the Hypothesis library for property-based testing.
"""

from decimal import Decimal
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.db import IntegrityError
from apps.products.models import (
    Product, ProductVariant, VariantSize, Stock, Fabric, Color, Pattern,
    Sleeve, Pocket, Size
)
from services.utils import generate_sku


class ProductPropertyTests(TestCase):
    """Property-based tests for product management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create required attribute objects using get_or_create to avoid duplicates
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
        self.product = Product.objects.create(
            product_name="Test Shirt",
            description="Test Description"
        )
    
    @settings(max_examples=10)
    @given(
        base_price1=st.decimals(min_value=Decimal('100'), max_value=Decimal('10000'), places=2),
        base_price2=st.decimals(min_value=Decimal('100'), max_value=Decimal('10000'), places=2)
    )
    def test_property_5_product_variant_skus_are_unique(self, base_price1, base_price2):
        """
        Feature: complete-ecommerce-platform, Property 5: Product variant SKUs are unique
        Validates: Requirements 2.2
        
        For any two product variants, their SKU values should be different if both SKUs are non-null.
        """
        # Create two variants with generated SKUs
        sku1 = generate_sku('SHIRT')
        sku2 = generate_sku('SHIRT')
        
        # SKUs should be different
        self.assertNotEqual(sku1, sku2, "Generated SKUs should be unique")
        
        # Create first variant
        variant1 = ProductVariant.objects.create(
            product=self.product,
            fabric=self.fabric,
            color=self.color,
            pattern=self.pattern,
            sleeve=self.sleeve,
            pocket=self.pocket,
            base_price=base_price1,
            sku=sku1
        )
        
        # Create a second fabric to avoid unique_together constraint
        fabric2 = Fabric.objects.create(fabric_name=f"Cotton_{base_price2}")
        
        # Create second variant with different SKU
        variant2 = ProductVariant.objects.create(
            product=self.product,
            fabric=fabric2,
            color=self.color,
            pattern=self.pattern,
            sleeve=self.sleeve,
            pocket=self.pocket,
            base_price=base_price2,
            sku=sku2
        )
        
        # Verify both variants exist with different SKUs
        self.assertIsNotNone(variant1.sku)
        self.assertIsNotNone(variant2.sku)
        self.assertNotEqual(variant1.sku, variant2.sku)
        
        # Verify database constraint: attempting to create a variant with duplicate SKU should fail
        with self.assertRaises(IntegrityError):
            fabric3 = Fabric.objects.create(fabric_name=f"Silk_{base_price1}")
            ProductVariant.objects.create(
                product=self.product,
                fabric=fabric3,
                color=self.color,
                pattern=self.pattern,
                sleeve=self.sleeve,
                pocket=self.pocket,
                base_price=base_price1,
                sku=sku1  # Duplicate SKU
            )

    @settings(max_examples=10)
    @given(
        initial_stock=st.integers(min_value=0, max_value=1000),
        updated_stock=st.integers(min_value=0, max_value=1000)
    )
    def test_property_6_stock_updates_are_persisted_correctly(self, initial_stock, updated_stock):
        """
        Feature: complete-ecommerce-platform, Property 6: Stock updates are persisted correctly
        Validates: Requirements 2.5
        
        For any variant size, after updating stock quantity, retrieving the stock record 
        should reflect the new quantity.
        """
        # Create a variant
        variant = ProductVariant.objects.create(
            product=self.product,
            fabric=self.fabric,
            color=self.color,
            pattern=self.pattern,
            sleeve=self.sleeve,
            pocket=self.pocket,
            base_price=Decimal('500.00'),
            sku=generate_sku('SHIRT')
        )
        
        # Create a variant size
        variant_size = VariantSize.objects.create(
            variant=variant,
            size=self.size,
            stock_quantity=initial_stock
        )
        
        # Create stock record with initial stock
        stock = Stock.objects.create(
            variant_size=variant_size,
            quantity_in_stock=initial_stock,
            quantity_reserved=0
        )
        
        # Verify initial stock
        self.assertEqual(stock.quantity_in_stock, initial_stock)
        
        # Update stock quantity
        stock.quantity_in_stock = updated_stock
        stock.save()
        
        # Retrieve the stock record from database
        stock_from_db = Stock.objects.get(variant_size=variant_size)
        
        # Verify the updated quantity is persisted
        self.assertEqual(stock_from_db.quantity_in_stock, updated_stock)
        
        # Verify last_updated timestamp is set
        self.assertIsNotNone(stock_from_db.last_updated)

    @settings(max_examples=10)
    @given(
        num_products=st.integers(min_value=1, max_value=10),
        filter_choice=st.integers(min_value=0, max_value=2)  # 0=fabric, 1=color, 2=pattern
    )
    def test_property_7_product_filters_return_correct_subsets(self, num_products, filter_choice):
        """
        Feature: complete-ecommerce-platform, Property 7: Product filters return correct subsets
        Validates: Requirements 3.2
        
        For any product filter (fabric, color, pattern), the returned products should only 
        include those matching the filter criteria.
        """
        # Create additional attributes for variety
        fabric1 = Fabric.objects.create(fabric_name=f"Fabric_A_{num_products}")
        fabric2 = Fabric.objects.create(fabric_name=f"Fabric_B_{num_products}")
        color1 = Color.objects.create(color_name=f"Color_A_{num_products}")
        color2 = Color.objects.create(color_name=f"Color_B_{num_products}")
        pattern1 = Pattern.objects.create(pattern_name=f"Pattern_A_{num_products}")
        pattern2 = Pattern.objects.create(pattern_name=f"Pattern_B_{num_products}")
        
        # Create products with different variants
        products_with_filter = []
        products_without_filter = []
        
        for i in range(num_products):
            product = Product.objects.create(
                product_name=f"Product_{i}_{num_products}",
                description=f"Description {i}"
            )
            
            # Half products get filter attributes, half don't
            if i % 2 == 0:
                # Create variant with filter attributes
                ProductVariant.objects.create(
                    product=product,
                    fabric=fabric1,
                    color=color1,
                    pattern=pattern1,
                    sleeve=self.sleeve,
                    pocket=self.pocket,
                    base_price=Decimal('500.00'),
                    sku=generate_sku(f'SHIRT_{i}')
                )
                products_with_filter.append(product)
            else:
                # Create variant without filter attributes
                ProductVariant.objects.create(
                    product=product,
                    fabric=fabric2,
                    color=color2,
                    pattern=pattern2,
                    sleeve=self.sleeve,
                    pocket=self.pocket,
                    base_price=Decimal('600.00'),
                    sku=generate_sku(f'SHIRT_{i}')
                )
                products_without_filter.append(product)
        
        # Apply filter based on choice
        if filter_choice == 0:
            # Filter by fabric
            filtered_products = Product.objects.filter(variants__fabric=fabric1).distinct()
            filter_attr = fabric1
        elif filter_choice == 1:
            # Filter by color
            filtered_products = Product.objects.filter(variants__color=color1).distinct()
            filter_attr = color1
        else:
            # Filter by pattern
            filtered_products = Product.objects.filter(variants__pattern=pattern1).distinct()
            filter_attr = pattern1
        
        # Verify all filtered products have the filter attribute
        for product in filtered_products:
            if filter_choice == 0:
                self.assertTrue(
                    product.variants.filter(fabric=filter_attr).exists(),
                    f"Product {product.id} should have fabric {filter_attr}"
                )
            elif filter_choice == 1:
                self.assertTrue(
                    product.variants.filter(color=filter_attr).exists(),
                    f"Product {product.id} should have color {filter_attr}"
                )
            else:
                self.assertTrue(
                    product.variants.filter(pattern=filter_attr).exists(),
                    f"Product {product.id} should have pattern {filter_attr}"
                )
        
        # Verify the count matches expected
        expected_count = len(products_with_filter)
        self.assertEqual(filtered_products.count(), expected_count)

    @settings(max_examples=10)
    @given(
        search_term=st.text(
            min_size=1, 
            max_size=20, 
            alphabet=st.characters(min_codepoint=65, max_codepoint=122, blacklist_characters='\\')
        ).filter(lambda x: x.strip() and x.isascii()),
        num_products=st.integers(min_value=2, max_value=10)
    )
    def test_property_8_product_search_returns_relevant_results(self, search_term, num_products):
        """
        Feature: complete-ecommerce-platform, Property 8: Product search returns relevant results
        Validates: Requirements 3.3
        
        For any search query, all returned products should have the search term in either 
        product_name or description (case-insensitive).
        """
        # Clean up search term
        search_term = search_term.strip()
        if not search_term:
            return  # Skip empty search terms
        
        # Use a unique prefix to avoid conflicts with setUp products
        unique_prefix = f"SEARCH_{search_term[:5]}_{num_products}"
        
        # Create products with and without the search term
        matching_products = []
        non_matching_products = []
        
        for i in range(num_products):
            if i % 2 == 0:
                # Create product with search term in name
                product = Product.objects.create(
                    product_name=f"{unique_prefix}_{search_term}_Product_{i}",
                    description=f"Description {i}"
                )
                matching_products.append(product)
            else:
                # Create product without search term
                product = Product.objects.create(
                    product_name=f"{unique_prefix}_Other_Product_{i}",
                    description=f"Other description {i}"
                )
                non_matching_products.append(product)
        
        # Also create one with search term in description
        if num_products > 2:
            product_desc = Product.objects.create(
                product_name=f"{unique_prefix}_Product_Desc",
                description=f"This has {search_term} in description"
            )
            matching_products.append(product_desc)
        
        # Perform search (case-insensitive) - only search within our test products
        from django.db.models import Q
        search_results = Product.objects.filter(
            Q(product_name__icontains=search_term) | Q(description__icontains=search_term)
        ).filter(product_name__startswith=unique_prefix)
        
        # Verify all results contain the search term
        for product in search_results:
            search_term_lower = search_term.lower()
            name_lower = product.product_name.lower()
            desc_lower = (product.description or "").lower()
            
            self.assertTrue(
                search_term_lower in name_lower or search_term_lower in desc_lower,
                f"Product {product.id} (name: '{product.product_name}', desc: '{product.description}') "
                f"should contain search term '{search_term}'"
            )
        
        # Verify we got at least the matching products
        self.assertGreaterEqual(search_results.count(), len(matching_products))
