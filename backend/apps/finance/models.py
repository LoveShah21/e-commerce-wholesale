from django.db import models
from apps.orders.models import Order

class TaxConfiguration(models.Model):
    tax_name = models.CharField(max_length=50)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tax_name', 'effective_from')

    def __str__(self):
        return f"{self.tax_name} ({self.tax_percentage}%)"

class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('advance', 'Advance'),
        ('final', 'Final'),
        ('full', 'Full'),
    )
    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    PAYMENT_METHOD_CHOICES = (
         ('upi', 'UPI'),
         ('card', 'Card'),
         ('netbanking', 'Net Banking'),
         ('wallet', 'Wallet'),
    )

    order = models.ForeignKey(Order, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='initiated')
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    failure_reason = models.CharField(max_length=255, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.payment_type} payment for Order #{self.order.id} - {self.payment_status}"
    
class Invoice(models.Model):
    order = models.ForeignKey(Order, on_delete=models.RESTRICT)
    invoice_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    invoice_date = models.DateTimeField(auto_now_add=True)
    invoice_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number
