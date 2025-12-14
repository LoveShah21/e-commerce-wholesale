from rest_framework import serializers
from .models import Inquiry, Complaint, Feedback, QuotationRequest

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'
        read_only_fields = ('user', 'status', 'inquiry_date')

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ('user', 'status', 'complaint_date', 'resolution_date', 'resolution_notes')

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('user', 'feedback_date')

class QuotationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationRequest
        fields = '__all__'
