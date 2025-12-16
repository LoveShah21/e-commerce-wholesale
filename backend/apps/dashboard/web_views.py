from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from apps.orders.models import Order
from apps.products.models import Stock
from apps.finance.models import Payment
from apps.manufacturing.models import RawMaterial, MaterialSupplier

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
            
            # Get comprehensive low stock data for initial render
            low_stock_details = self.get_comprehensive_low_stock_data(10)
            
            recent_orders = Order.objects.select_related('user').order_by('-order_date')[:10]
            
            context = {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'low_stock_items': low_stock_details,  # Updated to use comprehensive data
                'low_stock_count': len(low_stock_details),
                'recent_orders': recent_orders
            }
            return render(request, 'dashboard/index.html', context)
        
        elif user.user_type == 'operator':
            # Operator dashboard: show manufacturing and inventory info
            pending_manufacturing = Order.objects.filter(status__in=['confirmed', 'processing']).count()
            
            # Get comprehensive low stock data for operator dashboard
            low_stock_details = self.get_comprehensive_low_stock_data(10)
            
            recent_orders = Order.objects.filter(status__in=['confirmed', 'processing']).select_related('user').order_by('-order_date')[:10]
            
            context = {
                'pending_manufacturing': pending_manufacturing,
                'low_stock_items': low_stock_details,
                'low_stock_count': len(low_stock_details),
                'recent_orders': recent_orders,
            }
            return render(request, 'dashboard/operator_dashboard.html', context)
        
        else:
            # Unknown role, redirect to home
            return redirect('/')
    
    def get_comprehensive_low_stock_data(self, threshold=10):
        """
        Get comprehensive low stock data for both products and raw materials.
        """
        low_stock_items = []
        
        # Get product stock alerts
        product_stock_alerts = Stock.objects.filter(
            quantity_in_stock__lte=threshold
        ).select_related(
            'variant_size__size',
            'variant_size__variant__product'
        )[:10]  # Limit to 10 product items
        
        for stock in product_stock_alerts:
            low_stock_items.append({
                'type': 'product',
                'name': stock.variant_size.variant.product.product_name,
                'variant': f"Size: {stock.variant_size.size.size_code}",
                'current_stock': stock.quantity_in_stock,
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
