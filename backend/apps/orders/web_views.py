from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order

class OrderListView(LoginRequiredMixin, View):
    def get(self, request):
        from apps.finance.models import Payment
        
        orders = Order.objects.filter(user=request.user).order_by('-order_date')
        
        # Add payment information to each order
        for order in orders:
            # Check advance payment
            advance_payment = Payment.objects.filter(
                order=order,
                payment_type='advance',
                payment_status='success'
            ).first()
            order.advance_paid = advance_payment is not None
            
            # Check final payment
            final_payment = Payment.objects.filter(
                order=order,
                payment_type='final'
            ).first()
            order.final_payment = final_payment
            order.final_paid = final_payment is not None and final_payment.payment_status == 'success'
        
        return render(request, 'orders/list.html', {'orders': orders})
