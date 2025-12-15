from django.db import models

class Fabric(models.Model):
    fabric_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fabric_name

class Color(models.Model):
    color_name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.color_name

class Pattern(models.Model):
    pattern_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pattern_name

class Sleeve(models.Model):
    sleeve_type = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sleeve_type

class Pocket(models.Model):
    pocket_type = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pocket_type

class Size(models.Model):
    size_code = models.CharField(max_length=10, unique=True)
    size_name = models.CharField(max_length=50)
    size_markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.size_code

class Product(models.Model):
    product_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name
    
    @property
    def is_in_stock(self):
        """Check if any variant has available stock"""
        for variant in self.variants.all():
            for vsize in variant.sizes.all():
                if hasattr(vsize, 'stock_record') and vsize.stock_record:
                    if vsize.stock_record.quantity_available > 0:
                        return True
        return False

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=200, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    fabric = models.ForeignKey(Fabric, on_delete=models.RESTRICT)
    color = models.ForeignKey(Color, on_delete=models.RESTRICT)
    pattern = models.ForeignKey(Pattern, on_delete=models.RESTRICT)
    sleeve = models.ForeignKey(Sleeve, on_delete=models.RESTRICT)
    pocket = models.ForeignKey(Pocket, on_delete=models.RESTRICT)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'fabric', 'color', 'pattern', 'sleeve', 'pocket')

    def __str__(self):
        return f"{self.product.product_name} - {self.color.color_name} {self.pattern.pattern_name}"

class VariantSize(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='sizes')
    size = models.ForeignKey(Size, on_delete=models.RESTRICT)
    stock_quantity = models.IntegerField(default=0) # Total physical stock
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('variant', 'size')

    def __str__(self):
        return f"{self.variant} - {self.size.size_code}"

class Stock(models.Model):
    variant_size = models.OneToOneField(VariantSize, on_delete=models.CASCADE, related_name='stock_record')
    quantity_in_stock = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    # helper to get available
    @property
    def quantity_available(self):
        return self.quantity_in_stock - self.quantity_reserved

    def __str__(self):
        return f"Stock for {self.variant_size}: {self.quantity_available}"
