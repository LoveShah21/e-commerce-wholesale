from django.db import models
from apps.users.models import User, Address
from apps.products.models import VariantSize

class Cart(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('checked_out', 'Checked Out'),
        ('abandoned', 'Abandoned'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    guest_email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} - {self.user if self.user else self.guest_email}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant_size = models.ForeignKey(VariantSize, on_delete=models.RESTRICT)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'variant_size')

    def __str__(self):
        return f"{self.quantity} x {self.variant_size} in Cart {self.cart.id}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    delivery_address = models.ForeignKey(Address, on_delete=models.RESTRICT)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant_size = models.ForeignKey(VariantSize, on_delete=models.RESTRICT)
    quantity = models.IntegerField()
    snapshot_unit_price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of order
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def line_total(self):
        """Calculate line total (quantity * unit price)"""
        return self.snapshot_unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.variant_size} in Order #{self.order.id}"
