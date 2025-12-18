from django.db import models
from cloudinary.models import CloudinaryField
from apps.users.models import User
from apps.products.models import VariantSize
from apps.orders.models import Order

class Inquiry(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('quoted', 'Quoted'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    inquiry_description = models.TextField()
    logo_file = CloudinaryField('logo', null=True, blank=True, folder='inquiry_logos')
    inquiry_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Inquiry {self.id} by {self.user}"

class QuotationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('quoted', 'Quoted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='quotation_requests')
    variant_size = models.ForeignKey(VariantSize, on_delete=models.RESTRICT)
    requested_quantity = models.IntegerField()
    customization_type = models.CharField(max_length=100, null=True, blank=True)
    customization_details = models.TextField(null=True, blank=True)
    requested_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Quote Request {self.id} for Inquiry {self.inquiry.id}"

class QuotationPrice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    quotation = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE, related_name='prices')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    customization_charge_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quoted_quantity = models.IntegerField()
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    quoted_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Price Quote {self.id} for Request {self.quotation.id}"

class Complaint(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    complaint_description = models.TextField()
    complaint_category = models.CharField(max_length=50)
    complaint_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    resolution_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Complaint {self.id} - {self.status}"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rating = models.IntegerField()
    feedback_description = models.TextField(null=True, blank=True)
    feedback_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Order {self.order.id} - {self.rating}/5"
