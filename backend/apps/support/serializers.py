from rest_framework import serializers
from .models import Inquiry, Complaint, Feedback, QuotationRequest, QuotationPrice
from utils.security import validate_document_file, sanitize_filename

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'
        read_only_fields = ('user', 'status', 'inquiry_date')
    
    def validate_logo_file(self, value):
        """Validate uploaded logo file."""
        if value:
            validate_document_file(value)
            # Sanitize filename
            value.name = sanitize_filename(value.name)
        return value

class InquiryDetailSerializer(serializers.ModelSerializer):
    quotation_requests = serializers.SerializerMethodField()
    
    class Meta:
        model = Inquiry
        fields = '__all__'
        read_only_fields = ('user', 'status', 'inquiry_date')
    
    def get_quotation_requests(self, obj):
        requests = obj.quotation_requests.all()
        return QuotationRequestDetailSerializer(requests, many=True).data

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ('user', 'status', 'complaint_date', 'resolution_date', 'resolution_notes')

class ComplaintDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    order_number = serializers.CharField(source='order.id', read_only=True)
    
    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ('user', 'complaint_date')

class ComplaintStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Complaint.STATUS_CHOICES)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('user', 'feedback_date')

class FeedbackDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    order_number = serializers.CharField(source='order.id', read_only=True)
    order_date = serializers.DateTimeField(source='order.order_date', read_only=True)
    order_total = serializers.DecimalField(source='order.total_amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('user', 'feedback_date')

class QuotationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationRequest
        fields = '__all__'
        read_only_fields = ('requested_date', 'status')

class QuotationRequestDetailSerializer(serializers.ModelSerializer):
    prices = serializers.SerializerMethodField()
    
    class Meta:
        model = QuotationRequest
        fields = '__all__'
        read_only_fields = ('requested_date', 'status')
    
    def get_prices(self, obj):
        prices = obj.prices.all()
        return QuotationPriceSerializer(prices, many=True).data

class QuotationPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationPrice
        fields = '__all__'
        read_only_fields = ('quoted_date', 'status')

class QuotationPriceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationPrice
        fields = ('quotation', 'unit_price', 'customization_charge_per_unit', 
                  'quoted_quantity', 'valid_from', 'valid_until')

class QuotationAcceptRejectSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'reject'])
    notes = serializers.CharField(required=False, allow_blank=True)
