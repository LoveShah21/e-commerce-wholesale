"""
Property-Based Tests for Manufacturing Service

Tests correctness properties for manufacturing operations using Hypothesis.
Feature: complete-ecommerce-platform
"""

from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import uuid

from apps.manufacturing.models import (
    ManufacturingSpecification, RawMaterial, MaterialType,
    Supplier, MaterialSupplier
)
from apps.manufacturing.services import ManufacturingService
from apps.orders.models import Order, OrderItem
from apps.products.models import (
    Product, ProductVariant, VariantSize, Size, Stock,
    Fabric, Color, Pattern, Sleeve, Pocket
)
from apps.users.models import Address, Country, State, City, PostalCode


User = get_user_model()


def create_test_variant_size(stock_quantity=100, base_price=Decimal('500.00')):
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


def create_test_material(quantity=Decimal('1000.00')):
    """Helper to create a RawMaterial for testing"""
    unique_id = uuid.uuid4().hex[:6]
    
    material_type = MaterialType.objects.create(
        material_type_name=f"MaterialType_{unique_id}",
        unit_of_measurement='meters'
    )
    
    material = RawMaterial.objects.create(
        material_name=f"Material_{unique_id}",
        material_type=material_type,
        unit_price=Decimal('50.00'),
        current_quantity=quantity
    )
    
    return material


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


def cleanup_material(material):
    """Helper to cleanup material test data"""
    material_type = material.material_type
    material.delete()
    material_type.delete()


