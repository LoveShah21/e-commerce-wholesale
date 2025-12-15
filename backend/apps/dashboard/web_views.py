from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from apps.orders.models import Order
from apps.products.models import Stock
from apps.finance.models import Payment

class DashboardWebView(LoginRequiredMixin, View):
    """
    Role-based dashboard view that redirects users to appropriate dashboards
    based on their role (customer, admin, operator).
    """
    
    def get(self, request):
        user = request.user
        
        # Role-specific dashboard redirects
        if user.user_type == 'customer':
            # Customer dashboard: show their orders and account info
            user_orders = Order.objects.filter(user=user).select_related('delivery_address').order_by('-order_date')[:10]
            recent_payments = Payment.objects.filter(order__user=user).order_by('-created_at')[:5]
            
            context = {
                'user_orders': user_orders,
                'recent_payments': recent_payments,
                'total_orders': Order.objects.filter(user=user).count(),
                'pending_orders': Order.objects.filter(user=user, status='pending').count(),
            }
            return render(request, 'dashboard/customer_dashboard.html', context)
        
        elif user.user_type == 'admin':
            # Admin dashboard: show business metrics and analytics
            total_sales = Payment.objects.filter(payment_status='success').aggregate(total=Sum('amount'))['total'] or 0
            total_orders = Order.objects.count()
            pending_orders = Order.objects.filter(status='pending').count()
            
            low_stock_items = Stock.objects.filter(quantity_in_stock__lte=10).select_related(
                'variant_size__variant__product',
                'variant_size__size'
            )
            
            recent_orders = Order.objects.select_related('user').order_by('-order_date')[:10]
            
            context = {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'low_stock_items': low_stock_items,
                'recent_orders': recent_orders
            }
            return render(request, 'dashboard/index.html', context)
        
        elif user.user_type == 'operator':
            # Operator dashboard: show manufacturing and inventory info
            pending_manufacturing = Order.objects.filter(status__in=['confirmed', 'processing']).count()
            low_stock_items = Stock.objects.filter(quantity_in_stock__lte=10).select_related(
                'variant_size__variant__product',
                'variant_size__size'
            )
            recent_orders = Order.objects.filter(status__in=['confirmed', 'processing']).select_related('user').order_by('-order_date')[:10]
            
            context = {
                'pending_manufacturing': pending_manufacturing,
                'low_stock_items': low_stock_items,
                'recent_orders': recent_orders,
            }
            return render(request, 'dashboard/operator_dashboard.html', context)
        
        else:
            # Unknown role, redirect to home
            return redirect('/')
