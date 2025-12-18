from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Inquiry, Complaint, Feedback, QuotationRequest, QuotationPrice
from .serializers import (
    InquirySerializer, InquiryDetailSerializer, ComplaintSerializer, ComplaintDetailSerializer,
    ComplaintStatusUpdateSerializer, FeedbackSerializer, FeedbackDetailSerializer,
    QuotationRequestSerializer, QuotationRequestDetailSerializer,
    QuotationPriceSerializer, QuotationPriceCreateSerializer, QuotationAcceptRejectSerializer
)
from apps.users.permissions import IsAdmin

class InquiryListCreateView(generics.ListCreateAPIView):
    serializer_class = InquirySerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = ('inquiry_date', 'status')
    ordering = ('-inquiry_date',)
    search_fields = ('description',)

    def get_queryset(self):
        """
        Optimized queryset with select_related for user.
        """
        user = self.request.user
        if user.user_type == 'admin':
            return Inquiry.objects.all().select_related('user').order_by('-inquiry_date')
        return Inquiry.objects.filter(user=user).select_related('user').order_by('-inquiry_date')

    def perform_create(self, serializer):
        # Save inquiry - file upload is handled automatically by CloudinaryField
        serializer.save(user=self.request.user)

class InquiryDetailView(generics.RetrieveAPIView):
    serializer_class = InquiryDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Optimized queryset with select_related and prefetch_related.
        """
        user = self.request.user
        base_queryset = Inquiry.objects.all().select_related('user').prefetch_related(
            'quotation_requests__variant_size__variant__product',
            'quotation_requests__variant_size__size',
            'quotation_requests__prices'
        )
        if user.user_type == 'admin':
            return base_queryset
        return base_queryset.filter(user=user)

class QuotationRequestCreateView(generics.CreateAPIView):
    serializer_class = QuotationRequestSerializer
    permission_classes = (IsAdmin,)

    def perform_create(self, serializer):
        quotation_request = serializer.save()
        # Update inquiry status to reviewed
        inquiry = quotation_request.inquiry
        if inquiry.status == 'pending':
            inquiry.status = 'reviewed'
            inquiry.save()

class QuotationRequestDetailView(generics.RetrieveAPIView):
    serializer_class = QuotationRequestDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        """
        Optimized queryset with select_related and prefetch_related.
        """
        return QuotationRequest.objects.all().select_related(
            'inquiry',
            'inquiry__user',
            'variant_size',
            'variant_size__variant',
            'variant_size__variant__product',
            'variant_size__size'
        ).prefetch_related('prices')

class QuotationPriceCreateView(generics.CreateAPIView):
    serializer_class = QuotationPriceCreateSerializer
    permission_classes = (IsAdmin,)

    def perform_create(self, serializer):
        quotation_price = serializer.save()
        # Update quotation request status to quoted
        quotation_request = quotation_price.quotation
        quotation_request.status = 'quoted'
        quotation_request.save()
        
        # Update inquiry status to quoted
        inquiry = quotation_request.inquiry
        inquiry.status = 'quoted'
        inquiry.save()

class QuotationPriceSendView(APIView):
    permission_classes = (IsAdmin,)

    def post(self, request, pk):
        quotation_price = get_object_or_404(QuotationPrice, pk=pk)
        
        if quotation_price.status != 'pending':
            return Response(
                {'error': 'Quotation price has already been sent or processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to sent
        quotation_price.status = 'sent'
        quotation_price.save()
        
        # Send email notification to customer
        try:
            from services.email_service import EmailService
            email_result = EmailService.send_quotation_notification(pk)
            email_sent = email_result['success']
            email_message = email_result['message']
        except Exception as e:
            email_sent = False
            email_message = 'Email service unavailable'
        
        response_data = QuotationPriceSerializer(quotation_price).data
        response_data['email_sent'] = email_sent
        response_data['email_message'] = email_message
        
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )

class QuotationPriceAcceptRejectView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        quotation_price = get_object_or_404(QuotationPrice, pk=pk)
        
        # Verify user owns the inquiry
        if quotation_price.quotation.inquiry.user != request.user:
            return Response(
                {'error': 'You do not have permission to accept/reject this quotation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if quotation_price.status not in ['pending', 'sent']:
            return Response(
                {'error': 'Quotation has already been accepted or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if quotation is still valid
        if timezone.now() > quotation_price.valid_until:
            return Response(
                {'error': 'Quotation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuotationAcceptRejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        
        if action == 'accept':
            quotation_price.status = 'accepted'
            quotation_price.quotation.status = 'accepted'
            
            # Auto-reject all other quotations for this inquiry
            inquiry = quotation_price.quotation.inquiry
            other_quotations = QuotationRequest.objects.filter(
                inquiry=inquiry
            ).exclude(id=quotation_price.quotation.id)
            
            # Log the auto-rejection process
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Auto-rejecting {other_quotations.count()} other quotations for inquiry {inquiry.id}")
            
            # Reject all other quotation requests and their prices
            for other_quotation in other_quotations:
                if other_quotation.status not in ['accepted', 'rejected']:
                    old_status = other_quotation.status
                    other_quotation.status = 'rejected'
                    other_quotation.save()
                    logger.info(f"Quotation request {other_quotation.id} status changed from {old_status} to rejected")
                
                # Reject all prices for this quotation request
                other_prices = other_quotation.prices.filter(
                    status__in=['pending', 'sent']
                )
                rejected_count = other_prices.update(status='rejected')
                if rejected_count > 0:
                    logger.info(f"Rejected {rejected_count} prices for quotation request {other_quotation.id}")
            
            # Update inquiry status to accepted
            inquiry.status = 'accepted'
            inquiry.save()
            logger.info(f"Inquiry {inquiry.id} status updated to accepted")
            
        else:
            quotation_price.status = 'rejected'
            quotation_price.quotation.status = 'rejected'
        
        quotation_price.save()
        quotation_price.quotation.save()
        
        # Return response with inquiry ID for frontend convenience
        response_data = QuotationPriceSerializer(quotation_price).data
        response_data['inquiry_id'] = quotation_price.quotation.inquiry.id
        
        # Add message about auto-rejection if accepted
        if action == 'accept':
            other_quotations_count = QuotationRequest.objects.filter(
                inquiry=quotation_price.quotation.inquiry
            ).exclude(id=quotation_price.quotation.id).count()
            
            if other_quotations_count > 0:
                response_data['message'] = f'Quotation accepted successfully! {other_quotations_count} other quotation(s) have been automatically rejected.'
            else:
                response_data['message'] = 'Quotation accepted successfully!'
        else:
            response_data['message'] = 'Quotation rejected successfully!'
        
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )

class ComplaintListCreateView(generics.ListCreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = ('complaint_date', 'status', 'category')
    ordering = ('-complaint_date',)
    search_fields = ('description', 'category')

    def get_queryset(self):
        """
        Optimized queryset with select_related for user and order.
        """
        user = self.request.user
        base_queryset = Complaint.objects.all().select_related('user', 'order')
        
        if user.user_type == 'admin':
            queryset = base_queryset.order_by('-complaint_date')
        else:
            queryset = base_queryset.filter(user=user).order_by('-complaint_date')
        
        # Filter by order_id if provided
        order_id = self.request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ComplaintDetailView(generics.RetrieveAPIView):
    serializer_class = ComplaintDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Optimized queryset with select_related for user and order.
        """
        user = self.request.user
        base_queryset = Complaint.objects.all().select_related('user', 'order')
        if user.user_type == 'admin':
            return base_queryset
        return base_queryset.filter(user=user)