class TestMaterialCalculation(TestCase):
    """
    Property 38: Material requirements calculation is correct
    
    Feature: complete-ecommerce-platform, Property 38: Material requirements calculation is correct
    Validates: Requirements 10.2
    
    For any order with multiple items, the total material requirements should
    equal the sum of (item_quantity × spec_quantity_required) for each material.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_items=st.integers(min_value=1, max_value=3),
        order_quantities=st.lists(
            st.integers(min_value=1, max_value=10),
            min_size=1,
            max_size=3
        ),
        spec_quantities=st.lists(
            st.decimals(min_value=1, max_value=50, places=2),
            min_size=1,
            max_size=3
        )
    )
    def test_material_requirements_calculation_is_correct(
        self, num_items, order_quantities, spec_quantities
    ):
        """
        For any order with multiple items, total material requirements should
        equal sum of (item_quantity × spec_quantity_required).
        """
        # Ensure we have matching quantities
        order_quantities = order_quantities[:num_items]
        spec_quantities = spec_quantities[:num_items]
        
        if len(order_quantities) < num_items:
            order_quantities.extend([1] * (num_items - len(order_quantities)))
        if len(spec_quantities) < num_items:
            spec_quantities.extend([Decimal('1.00')] * (num_items - len(spec_quantities)))
        
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
        
        # Create a shared material for all items
        material = create_test_material(quantity=Decimal('10000.00'))
        
        # Create variant sizes and manufacturing specs
        variant_sizes = []
        expected_total = Decimal('0.00')
        
        try:
            # Create order
            order = Order.objects.create(
                user=user,
                delivery_address=address,
                status='pending'
            )
            
            for i in range(num_items):
                variant_size = create_test_variant_size(stock_quantity=100)
                variant_sizes.append(variant_size)
                
                # Create manufacturing specification
                ManufacturingSpecification.objects.create(
                    variant_size=variant_size,
                    material=material,
                    quantity_required=spec_quantities[i]
                )
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    variant_size=variant_size,
                    quantity=order_quantities[i],
                    snapshot_unit_price=Decimal('550.00')
                )
                
                # Calculate expected total
                expected_total += spec_quantities[i] * order_quantities[i]
            
            # Calculate material requirements
            requirements = ManufacturingService.calculate_material_requirements(order)
            
            # Property: Should have exactly one material in requirements
            assert len(requirements) == 1, \
                f"Should have 1 material in requirements, got {len(requirements)}"
            
            # Property: Total quantity should match expected calculation
            material_id = material.id
            assert material_id in requirements, \
                f"Material {material_id} should be in requirements"
            
            calculated_quantity = requirements[material_id]['quantity']
            
            assert calculated_quantity == expected_total, \
                f"Total material requirement should be {expected_total}, got {calculated_quantity}"
            
            # Property: Specifications list should have correct number of entries
            specs_list = requirements[material_id]['specifications']
            assert len(specs_list) == num_items, \
                f"Should have {num_items} specifications, got {len(specs_list)}"
            
            # Property: Each specification should have correct calculation
            for i, spec_entry in enumerate(specs_list):
                expected_item_total = spec_quantities[i] * order_quantities[i]
                assert spec_entry['total'] == expected_item_total, \
                    f"Spec {i} total should be {expected_item_total}, got {spec_entry['total']}"
            
        finally:
            # Cleanup
            order.delete()
            user.delete()
            cleanup_address(address)
            cleanup_material(material)
            for vs in variant_sizes:
                cleanup_variant_size(vs)


class TestMaterialConsumption(TestCase):
    """
    Property 39: Material consumption decreases inventory
    
    Feature: complete-ecommerce-platform, Property 39: Material consumption decreases inventory
    Validates: Requirements 10.3
    
    For any material consumption operation, the raw material current_quantity
    should decrease by the consumed amount.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        initial_quantity=st.decimals(min_value=100, max_value=1000, places=2),
        order_quantity=st.integers(min_value=1, max_value=5),
        spec_quantity=st.decimals(min_value=1, max_value=10, places=2)
    )
    def test_material_consumption_decreases_inventory(
        self, initial_quantity, order_quantity, spec_quantity
    ):
        """
        For any material consumption, current_quantity should decrease by
        the consumed amount.
        """
        # Ensure we have enough material
        consumed_amount = spec_quantity * order_quantity
        assume(initial_quantity >= consumed_amount)
        
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
        
        # Create material with initial quantity
        material = create_test_material(quantity=initial_quantity)
        
        # Create variant size
        variant_size = create_test_variant_size(stock_quantity=100)
        
        try:
            # Create manufacturing specification
            ManufacturingSpecification.objects.create(
                variant_size=variant_size,
                material=material,
                quantity_required=spec_quantity
            )
            
            # Create order
            order = Order.objects.create(
                user=user,
                delivery_address=address,
                status='pending'
            )
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                variant_size=variant_size,
                quantity=order_quantity,
                snapshot_unit_price=Decimal('550.00')
            )
            
            # Record initial quantity
            initial_qty = material.current_quantity
            
            # Consume materials
            consumed = ManufacturingService.consume_materials_for_order(order)
            
            # Refresh material from database
            material.refresh_from_db()
            
            # Property: current_quantity should decrease by consumed amount
            expected_final = initial_qty - consumed_amount
            assert material.current_quantity == expected_final, \
                f"Material quantity should be {expected_final}, got {material.current_quantity}"
            
            # Property: consumed dict should contain correct material and quantity
            assert material.id in consumed, \
                f"Material {material.id} should be in consumed dict"
            
            assert consumed[material.id] == consumed_amount, \
                f"Consumed amount should be {consumed_amount}, got {consumed[material.id]}"
            
            # Property: Difference should equal consumed amount
            actual_decrease = initial_qty - material.current_quantity
            assert actual_decrease == consumed_amount, \
                f"Actual decrease {actual_decrease} should equal consumed {consumed_amount}"
            
        finally:
            # Cleanup
            order.delete()
            user.delete()
            cleanup_address(address)
            cleanup_material(material)
            cleanup_variant_size(variant_size)


