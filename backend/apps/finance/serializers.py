"""
Finance Serializers

Serializers for payment and invoice models.
"""

from rest_framework import serializers
from .models import Payment, Invoice


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    order_number = serializers.IntegerField(source='order.id', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'amount', 
            'payment_type', 'payment_type_display',
            'payment_method', 'payment_method_display',
            'payment_status', 'payment_status_display',
            'razorpay_order_id', 'razorpay_payment_id',
            'failure_reason', 'paid_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'razorpay_order_id', 'razorpay_payment_id',
            'payment_status', 'paid_at', 'created_at', 'updated_at'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating payment orders"""
    
    order_id = serializers.IntegerField()
    payment_type = serializers.ChoiceField(choices=['advance', 'final'])
    payment_method = serializers.ChoiceField(
        choices=['upi', 'card', 'netbanking', 'wallet'],
        default='upi'
    )


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    
    order_number = serializers.IntegerField(source='order.id', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'order', 'order_number', 'invoice_number',
            'total_amount', 'invoice_date', 'invoice_url', 'created_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'invoice_date', 'created_at']