class ComplaintStatusUpdateView(APIView):
    permission_classes = (IsAdmin,)

    def put(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        
        serializer = ComplaintStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        resolution_notes = serializer.validated_data.get('resolution_notes', '')
        
        # Update complaint status
        complaint.status = new_status
        
        # If status is resolved, set resolution date
        if new_status == 'resolved' and complaint.resolution_date is None:
            complaint.resolution_date = timezone.now()
        
        # Update resolution notes if provided
        if resolution_notes:
            complaint.resolution_notes = resolution_notes
        
        complaint.save()
        
        # Send email notification to customer
        try:
            from services.email_service import EmailService
            email_result = EmailService.send_complaint_status_notification(complaint.id)
            
            if not email_result['success']:
                # Log email failure but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send complaint status email for complaint {complaint.id}: {email_result['message']}")
        except Exception as e:
            # Log email failure but don't fail the request
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Exception sending complaint status email for complaint {complaint.id}: {str(e)}")
        
        response_data = ComplaintDetailSerializer(complaint).data
        response_data['email_sent'] = email_result.get('success', False) if 'email_result' in locals() else False
        
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )

class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FeedbackListView(generics.ListAPIView):
    serializer_class = FeedbackDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('feedback_date', 'rating')
    ordering = ('-feedback_date',)

    def get_queryset(self):
        """
        Optimized queryset with select_related for user and order.
        """
        user = self.request.user
        base_queryset = Feedback.objects.all().select_related('user', 'order')
        if user.user_type == 'admin':
            return base_queryset.order_by('-feedback_date')
        return base_queryset.filter(user=user).order_by('-feedback_date')

class FeedbackDetailView(generics.RetrieveAPIView):
    serializer_class = FeedbackDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Optimized queryset with select_related for user and order.
        """
        user = self.request.user
        base_queryset = Feedback.objects.all().select_related('user', 'order')
        if user.user_type == 'admin':
            return base_queryset
        return base_queryset.filter(user=user)
