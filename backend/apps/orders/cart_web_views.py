from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from .models import Order
from apps.finance.models import Payment

class CartView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'cart/cart.html')

class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'checkout/checkout.html')

class OrderTrackingView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        return render(request, 'orders/tracking.html', {'order_id': order_id})

class FinalPaymentView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        """Display final payment page for the order"""
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if advance payment is completed
        advance_payment = Payment.objects.filter(
            order=order,
            payment_type='advance',
            payment_status='success'
        ).first()
        
        if not advance_payment:
            messages.error(request, 'Advance payment must be completed before final payment.')
            return redirect('order-list-web')
        
        # Check if final payment already exists
        final_payment = Payment.objects.filter(
            order=order,
            payment_type='final'
        ).first()
        
        if not final_payment:
            messages.error(request, 'Final payment has not been initiated yet. Please wait for admin to create final payment.')
            return redirect('order-list-web')
        
        if final_payment.payment_status == 'success':
            messages.info(request, 'Final payment has already been completed.')
            return redirect('order-tracking-web', order_id=order.id)
        
        # Get Razorpay key
        from services.payment_service import PaymentService
        
        context = {
            'order': order,
            'final_payment': final_payment,
            'advance_payment': advance_payment,
            'razorpay_key_id': PaymentService.RAZORPAY_KEY_ID,
        }
        
        return render(request, 'orders/final_payment.html', context)