class TestMaterialAggregation(TestCase):
    """
    Property 60: Material requirements aggregation is correct
    
    Feature: complete-ecommerce-platform, Property 60: Material requirements aggregation is correct
    Validates: Requirements 15.2
    
    For any order with multiple items using the same material, the total
    requirement should be the sum of individual requirements.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_items=st.integers(min_value=2, max_value=4),
        order_quantities=st.lists(
            st.integers(min_value=1, max_value=5),
            min_size=2,
            max_size=4
        ),
        spec_quantities=st.lists(
            st.decimals(min_value=1, max_value=20, places=2),
            min_size=2,
            max_size=4
        )
    )
    def test_material_requirements_aggregation_is_correct(
        self, num_items, order_quantities, spec_quantities
    ):
        """
        For any order with multiple items using the same material, total
        requirement should be sum of individual requirements.
        """
        # Ensure we have matching quantities
        order_quantities = order_quantities[:num_items]
        spec_quantities = spec_quantities[:num_items]
        
        if len(order_quantities) < num_items:
            order_quantities.extend([1] * (num_items - len(order_quantities)))
        if len(spec_quantities) < num_items:
            spec_quantities.extend([Decimal('1.00')] * (num_items - len(spec_quantities)))
        
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
        
        # Create a SINGLE shared material for all items
        material = create_test_material(quantity=Decimal('10000.00'))
        
        # Create variant sizes
        variant_sizes = []
        individual_requirements = []
        
        try:
            # Create order
            order = Order.objects.create(
                user=user,
                delivery_address=address,
                status='pending'
            )
            
            for i in range(num_items):
                variant_size = create_test_variant_size(stock_quantity=100)
                variant_sizes.append(variant_size)
                
                # Create manufacturing specification using the SAME material
                ManufacturingSpecification.objects.create(
                    variant_size=variant_size,
                    material=material,
                    quantity_required=spec_quantities[i]
                )
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    variant_size=variant_size,
                    quantity=order_quantities[i],
                    snapshot_unit_price=Decimal('550.00')
                )
                
                # Track individual requirement
                individual_req = spec_quantities[i] * order_quantities[i]
                individual_requirements.append(individual_req)
            
            # Calculate material requirements
            requirements = ManufacturingService.calculate_material_requirements(order)
            
            # Property: Should have exactly ONE material (aggregated)
            assert len(requirements) == 1, \
                f"Should have 1 aggregated material, got {len(requirements)}"
            
            # Property: The material should be our shared material
            assert material.id in requirements, \
                f"Material {material.id} should be in requirements"
            
            # Property: Total should equal sum of individual requirements
            expected_total = sum(individual_requirements)
            calculated_total = requirements[material.id]['quantity']
            
            assert calculated_total == expected_total, \
                f"Aggregated total should be {expected_total}, got {calculated_total}"
            
            # Property: Sum of specification totals should equal aggregated total
            specs_list = requirements[material.id]['specifications']
            specs_sum = sum(spec['total'] for spec in specs_list)
            
            assert specs_sum == expected_total, \
                f"Sum of spec totals {specs_sum} should equal expected {expected_total}"
            
            # Property: Each individual requirement should be preserved in specs
            for i, spec_entry in enumerate(specs_list):
                assert spec_entry['total'] == individual_requirements[i], \
                    f"Spec {i} should preserve individual requirement {individual_requirements[i]}"
            
        finally:
            # Cleanup
            order.delete()
            user.delete()
            cleanup_address(address)
            cleanup_material(material)
            for vs in variant_sizes:
                cleanup_variant_size(vs)



class TestMaterialQuantityUpdates(TestCase):
    """
    Property 54: Material quantity updates include timestamp
    
    Feature: complete-ecommerce-platform, Property 54: Material quantity updates include timestamp
    Validates: Requirements 13.3
    
    For any material quantity update, the last_updated timestamp should be
    set to the current time.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        initial_quantity=st.decimals(min_value=0, max_value=1000, places=2),
        new_quantity=st.decimals(min_value=0, max_value=1000, places=2)
    )
    def test_material_quantity_updates_include_timestamp(
        self, initial_quantity, new_quantity
    ):
        """
        For any material quantity update, last_updated should be set to
        current time.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Create material with initial quantity
        material = create_test_material(quantity=initial_quantity)
        
        try:
            # Record the initial last_updated timestamp
            initial_timestamp = material.last_updated
            
            # Wait a tiny bit to ensure timestamp difference
            # (In real scenarios, there would be time between operations)
            import time
            time.sleep(0.01)
            
            # Update the quantity
            material.current_quantity = new_quantity
            material.save()
            
            # Refresh from database
            material.refresh_from_db()
            
            # Property: last_updated should be updated
            assert material.last_updated > initial_timestamp, \
                f"last_updated should be updated from {initial_timestamp} to {material.last_updated}"
            
            # Property: last_updated should be recent (within last minute)
            now = timezone.now()
            time_diff = now - material.last_updated
            assert time_diff < timedelta(minutes=1), \
                f"last_updated should be recent, but was {time_diff} ago"
            
            # Property: current_quantity should reflect the new value
            assert material.current_quantity == new_quantity, \
                f"current_quantity should be {new_quantity}, got {material.current_quantity}"
            
        finally:
            # Cleanup
            cleanup_material(material)


class TestReorderAlerts(TestCase):
    """
    Property 56: Reorder alerts highlight low materials
    
    Feature: complete-ecommerce-platform, Property 56: Reorder alerts highlight low materials
    Validates: Requirements 13.5
    
    For any material with current_quantity < reorder_level, the material
    should be flagged in the inventory view.
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        current_quantity=st.decimals(min_value=0, max_value=100, places=2),
        reorder_level=st.decimals(min_value=0, max_value=200, places=2)
    )
    def test_reorder_alerts_highlight_low_materials(
        self, current_quantity, reorder_level
    ):
        """
        For any material with current_quantity < reorder_level, the material
        should appear in reorder alerts.
        """
        # Create material
        material = create_test_material(quantity=current_quantity)
        
        # Create supplier
        unique_id = uuid.uuid4().hex[:6]
        supplier = Supplier.objects.create(
            supplier_name=f"Supplier_{unique_id}",
            contact_person="Test Contact",
            email=f"supplier_{unique_id}@example.com"
        )
        
        try:
            # Create material-supplier association with reorder level
            MaterialSupplier.objects.create(
                material=material,
                supplier=supplier,
                supplier_price=Decimal('45.00'),
                min_order_quantity=Decimal('100.00'),
                reorder_level=reorder_level,
                lead_time_days=7,
                is_preferred=True
            )
            
            # Get reorder alerts
            alerts = ManufacturingService.get_reorder_alerts()
            
            # Property: If current_quantity < reorder_level, material should be in alerts
            is_below_reorder = current_quantity < reorder_level
            material_in_alerts = any(alert['material_id'] == material.id for alert in alerts)
            
            if is_below_reorder:
                assert material_in_alerts, \
                    f"Material with quantity {current_quantity} < reorder level {reorder_level} " \
                    f"should be in alerts"
                
                # Find the alert for this material
                alert = next(a for a in alerts if a['material_id'] == material.id)
                
                # Property: Alert should have correct shortage calculation
                expected_shortage = reorder_level - current_quantity
                assert alert['shortage'] == expected_shortage, \
                    f"Shortage should be {expected_shortage}, got {alert['shortage']}"
                
                # Property: Alert should have correct current_quantity
                assert alert['current_quantity'] == current_quantity, \
                    f"Alert current_quantity should be {current_quantity}, got {alert['current_quantity']}"
                
                # Property: Alert should have correct reorder_level
                assert alert['reorder_level'] == reorder_level, \
                    f"Alert reorder_level should be {reorder_level}, got {alert['reorder_level']}"
                
                # Property: Alert should include preferred supplier info
                assert alert['preferred_supplier'] is not None, \
                    "Alert should include preferred supplier info"
                
                assert alert['preferred_supplier']['supplier_name'] == supplier.supplier_name, \
                    f"Preferred supplier should be {supplier.supplier_name}"
            else:
                # Property: If current_quantity >= reorder_level, material should NOT be in alerts
                assert not material_in_alerts, \
                    f"Material with quantity {current_quantity} >= reorder level {reorder_level} " \
                    f"should NOT be in alerts"
            
        finally:
            # Cleanup
            supplier.delete()
            cleanup_material(material)
