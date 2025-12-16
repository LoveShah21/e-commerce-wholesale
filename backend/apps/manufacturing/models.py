from django.db import models
from apps.products.models import VariantSize
from apps.users.models import City

class MaterialType(models.Model):
    material_type_name = models.CharField(max_length=50, unique=True)
    unit_of_measurement = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.material_type_name

class Supplier(models.Model):
    supplier_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_name

class RawMaterial(models.Model):
    material_name = models.CharField(max_length=100)
    material_type = models.ForeignKey(MaterialType, on_delete=models.RESTRICT)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_reorder_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Default minimum stock level for reorder alerts")
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('material_name', 'material_type')

    def __str__(self):
        return self.material_name

class MaterialSupplier(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    supplier_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lead_time_days = models.IntegerField(null=True, blank=True)
    is_preferred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('material', 'supplier')

    def __str__(self):
        return f"{self.supplier.supplier_name} - {self.material.material_name}"

class ManufacturingSpecification(models.Model):
    variant_size = models.ForeignKey(VariantSize, on_delete=models.CASCADE)
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('variant_size', 'material')

    def __str__(self):
        return f"{self.variant_size} requires {self.quantity_required} of {self.material.material_name}"
