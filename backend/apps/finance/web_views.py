"""
Finance Web Views

Handles payment-related web pages including success, failure, and payment history.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Payment
from apps.orders.models import Order
from services.payment_service import PaymentService


class PaymentSuccessView(LoginRequiredMixin, View):
    """
    Payment success page.
    Displays after successful payment completion.
    """
    
    def get(self, request):
        payment_id = request.GET.get('payment_id')
        order_id = request.GET.get('order_id')
        
        context = {
            'payment_id': payment_id,
            'order_id': order_id
        }
        
        # Get payment details if payment_id provided
        if payment_id:
            try:
                payment = Payment.objects.select_related('order').get(
                    id=payment_id,
                    order__user=request.user
                )
                context['payment'] = payment
                context['order'] = payment.order
            except Payment.DoesNotExist:
                messages.error(request, 'Payment not found')
        
        # Get order details if order_id provided
        elif order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                context['order'] = order
                
                # Get latest successful payment for this order
                payment = Payment.objects.filter(
                    order=order,
                    payment_status='success'
                ).order_by('-paid_at').first()
                
                if payment:
                    context['payment'] = payment
            except Order.DoesNotExist:
                messages.error(request, 'Order not found')
        
        return render(request, 'payments/success.html', context)


class PaymentFailureView(LoginRequiredMixin, View):
    """
    Payment failure page.
    Displays after payment failure with retry option.
    """
    
    def get(self, request):
        payment_id = request.GET.get('payment_id')
        order_id = request.GET.get('order_id')
        error_message = request.GET.get('error', 'Payment failed. Please try again.')
        
        context = {
            'payment_id': payment_id,
            'order_id': order_id,
            'error_message': error_message
        }
        
        # Get payment details if payment_id provided
        if payment_id:
            try:
                payment = Payment.objects.select_related('order').get(
                    id=payment_id,
                    order__user=request.user
                )
                context['payment'] = payment
                context['order'] = payment.order
            except Payment.DoesNotExist:
                messages.error(request, 'Payment not found')
        
        # Get order details if order_id provided
        elif order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                context['order'] = order
                
                # Get latest failed payment for this order
                payment = Payment.objects.filter(
                    order=order,
                    payment_status='failed'
                ).order_by('-created_at').first()
                
                if payment:
                    context['payment'] = payment
            except Order.DoesNotExist:
                messages.error(request, 'Order not found')
        
        return render(request, 'payments/failure.html', context)


class PaymentHistoryView(LoginRequiredMixin, View):
    """
    Payment history page.
    Displays all payments for the authenticated user.
    """
    
    def get(self, request):
        # Get all payments for user's orders
        payments = Payment.objects.filter(
            order__user=request.user
        ).select_related('order').order_by('-created_at')
        
        # Filter by order_id if provided
        order_id = request.GET.get('order_id')
        if order_id:
            payments = payments.filter(order_id=order_id)
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            payments = payments.filter(payment_status=status_filter)
        
        context = {
            'payments': payments,
            'order_id': order_id,
            'status_filter': status_filter
        }
        
        return render(request, 'payments/history.html', context)


class OrderPaymentView(LoginRequiredMixin, View):
    """
    Order payment page.
    Displays payment options and initiates payment for an order.
    """
    
    def get(self, request, order_id):
        # Get order
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check payment status
        try:
            payment_status = PaymentService.check_payment_completion(order_id)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('order-list-web')
        
        # Get existing payments
        payments = Payment.objects.filter(order=order).order_by('-created_at')
        
        context = {
            'order': order,
            'payment_status': payment_status,
            'payments': payments,
            'razorpay_key_id': PaymentService.RAZORPAY_KEY_ID
        }
        
        return render(request, 'payments/order_payment.html', context)



class InvoicePreviewView(LoginRequiredMixin, View):
    """
    Invoice preview page.
    Displays invoice details before download.
    """
    
    def get(self, request, order_id):
        # Get order and verify ownership
        order = get_object_or_404(Order, id=order_id)
        
        # Check if user owns the order or is admin
        if order.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this invoice')
            return redirect('order-list-web')
        
        # Get or create invoice
        from .models import Invoice
        from services.invoice_service import InvoiceService
        
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
        
        context = {
            'invoice': invoice,
            'order': order,
            'totals': totals,
            'payments': payments
        }
        
        return render(request, 'finance/invoice_preview.html', context)
