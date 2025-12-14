from .models import ManufacturingSpecification, RawMaterial, MaterialSupplier
from apps.products.models import VariantSize
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ManufacturingService:
    """
    Service layer for manufacturing workflow management.
    
    Handles material requirements calculation, material consumption,
    reorder level alerts, and manufacturing specification management.
    """
    
    @staticmethod
    def calculate_material_requirements(order) -> Dict[int, Dict[str, Any]]:
        """
        Calculate total material requirements for a given order.
        
        Aggregates material requirements across all order items by summing
        the quantity_required from manufacturing specifications multiplied
        by the order item quantity.
        
        Args:
            order: Order instance
            
        Returns:
            Dictionary mapping material_id to:
                - material: RawMaterial instance
                - quantity: Total quantity required (Decimal)
                - specifications: List of (variant_size, spec_quantity, order_quantity)
        
        Validates: Requirements 10.2, 15.2
        """
        material_requirements = {}
        
        for order_item in order.items.all():
            variant_size = order_item.variant_size
            specs = ManufacturingSpecification.objects.filter(variant_size=variant_size)
            
            for spec in specs:
                material_id = spec.material.id
                required_qty = spec.quantity_required * order_item.quantity
                
                if material_id in material_requirements:
                    material_requirements[material_id]['quantity'] += required_qty
                    material_requirements[material_id]['specifications'].append({
                        'variant_size': variant_size,
                        'spec_quantity': spec.quantity_required,
                        'order_quantity': order_item.quantity,
                        'total': required_qty
                    })
                else:
                    material_requirements[material_id] = {
                        'material': spec.material,
                        'quantity': required_qty,
                        'specifications': [{
                            'variant_size': variant_size,
                            'spec_quantity': spec.quantity_required,
                            'order_quantity': order_item.quantity,
                            'total': required_qty
                        }]
                    }
        
        logger.info(f"Calculated material requirements for order {order.id}: "
                   f"{len(material_requirements)} unique materials")
        
        return material_requirements
    
    @staticmethod
    def calculate_material_usage(order) -> Dict[int, Dict[str, Any]]:
        """
        Alias for calculate_material_requirements for backward compatibility.
        """
        return ManufacturingService.calculate_material_requirements(order)

    @staticmethod
    def check_production_feasibility(order) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if we have enough raw materials to produce the order.
        
        Args:
            order: Order instance
            
        Returns:
            Tuple of (is_feasible: bool, missing_materials: list)
            missing_materials contains dicts with material_name, required, available
        
        Validates: Requirements 10.4
        """
        requirements = ManufacturingService.calculate_material_requirements(order)
        missing_materials = []
        is_feasible = True
        
        for mat_id, data in requirements.items():
            material = data['material']
            required_qty = data['quantity']
            
            if material.current_quantity < required_qty:
                is_feasible = False
                missing_materials.append({
                    'material_id': material.id,
                    'material_name': material.material_name,
                    'required': required_qty,
                    'available': material.current_quantity,
                    'shortage': required_qty - material.current_quantity
                })
        
        if not is_feasible:
            logger.warning(f"Order {order.id} is not feasible: {len(missing_materials)} materials short")
        
        return is_feasible, missing_materials

    @staticmethod
    @transaction.atomic
    def consume_materials_for_order(order) -> Dict[int, Decimal]:
        """
        Deduct raw materials from inventory for an order production.
        
        This is an atomic operation - either all materials are consumed
        or none are (transaction rollback on failure).
        
        Args:
            order: Order instance
            
        Returns:
            Dictionary mapping material_id to quantity consumed
            
        Raises:
            ValidationError: If insufficient materials are available
            
        Validates: Requirements 10.3
        """
        feasible, missing = ManufacturingService.check_production_feasibility(order)
        if not feasible:
            error_msg = "Insufficient raw materials: " + ", ".join([
                f"{m['material_name']} (need {m['required']}, have {m['available']})"
                for m in missing
            ])
            logger.error(f"Cannot consume materials for order {order.id}: {error_msg}")
            raise ValidationError(error_msg)
        
        requirements = ManufacturingService.calculate_material_requirements(order)
        consumed = {}
        
        for mat_id, data in requirements.items():
            material = data['material']
            quantity_to_consume = data['quantity']
            
            # Deduct from inventory
            material.current_quantity -= quantity_to_consume
            material.save()
            
            consumed[mat_id] = quantity_to_consume
            
            logger.info(f"Consumed {quantity_to_consume} of {material.material_name} "
                       f"for order {order.id}")
        
        logger.info(f"Successfully consumed materials for order {order.id}: "
                   f"{len(consumed)} materials")
        
        return consumed
    
    @staticmethod
    @transaction.atomic
    def deduct_raw_materials(order) -> bool:
        """
        Alias for consume_materials_for_order for backward compatibility.
        
        Returns True on success, raises ValidationError on failure.
        """
        ManufacturingService.consume_materials_for_order(order)
        return True
    
    @staticmethod
    def get_reorder_alerts() -> List[Dict[str, Any]]:
        """
        Get list of materials that are below their reorder level.
        
        Returns materials where current_quantity is below the reorder_level
        defined in any MaterialSupplier relationship.
        
        Returns:
            List of dictionaries containing:
                - material: RawMaterial instance
                - current_quantity: Current inventory level
                - reorder_level: Minimum threshold
                - shortage: How much below threshold
                - preferred_supplier: Preferred supplier info (if any)
                
        Validates: Requirements 10.4
        """
        alerts = []
        
        # Get all materials with supplier relationships
        material_suppliers = MaterialSupplier.objects.select_related(
            'material', 'supplier'
        ).filter(
            reorder_level__isnull=False
        )
        
        # Track materials we've already processed
        processed_materials = set()
        
        for ms in material_suppliers:
            material = ms.material
            
            # Skip if we've already processed this material
            if material.id in processed_materials:
                continue
            
            # Check if below reorder level
            if material.current_quantity < ms.reorder_level:
                # Get preferred supplier if exists
                preferred_supplier = MaterialSupplier.objects.filter(
                    material=material,
                    is_preferred=True
                ).select_related('supplier').first()
                
                alert = {
                    'material': material,
                    'material_id': material.id,
                    'material_name': material.material_name,
                    'current_quantity': material.current_quantity,
                    'reorder_level': ms.reorder_level,
                    'shortage': ms.reorder_level - material.current_quantity,
                    'unit_price': material.unit_price,
                }
                
                if preferred_supplier:
                    alert['preferred_supplier'] = {
                        'supplier_id': preferred_supplier.supplier.id,
                        'supplier_name': preferred_supplier.supplier.supplier_name,
                        'supplier_price': preferred_supplier.supplier_price,
                        'min_order_quantity': preferred_supplier.min_order_quantity,
                        'lead_time_days': preferred_supplier.lead_time_days,
                    }
                else:
                    alert['preferred_supplier'] = None
                
                alerts.append(alert)
                processed_materials.add(material.id)
        
        logger.info(f"Found {len(alerts)} materials below reorder level")
        
        return alerts
    
    @staticmethod
    @transaction.atomic
    def create_manufacturing_specification(
        variant_size_id: int,
        material_id: int,
        quantity_required: Decimal
    ) -> ManufacturingSpecification:
        """
        Create a manufacturing specification linking a variant size to required materials.
        
        Args:
            variant_size_id: ID of the VariantSize
            material_id: ID of the RawMaterial
            quantity_required: Quantity of material needed per unit
            
        Returns:
            ManufacturingSpecification instance
            
        Raises:
            ValidationError: If variant_size or material doesn't exist,
                           or if specification already exists
                           
        Validates: Requirements 10.1
        """
        try:
            variant_size = VariantSize.objects.get(id=variant_size_id)
        except VariantSize.DoesNotExist:
            raise ValidationError(f"VariantSize with id {variant_size_id} does not exist")
        
        try:
            material = RawMaterial.objects.get(id=material_id)
        except RawMaterial.DoesNotExist:
            raise ValidationError(f"RawMaterial with id {material_id} does not exist")
        
        # Check if specification already exists
        existing = ManufacturingSpecification.objects.filter(
            variant_size=variant_size,
            material=material
        ).first()
        
        if existing:
            raise ValidationError(
                f"Manufacturing specification already exists for {variant_size} "
                f"and {material.material_name}"
            )
        
        spec = ManufacturingSpecification.objects.create(
            variant_size=variant_size,
            material=material,
            quantity_required=quantity_required
        )
        
        logger.info(f"Created manufacturing specification: {spec}")
        
        return spec
    
    @staticmethod
    def get_order_material_requirements(order_id: int) -> Dict[str, Any]:
        """
        Get detailed material requirements for a specific order.
        
        Args:
            order_id: ID of the Order
            
        Returns:
            Dictionary containing:
                - order_id: Order ID
                - requirements: List of material requirements with details
                - is_feasible: Whether order can be produced with current inventory
                - missing_materials: List of materials that are insufficient
                
        Validates: Requirements 10.5
        """
        from apps.orders.models import Order
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order with id {order_id} does not exist")
        
        requirements = ManufacturingService.calculate_material_requirements(order)
        is_feasible, missing = ManufacturingService.check_production_feasibility(order)
        
        requirements_list = []
        for mat_id, data in requirements.items():
            material = data['material']
            requirements_list.append({
                'material_id': material.id,
                'material_name': material.material_name,
                'material_type': material.material_type.material_type_name,
                'unit_of_measurement': material.material_type.unit_of_measurement,
                'required_quantity': data['quantity'],
                'available_quantity': material.current_quantity,
                'is_sufficient': material.current_quantity >= data['quantity'],
                'shortage': max(Decimal('0'), data['quantity'] - material.current_quantity),
                'specifications': data['specifications']
            })
        
        return {
            'order_id': order_id,
            'requirements': requirements_list,
            'is_feasible': is_feasible,
            'missing_materials': missing,
            'total_materials_count': len(requirements_list)
        }
