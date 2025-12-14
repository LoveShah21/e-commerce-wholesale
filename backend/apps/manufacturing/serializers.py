from rest_framework import serializers
from .models import RawMaterial, MaterialType, Supplier, MaterialSupplier, ManufacturingSpecification
from apps.products.models import VariantSize
from decimal import Decimal


class MaterialTypeSerializer(serializers.ModelSerializer):
    """Serializer for MaterialType model."""
    
    class Meta:
        model = MaterialType
        fields = ('id', 'material_type_name', 'unit_of_measurement', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model."""
    city_name = serializers.CharField(source='city.city_name', read_only=True)
    
    class Meta:
        model = Supplier
        fields = ('id', 'supplier_name', 'contact_person', 'email', 'phone', 'city', 'city_name', 'created_at')
        read_only_fields = ('id', 'created_at')


class SupplierCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Supplier."""
    
    class Meta:
        model = Supplier
        fields = ('id', 'supplier_name', 'contact_person', 'email', 'phone', 'city', 'created_at')
        read_only_fields = ('id', 'created_at')


class RawMaterialSerializer(serializers.ModelSerializer):
    """Serializer for RawMaterial model with related data."""
    material_type_name = serializers.CharField(source='material_type.material_type_name', read_only=True)
    unit_of_measurement = serializers.CharField(source='material_type.unit_of_measurement', read_only=True)
    is_below_reorder = serializers.SerializerMethodField()
    reorder_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RawMaterial
        fields = (
            'id', 'material_name', 'material_type', 'material_type_name', 
            'unit_of_measurement', 'unit_price', 'current_quantity', 
            'is_below_reorder', 'reorder_info', 'created_at', 'last_updated'
        )
        read_only_fields = ('id', 'created_at', 'last_updated')
    
    def get_is_below_reorder(self, obj):
        """Check if material is below any reorder level."""
        material_suppliers = MaterialSupplier.objects.filter(
            material=obj,
            reorder_level__isnull=False
        )
        
        for ms in material_suppliers:
            if obj.current_quantity < ms.reorder_level:
                return True
        return False
    
    def get_reorder_info(self, obj):
        """Get reorder information if below threshold."""
        material_suppliers = MaterialSupplier.objects.filter(
            material=obj,
            reorder_level__isnull=False
        ).select_related('supplier')
        
        for ms in material_suppliers:
            if obj.current_quantity < ms.reorder_level:
                preferred = MaterialSupplier.objects.filter(
                    material=obj,
                    is_preferred=True
                ).select_related('supplier').first()
                
                return {
                    'reorder_level': ms.reorder_level,
                    'shortage': ms.reorder_level - obj.current_quantity,
                    'preferred_supplier': {
                        'id': preferred.supplier.id,
                        'name': preferred.supplier.supplier_name,
                        'price': preferred.supplier_price,
                        'min_order_qty': preferred.min_order_quantity,
                        'lead_time_days': preferred.lead_time_days
                    } if preferred else None
                }
        return None


class RawMaterialCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating RawMaterial."""
    
    class Meta:
        model = RawMaterial
        fields = ('id', 'material_name', 'material_type', 'unit_price', 'current_quantity', 'created_at', 'last_updated')
        read_only_fields = ('id', 'created_at', 'last_updated')
    
    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative")
        return value
    
    def validate_current_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Current quantity cannot be negative")
        return value


class RawMaterialUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating RawMaterial."""
    
    class Meta:
        model = RawMaterial
        fields = ('material_name', 'unit_price', 'current_quantity')
    
    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative")
        return value
    
    def validate_current_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Current quantity cannot be negative")
        return value


class MaterialQuantityUpdateSerializer(serializers.Serializer):
    """Serializer for updating material quantity."""
    current_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    
    def validate_current_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Current quantity cannot be negative")
        return value


class MaterialSupplierSerializer(serializers.ModelSerializer):
    """Serializer for MaterialSupplier model with related data."""
    material_name = serializers.CharField(source='material.material_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.supplier_name', read_only=True)
    material_type = serializers.CharField(source='material.material_type.material_type_name', read_only=True)
    
    class Meta:
        model = MaterialSupplier
        fields = (
            'id', 'material', 'material_name', 'material_type', 'supplier', 
            'supplier_name', 'supplier_price', 'min_order_quantity', 
            'reorder_level', 'lead_time_days', 'is_preferred', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class MaterialSupplierCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MaterialSupplier association."""
    
    class Meta:
        model = MaterialSupplier
        fields = (
            'id', 'material', 'supplier', 'supplier_price', 'min_order_quantity',
            'reorder_level', 'lead_time_days', 'is_preferred', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
    
    def validate_supplier_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Supplier price cannot be negative")
        return value
    
    def validate_min_order_quantity(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Minimum order quantity cannot be negative")
        return value
    
    def validate_reorder_level(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Reorder level cannot be negative")
        return value
    
    def validate_lead_time_days(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Lead time cannot be negative")
        return value


class ManufacturingSpecificationSerializer(serializers.ModelSerializer):
    """Serializer for ManufacturingSpecification model."""
    material_name = serializers.CharField(source='material.material_name', read_only=True)
    variant_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ManufacturingSpecification
        fields = (
            'id', 'variant_size', 'variant_info', 'material', 'material_name',
            'quantity_required', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
    
    def get_variant_info(self, obj):
        variant = obj.variant_size.variant
        return {
            'product_name': variant.product.product_name,
            'size': obj.variant_size.size.size_name,
            'sku': variant.sku
        }


class ManufacturingSpecificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ManufacturingSpecification."""
    
    class Meta:
        model = ManufacturingSpecification
        fields = ('variant_size', 'material', 'quantity_required')
    
    def validate_quantity_required(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity required must be positive")
        return value


class InventoryViewSerializer(serializers.Serializer):
    """Serializer for inventory view with reorder alerts."""
    material_id = serializers.IntegerField()
    material_name = serializers.CharField()
    material_type = serializers.CharField()
    unit_of_measurement = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_below_reorder = serializers.BooleanField()
    reorder_level = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    shortage = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    preferred_supplier = serializers.DictField(allow_null=True)
    last_updated = serializers.DateTimeField()
