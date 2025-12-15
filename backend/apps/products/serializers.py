from rest_framework import serializers
from .models import (
    Product, ProductVariant, VariantSize, Fabric, Color, Pattern, 
    ProductImage, Stock, Size, Sleeve, Pocket
)
from services.utils import generate_sku
from utils.security import validate_image_file, sanitize_filename


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image_url', 'alt_text', 'is_primary', 'display_order')


class ProductImageCreateSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False)
    
    class Meta:
        model = ProductImage
        fields = ('image_url', 'image_file', 'alt_text', 'is_primary', 'display_order')
    
    def validate_image_file(self, value):
        """Validate uploaded image file."""
        if value:
            validate_image_file(value)
            # Sanitize filename
            value.name = sanitize_filename(value.name)
        return value


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ('quantity_in_stock', 'quantity_reserved', 'quantity_available', 'last_updated')
        read_only_fields = ('quantity_available', 'last_updated')


class VariantSizeSerializer(serializers.ModelSerializer):
    size_code = serializers.CharField(source='size.size_code', read_only=True)
    size_name = serializers.CharField(source='size.size_name', read_only=True)
    final_price = serializers.SerializerMethodField()
    stock_available = serializers.SerializerMethodField()
    stock_info = serializers.SerializerMethodField()
    
    class Meta:
        model = VariantSize
        fields = ('id', 'size', 'size_code', 'size_name', 'stock_quantity', 'final_price', 'stock_available', 'stock_info')
        read_only_fields = ('id',)

    def get_final_price(self, obj):
        # Base price + Markup
        base = obj.variant.base_price
        markup = obj.size.size_markup_percentage
        return base * (1 + markup / 100)
        
    def get_stock_available(self, obj):
        if hasattr(obj, 'stock_record'):
            return obj.stock_record.quantity_available
        return 0
    
    def get_stock_info(self, obj):
        if hasattr(obj, 'stock_record'):
            return {
                'in_stock': obj.stock_record.quantity_in_stock,
                'reserved': obj.stock_record.quantity_reserved,
                'available': obj.stock_record.quantity_available
            }
        return None


class VariantSizeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantSize
        fields = ('size', 'stock_quantity')


class ProductVariantSerializer(serializers.ModelSerializer):
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    color_name = serializers.CharField(source='color.color_name', read_only=True)
    pattern_name = serializers.CharField(source='pattern.pattern_name', read_only=True)
    sleeve_type = serializers.CharField(source='sleeve.sleeve_type', read_only=True)
    pocket_type = serializers.CharField(source='pocket.pocket_type', read_only=True)
    sizes = VariantSizeSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = ('sku', 'created_at')


class ProductVariantCreateSerializer(serializers.ModelSerializer):
    sizes = VariantSizeCreateSerializer(many=True, required=False)
    
    class Meta:
        model = ProductVariant
        fields = ('fabric', 'color', 'pattern', 'sleeve', 'pocket', 'base_price', 'sizes')
    
    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', [])
        
        # Generate SKU if not provided
        if not validated_data.get('sku'):
            validated_data['sku'] = generate_sku('SHIRT')
        
        variant = ProductVariant.objects.create(**validated_data)
        
        # Create sizes if provided
        for size_data in sizes_data:
            variant_size = VariantSize.objects.create(variant=variant, **size_data)
            # Create stock record
            Stock.objects.create(
                variant_size=variant_size,
                quantity_in_stock=size_data.get('stock_quantity', 0)
            )
        
        return variant


class ProductVariantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ('fabric', 'color', 'pattern', 'sleeve', 'pocket', 'base_price')


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'


class ProductCreateSerializer(serializers.ModelSerializer):
    images = ProductImageCreateSerializer(many=True, required=False)
    variants = ProductVariantCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = ('product_name', 'description', 'images', 'variants')
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        
        product = Product.objects.create(**validated_data)
        
        # Create images
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        
        # Create variants
        for variant_data in variants_data:
            sizes_data = variant_data.pop('sizes', [])
            
            # Generate SKU
            if not variant_data.get('sku'):
                variant_data['sku'] = generate_sku('SHIRT')
            
            variant = ProductVariant.objects.create(product=product, **variant_data)
            
            # Create sizes
            for size_data in sizes_data:
                variant_size = VariantSize.objects.create(variant=variant, **size_data)
                # Create stock record
                Stock.objects.create(
                    variant_size=variant_size,
                    quantity_in_stock=size_data.get('stock_quantity', 0)
                )
        
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('product_name', 'description')


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


class StockUpdateSerializer(serializers.Serializer):
    quantity_in_stock = serializers.IntegerField(min_value=0, required=False)
    quantity_reserved = serializers.IntegerField(min_value=0, required=False)
