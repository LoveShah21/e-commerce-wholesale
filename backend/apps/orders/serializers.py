from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem
from apps.products.serializers import VariantSizeSerializer

# Nested serializers for order tracking
class CountrySerializer(serializers.Serializer):
    country_name = serializers.CharField()

class StateSerializer(serializers.Serializer):
    state_name = serializers.CharField()
    country = CountrySerializer()

class CitySerializer(serializers.Serializer):
    city_name = serializers.CharField()
    state = StateSerializer()

class PostalCodeSerializer(serializers.Serializer):
    postal_code = serializers.CharField()
    city = CitySerializer()

class OrderAddressSerializer(serializers.Serializer):
    """Enhanced address serializer for order tracking with nested structure"""
    address_line_1 = serializers.CharField(source='address_line1')
    address_line_2 = serializers.CharField(source='address_line2')
    city = CitySerializer(source='postal_code.city')
    state = StateSerializer(source='postal_code.city.state')
    postal_code = PostalCodeSerializer()
    country = CountrySerializer(source='postal_code.city.state.country')

class ProductSerializer(serializers.Serializer):
    product_name = serializers.CharField()

class FabricSerializer(serializers.Serializer):
    fabric_name = serializers.CharField()

class ColorSerializer(serializers.Serializer):
    color_name = serializers.CharField()

class SizeSerializer(serializers.Serializer):
    size_code = serializers.CharField()

class VariantSerializer(serializers.Serializer):
    product = ProductSerializer()
    fabric = FabricSerializer()
    color = ColorSerializer()

class OrderVariantSizeSerializer(serializers.Serializer):
    """Enhanced variant size serializer for order tracking"""
    variant = VariantSerializer()
    size = SizeSerializer()

class CartItemSerializer(serializers.ModelSerializer):
    variant_details = VariantSizeSerializer(source='variant_size', read_only=True)
    
    class Meta:
        model = CartItem
        fields = ('id', 'variant_size', 'quantity', 'variant_details')

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ('id', 'status', 'items', 'total_price')

    def get_total_price(self, obj):
        total = 0
        for item in obj.items.all():
            price = item.variant_size.variant.base_price * (1 + item.variant_size.size.size_markup_percentage / 100)
            total += price * item.quantity
        return total

class OrderItemSerializer(serializers.ModelSerializer):
    variant_size = OrderVariantSizeSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'variant_size', 'quantity', 'snapshot_unit_price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    delivery_address = OrderAddressSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='order_date', read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'created_at', 'order_date', 'status', 'delivery_address', 'items', 'notes', 'total_amount')
        read_only_fields = ('user', 'order_date', 'status')
    
    def get_total_amount(self, obj):
        """Calculate total amount from order items"""
        total = 0
        for item in obj.items.all():
            total += item.snapshot_unit_price * item.quantity
        return total

class OrderCreateSerializer(serializers.Serializer):
    delivery_address_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.filter(user=user, status='active').first()
        if not cart or not cart.items.exists():
            raise serializers.ValidationError("Cart is empty")
            
        delivery_address_id = validated_data['delivery_address_id']
        
        # Create Order (Signal will check stock? No, Signal reserves stock on OrderItem save)
        # But we need to ensure feasibility first? 
        # For this MVP, we rely on signals or service checks.
        # Let's use transaction
        from django.db import transaction
        from apps.users.models import Address
        from apps.manufacturing.services import ManufacturingService
        
        try:
            address = Address.objects.get(id=delivery_address_id, user=user)
        except Address.DoesNotExist:
            raise serializers.ValidationError("Invalid address")

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                delivery_address=address,
                notes=validated_data.get('notes', '')
            )
            
            for cart_item in cart.items.all():
                # Calculate price
                variant = cart_item.variant_size.variant
                markup = cart_item.variant_size.size.size_markup_percentage
                price = variant.base_price * (1 + markup / 100)
                
                OrderItem.objects.create(
                    order=order,
                    variant_size=cart_item.variant_size,
                    quantity=cart_item.quantity,
                    snapshot_unit_price=price
                )
                
            # Close Cart
            cart.status = 'checked_out'
            cart.save()
            
            # Initiate payment logic here (not implemented yet)
            
            return order
