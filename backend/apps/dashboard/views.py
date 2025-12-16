from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from apps.orders.models import Order
from apps.products.models import Stock, Product
from apps.finance.models import Payment
from apps.manufacturing.models import RawMaterial, MaterialSupplier
from utils.query_cache import generate_cache_key, get_cache_timeout

class DashboardStatsView(APIView):
    """
    API endpoint for admin dashboard statistics with date range filtering.
    
    Query Parameters:
    - start_date: Start date for filtering (YYYY-MM-DD format)
    - end_date: End date for filtering (YYYY-MM-DD format)
    - days: Number of days for sales trend (default: 7)
    - low_stock_threshold: Threshold for low stock alerts (default: 10)
    """
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        # Parse query parameters (use request.GET for compatibility)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        days = int(request.GET.get('days', 7))
        low_stock_threshold = int(request.GET.get('low_stock_threshold', 10))
        
        # Generate cache key based on parameters
        cache_key = generate_cache_key(
            'dashboard_stats',
            start_date=start_date,
            end_date=end_date,
            days=days,
            threshold=low_stock_threshold
        )
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response(cached_result)
        
        # Parse dates if provided
        date_filter = {}
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                date_filter['created_at__date__gte'] = start_date_obj
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                date_filter['created_at__date__lte'] = end_date_obj
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Sales Stats with date filtering
        payment_filter = {'payment_status': 'success'}
        payment_filter.update(date_filter)
        total_sales = Payment.objects.filter(**payment_filter).aggregate(total=Sum('amount'))['total'] or 0
        
        # Order Stats with date filtering
        order_date_filter = {}
        if start_date:
            order_date_filter['order_date__date__gte'] = start_date_obj
        if end_date:
            order_date_filter['order_date__date__lte'] = end_date_obj
            
        total_orders = Order.objects.filter(**order_date_filter).count()
        pending_orders = Order.objects.filter(status='pending', **order_date_filter).count()
        
        # Inventory Stats (not date-filtered as it's current state)
        # Count both product stock and raw material low stock
        product_low_stock = Stock.objects.filter(quantity_in_stock__lte=low_stock_threshold).count()
        
        # Raw material low stock - check against reorder levels
        raw_material_low_stock = 0
        for material in RawMaterial.objects.all():
            # Check if material has supplier-specific reorder levels
            supplier_reorder_levels = MaterialSupplier.objects.filter(
                material=material, 
                reorder_level__isnull=False
            ).values_list('reorder_level', flat=True)
            
            if supplier_reorder_levels:
                # Use the minimum reorder level from suppliers
                min_reorder_level = min(supplier_reorder_levels)
                if material.current_quantity <= min_reorder_level:
                    raw_material_low_stock += 1
            elif material.default_reorder_level:
                # Use default reorder level
                if material.current_quantity <= material.default_reorder_level:
                    raw_material_low_stock += 1
            else:
                # Use threshold as fallback
                if material.current_quantity <= low_stock_threshold:
                    raw_material_low_stock += 1
        
        low_stock_count = product_low_stock + raw_material_low_stock
        
        # Recent Orders (limited to 10, ordered by date descending)
        # Optimized with select_related to avoid N+1 queries
        recent_orders = Order.objects.filter(
            **order_date_filter
        ).select_related('user').order_by('-order_date')[:10].values(
            'id', 'user__full_name', 'status', 'order_date'
        )
        
        result = {
            'total_sales': float(total_sales),
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'low_stock_count': low_stock_count,
            'recent_orders': list(recent_orders),
            'sales_trend': self.get_sales_trend(days, start_date, end_date),
            'low_stock_details': self.get_low_stock_details(low_stock_threshold)
        }
        
        # Cache the result for 3 minutes
        cache.set(cache_key, result, get_cache_timeout('dashboard_stats'))
        
        return Response(result)

    def get_sales_trend(self, days=7, start_date=None, end_date=None):
        """
        Calculate sales trend for the specified number of days.
        Returns exactly 'days' data points, one for each day.
        """
        today = timezone.now().date()
        
        # If custom date range is provided, use it
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date_obj = today
            
        trend = []
        for i in range(days - 1, -1, -1):
            date = end_date_obj - timedelta(days=i)
            daily_sales = Payment.objects.filter(
                payment_status='success',
                created_at__date=date
            ).aggregate(total=Sum('amount'))['total'] or 0
            trend.append({
                'date': str(date),
                'sales': float(daily_sales)
            })
        return trend

    def get_low_stock_details(self, threshold):
        """
        Get details of items with stock below the threshold.
        Returns both product stock and raw material alerts.
        """
        low_stock_items = []
        
        # Get product stock alerts
        product_stock_alerts = Stock.objects.filter(
            quantity_in_stock__lte=threshold
        ).select_related(
            'variant_size__size',
            'variant_size__variant__product'
        ).values(
            'variant_size__size__size_code',
            'variant_size__variant__product__product_name',
            'quantity_in_stock'
        )[:10]  # Limit to 10 product items
        
        for item in product_stock_alerts:
            low_stock_items.append({
                'type': 'product',
                'name': item['variant_size__variant__product__product_name'],
                'variant': f"Size: {item['variant_size__size__size_code']}",
                'current_stock': item['quantity_in_stock'],
                'threshold': threshold
            })
        
        # Get raw material alerts
        raw_materials = RawMaterial.objects.select_related('material_type').all()
        
        for material in raw_materials:
            is_low_stock = False
            reorder_level = threshold  # Default
            
            # Check supplier-specific reorder levels
            supplier_reorder_levels = MaterialSupplier.objects.filter(
                material=material, 
                reorder_level__isnull=False
            ).values_list('reorder_level', flat=True)
            
            if supplier_reorder_levels:
                reorder_level = min(supplier_reorder_levels)
                is_low_stock = material.current_quantity <= reorder_level
            elif material.default_reorder_level:
                reorder_level = material.default_reorder_level
                is_low_stock = material.current_quantity <= reorder_level
            else:
                is_low_stock = material.current_quantity <= threshold
            
            if is_low_stock and len(low_stock_items) < 20:  # Total limit of 20 items
                low_stock_items.append({
                    'type': 'raw_material',
                    'name': material.material_name,
                    'variant': f"Type: {material.material_type.material_type_name}",
                    'current_stock': float(material.current_quantity),
                    'threshold': float(reorder_level)
                })
        
        return low_stock_items
