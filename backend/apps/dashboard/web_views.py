from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count
from apps.orders.models import Order
from apps.products.models import Stock
from apps.finance.models import Payment

class DashboardWebView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get(self, request):
        # Gather Stats for Template
        total_sales = Payment.objects.filter(payment_status='success').aggregate(total=Sum('amount'))['total'] or 0
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        low_stock_items = Stock.objects.filter(quantity_in_stock__lte=10).select_related(
            'variant_size__variant__product',
            'variant_size__size'
        )
        
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
        
        context = {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'low_stock_items': low_stock_items,
            'recent_orders': recent_orders
        }
        return render(request, 'dashboard/index.html', context)
