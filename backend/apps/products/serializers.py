from rest_framework import serializers
from .models import Product, ProductVariant, VariantSize, Fabric, Color, Pattern, ProductImage, Stock

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image_url', 'alt_text', 'is_primary', 'display_order')

class ProductVariantSerializer(serializers.ModelSerializer):
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    color_name = serializers.CharField(source='color.color_name', read_only=True)
    pattern_name = serializers.CharField(source='pattern.pattern_name', read_only=True)
    sleeve_type = serializers.CharField(source='sleeve.sleeve_type', read_only=True)
    pocket_type = serializers.CharField(source='pocket.pocket_type', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = '__all__'

class VariantSizeSerializer(serializers.ModelSerializer):
    size_code = serializers.CharField(source='size.size_code', read_only=True)
    final_price = serializers.SerializerMethodField()
    stock_available = serializers.SerializerMethodField()
    
    class Meta:
        model = VariantSize
        fields = ('id', 'size_code', 'stock_quantity', 'final_price', 'stock_available')

    def get_final_price(self, obj):
        # Base price + Markup
        base = obj.variant.base_price
        markup = obj.size.size_markup_percentage
        return base * (1 + markup / 100)
        
    def get_stock_available(self, obj):
        if hasattr(obj, 'stock_record'):
            return obj.stock_record.quantity_available
        return 0

class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ('id', 'product_name', 'primary_image', 'price_range', 'created_at')

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first()
        return img.image_url if img else None

    def get_price_range(self, obj):
        # Simplified: min price of variants
        variants = obj.variants.all()
        if not variants:
            return "N/A"
        prices = [v.base_price for v in variants]
        return f"{min(prices)}"
