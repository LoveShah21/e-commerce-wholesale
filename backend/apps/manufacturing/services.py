from .models import ManufacturingSpecification, RawMaterial
from apps.products.models import VariantSize
from django.db import transaction
from django.core.exceptions import ValidationError

class ManufacturingService:
    @staticmethod
    def calculate_material_usage(order):
        """
        Calculate total material requirements for a given order.
        Returns a dictionary of material_id -> quantity_required.
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
                else:
                    material_requirements[material_id] = {
                        'material': spec.material,
                        'quantity': required_qty
                    }
        
        return material_requirements

    @staticmethod
    def check_production_feasibility(order):
        """
        Check if we have enough raw materials to produce the order.
        Returns (bool, list_of_missing_materials).
        """
        requirements = ManufacturingService.calculate_material_usage(order)
        missing_materials = []
        is_feasible = True
        
        for mat_id, data in requirements.items():
            material = data['material']
            required_qty = data['quantity']
            
            if material.current_quantity < required_qty:
                is_feasible = False
                missing_materials.append({
                    'material_name': material.material_name,
                    'required': required_qty,
                    'available': material.current_quantity
                })
                
        return is_feasible, missing_materials

    @staticmethod
    @transaction.atomic
    def deduct_raw_materials(order):
        """
        Deduct raw materials from inventory for an order production.
        Raises ValidationError if insufficient stock.
        """
        feasible, missing = ManufacturingService.check_production_feasibility(order)
        if not feasible:
            raise ValidationError(f"Insufficient raw materials: {missing}")
            
        requirements = ManufacturingService.calculate_material_usage(order)
        for mat_id, data in requirements.items():
            material = data['material']
            material.current_quantity -= data['quantity']
            material.save()
            
        return True
