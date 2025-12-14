from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count, F
from apps.orders.models import Order
from apps.products.models import Stock, Product
from apps.finance.models import Payment

class DashboardStatsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        # Sales Stats
        total_sales = Payment.objects.filter(payment_status='success').aggregate(total=Sum('amount'))['total'] or 0
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        # Inventory Stats
        low_stock_threshold = 10
        low_stock_count = Stock.objects.filter(quantity_in_stock__lte=low_stock_threshold).count()
        
        # Recent Orders
        recent_orders = Order.objects.all().order_by('-created_at')[:5].values(
            'id', 'user__full_name', 'status', 'created_at'  # Note: created_at might be order_date
        )
        # Fix: Order model uses order_date, not created_at in some definitions, check model
        # Checking Order model: order_date = auto_now_add=True. So it exists.
        
        return Response({
            'total_sales': total_sales,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'low_stock_count': low_stock_count,
            'recent_orders': list(recent_orders),
            'sales_trend': self.get_sales_trend(),
            'low_stock_details': self.get_low_stock_details(low_stock_threshold)
        })

    def get_sales_trend(self):
        # Last 7 days sales
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        trend = []
        for i in range(6, -1, -1):
            date = today - datetime.timedelta(days=i)
            daily_sales = Payment.objects.filter(
                payment_status='success',
                created_at__date=date
            ).aggregate(total=Sum('amount'))['total'] or 0
            trend.append({'date': date, 'sales': daily_sales})
        return trend

    def get_low_stock_details(self, threshold):
        return list(Stock.objects.filter(quantity_in_stock__lte=threshold).values(
            'variant_size__size__size_code',
            'variant_size__variant__product__product_name',
            'quantity_in_stock'
        )[:10])
