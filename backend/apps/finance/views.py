"""
Finance API Views

Handles payment-related API endpoints including payment creation,
verification, retry, and payment history.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from utils.rate_limiting import rate_limit_strict, rate_limit_api
import os

from .models import Payment, Invoice
from .serializers import PaymentSerializer, PaymentCreateSerializer
from services.payment_service import PaymentService
from services.invoice_service import InvoiceService
from apps.orders.models import Order


@method_decorator(rate_limit_strict, name='post')
class PaymentCreateView(APIView):
    """
    Create a Razorpay payment order for advance or final payment.
    
    POST /api/payments/create/
    Body: {
        "order_id": 123,
        "payment_type": "advance" or "final",
        "payment_method": "upi" (optional)
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        order_id = request.data.get('order_id')
        payment_type = request.data.get('payment_type')
        payment_method = request.data.get('payment_method', 'upi')
        
        if not order_id or not payment_type:
            return Response(
                {'error': 'order_id and payment_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = PaymentService.create_razorpay_order(
                order_id=order_id,
                payment_type=payment_type,
                payment_method=payment_method
            )
            
            # Serialize payment
            payment_serializer = PaymentSerializer(result['payment'])
            
            return Response({
                'payment': payment_serializer.data,
                'razorpay_order_id': result['razorpay_order']['id'],
                'razorpay_key_id': PaymentService.RAZORPAY_KEY_ID,
                'amount': result['razorpay_order']['amount'],
                'currency': result['razorpay_order']['currency'],
                'message': result['message']
            }, status=status.HTTP_201_CREATED)
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(rate_limit_strict, name='post')
class PaymentVerifyView(APIView):
    """
    Verify payment signature and process successful payment.
    
    POST /api/payments/verify/
    Body: {
        "payment_id": 123,
        "razorpay_payment_id": "pay_xxx",
        "razorpay_signature": "signature_xxx"
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        payment_id = request.data.get('payment_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        if not all([payment_id, razorpay_payment_id, razorpay_signature]):
            return Response(
                {'error': 'payment_id, razorpay_payment_id, and razorpay_signature are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = PaymentService.process_successful_payment(
                payment_id=payment_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature
            )
            
            payment_serializer = PaymentSerializer(result['payment'])
            
            return Response({
                'payment': payment_serializer.data,
                'order_id': result['order'].id,
                'order_status': result['order'].status,
                'message': result['message']
            }, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentFailureView(APIView):
    """
    Handle payment failure.
    
    POST /api/payments/failure/
    Body: {
        "payment_id": 123,
        "failure_reason": "Payment declined"
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        payment_id = request.data.get('payment_id')
        failure_reason = request.data.get('failure_reason')
        
        if not payment_id:
            return Response(
                {'error': 'payment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment = PaymentService.handle_payment_failure(
                payment_id=payment_id,
                failure_reason=failure_reason
            )
            
            payment_serializer = PaymentSerializer(payment)
            
            return Response({
                'payment': payment_serializer.data,
                'message': 'Payment failure recorded'
            }, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentRetryView(APIView):
    """
    Retry a failed payment.
    
    POST /api/payments/retry/
    Body: {
        "order_id": 123,
        "payment_type": "advance" or "final",
        "payment_method": "upi" (optional)
    }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        order_id = request.data.get('order_id')
        payment_type = request.data.get('payment_type')
        payment_method = request.data.get('payment_method', 'upi')
        
        if not order_id or not payment_type:
            return Response(
                {'error': 'order_id and payment_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = PaymentService.retry_payment(
                order_id=order_id,
                payment_type=payment_type,
                payment_method=payment_method
            )
            
            payment_serializer = PaymentSerializer(result['payment'])
            
            return Response({
                'payment': payment_serializer.data,
                'razorpay_order_id': result['razorpay_order']['id'],
                'razorpay_key_id': PaymentService.RAZORPAY_KEY_ID,
                'amount': result['razorpay_order']['amount'],
                'currency': result['razorpay_order']['currency'],
                'message': result['message']
            }, status=status.HTTP_201_CREATED)
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentHistoryView(generics.ListAPIView):
    """
    Get payment history for the authenticated user.
    
    GET /api/payments/history/
    Optional query params:
        - order_id: Filter by order ID
    
    Optimized with select_related for order and user.
    """
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        queryset = Payment.objects.filter(
            order__user=self.request.user
        ).select_related(
            'order',
            'order__user',
            'order__delivery_address'
        ).order_by('-created_at')
        
        # Filter by order_id if provided
        order_id = self.request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        return queryset


class PaymentStatusView(APIView):
    """
    Get payment status for an order.
    
    GET /api/payments/status/<order_id>/
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, order_id):
        try:
            result = PaymentService.check_payment_completion(order_id)
            return Response(result, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentWebhookView(APIView):
    """
    Handle Razorpay webhook events.
    
    POST /api/payments/webhook/
    """
    permission_classes = ()  # No authentication for webhooks
    
    def post(self, request):
        webhook_data = request.data
        
        try:
            result = PaymentService.handle_webhook(webhook_data)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class InvoiceDownloadView(APIView):
    """
    Download invoice PDF for an order.
    
    GET /api/invoices/<order_id>/download/
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, order_id):
        try:
            # Get order and verify ownership
            order = get_object_or_404(Order, id=order_id)
            
            # Check if user owns the order or is admin
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You do not have permission to access this invoice'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create invoice
            try:
                invoice = Invoice.objects.get(order=order)
            except Invoice.DoesNotExist:
                # Generate invoice if it doesn't exist
                invoice = InvoiceService.generate_invoice(order_id)
            
            # Generate PDF if not already generated
            if not invoice.invoice_url:
                InvoiceService.generate_invoice_pdf(invoice.id)
                invoice.refresh_from_db()
            
            # Get PDF file path
            pdf_path = invoice.invoice_url.lstrip('/')
            full_path = os.path.join('backend', pdf_path)
            
            if not os.path.exists(full_path):
                # Regenerate PDF if file doesn't exist
                InvoiceService.generate_invoice_pdf(invoice.id)
                invoice.refresh_from_db()
                pdf_path = invoice.invoice_url.lstrip('/')
                full_path = os.path.join('backend', pdf_path)
            
            # Return PDF file
            response = FileResponse(
                open(full_path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
            return response
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to generate invoice: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InvoiceDetailView(APIView):
    """
    Get invoice details for an order.
    
    GET /api/invoices/<order_id>/
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, order_id):
        try:
            # Get order and verify ownership
            order = get_object_or_404(Order, id=order_id)
            
            # Check if user owns the order or is admin
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You do not have permission to access this invoice'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create invoice
            try:
                invoice = Invoice.objects.get(order=order)
            except Invoice.DoesNotExist:
                # Generate invoice if it doesn't exist
                invoice = InvoiceService.generate_invoice(order_id)
            
            # Calculate totals
            totals = InvoiceService.calculate_invoice_totals(order_id)
            
            # Get payment information
            payments = Payment.objects.filter(
                order=order,
                payment_status='success'
            ).order_by('created_at')
            
            payment_data = [{
                'payment_type': p.get_payment_type_display(),
                'amount': str(p.amount),
                'paid_at': p.paid_at.isoformat() if p.paid_at else None,
                'payment_status': p.get_payment_status_display()
            } for p in payments]
            
            return Response({
                'invoice_number': invoice.invoice_number,
                'invoice_date': invoice.invoice_date.isoformat(),
                'order_id': order.id,
                'order_date': order.order_date.isoformat(),
                'customer': {
                    'name': order.user.full_name,
                    'email': order.user.email,
                },
                'delivery_address': {
                    'address_line1': order.delivery_address.address_line1,
                    'address_line2': order.delivery_address.address_line2,
                    'city': order.delivery_address.city.city_name,
                    'state': order.delivery_address.state.state_name,
                    'postal_code': order.delivery_address.postal_code.postal_code,
                    'country': order.delivery_address.country.country_name,
                },
                'items': [{
                    'product_name': item.variant_size.variant.product.product_name,
                    'variant_details': f"{item.variant_size.variant.fabric.fabric_name} - {item.variant_size.variant.color.color_name}",
                    'size': item.variant_size.size.size_code,
                    'quantity': item.quantity,
                    'unit_price': str(item.snapshot_unit_price),
                    'total': str(item.snapshot_unit_price * item.quantity)
                } for item in order.items.all()],
                'subtotal': str(totals['subtotal']),
                'tax_percentage': str(totals['tax_percentage']),
                'tax_amount': str(totals['tax_amount']),
                'total_amount': str(totals['total_amount']),
                'payments': payment_data,
                'invoice_url': invoice.invoice_url if invoice.invoice_url else None
            }, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
