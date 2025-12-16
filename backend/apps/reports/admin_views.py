"""
Admin views for reports management.

Provides web views for:
- Reports dashboard with various report options
- Sales reports with date filtering
- Order reports and analytics
- Financial reports
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

from apps.users.permissions import AdminRequiredMixin
from apps.orders.models import Order, OrderItem
from apps.finance.models import Payment
from apps.products.models import Product, ProductVariant
from services.order_service import OrderService
from .utils import (
    generate_sales_report_pdf, generate_order_analytics_pdf, 
    generate_financial_report_pdf, generate_invoice_pdf
)


def get_date_range_filter(start_date, end_date, field_name):
    """
    Helper function to create proper datetime range filters that handle timezones correctly.
    
    Args:
        start_date: date object for start
        end_date: date object for end  
        field_name: name of the datetime field to filter on
        
    Returns:
        dict: Filter kwargs for Django ORM
    """
    # Convert dates to datetime ranges with proper timezone handling
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    return {
        f'{field_name}__gte': start_datetime,
        f'{field_name}__lte': end_datetime
    }


class AdminReportsListView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Admin reports dashboard page.
    
    Shows available reports and quick stats.
    """
    
    def get(self, request):
        # Calculate quick stats for the dashboard
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # Order statistics with proper timezone handling
        total_orders = Order.objects.count()
        
        # This month orders
        this_month_filter = get_date_range_filter(this_month_start, today, 'order_date')
        this_month_orders = Order.objects.filter(**this_month_filter).count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        # If no orders this month, show recent orders instead
        if this_month_orders == 0:
            # Show orders from last 30 days, or all orders if none in last 30 days
            recent_start = today - timedelta(days=30)
            recent_filter = get_date_range_filter(recent_start, today, 'order_date')
            recent_orders = Order.objects.filter(**recent_filter).count()
            if recent_orders == 0:
                this_month_orders = total_orders  # Show all orders if no recent ones
        
        # Revenue statistics (using order totals)
        try:
            # Calculate total revenue from all completed orders
            completed_orders = Order.objects.filter(
                status__in=['delivered', 'dispatched']
            ).prefetch_related('items')
            
            total_revenue = Decimal('0.00')
            for order in completed_orders:
                total_revenue += order.total_amount
            
            # This month revenue (or recent revenue if no orders this month)
            this_month_filter = get_date_range_filter(this_month_start, today, 'order_date')
            this_month_completed = Order.objects.filter(
                status__in=['delivered', 'dispatched'],
                **this_month_filter
            ).prefetch_related('items')
            
            this_month_revenue = Decimal('0.00')
            for order in this_month_completed:
                this_month_revenue += order.total_amount
            
            # If no revenue this month, calculate from recent orders
            if this_month_revenue == Decimal('0.00'):
                recent_start = today - timedelta(days=30)
                recent_filter = get_date_range_filter(recent_start, today, 'order_date')
                recent_completed = Order.objects.filter(
                    status__in=['delivered', 'dispatched'],
                    **recent_filter
                ).prefetch_related('items')
                
                for order in recent_completed:
                    this_month_revenue += order.total_amount
                
        except Exception as e:
            messages.warning(request, f"Could not calculate revenue: {str(e)}")
            total_revenue = Decimal('0.00')
            this_month_revenue = Decimal('0.00')
        
        # Payment statistics
        successful_payments = Payment.objects.filter(payment_status='success').count()
        pending_payments = Payment.objects.filter(payment_status='pending').count()
        
        # Product statistics
        total_products = Product.objects.count()
        total_variants = ProductVariant.objects.count()
        
        context = {
            'total_orders': total_orders,
            'this_month_orders': this_month_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'this_month_revenue': this_month_revenue,
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'total_products': total_products,
            'total_variants': total_variants,
        }
        
        return render(request, 'reports/admin/dashboard.html', context)


class AdminSalesReportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Admin sales report page with filtering options.
    """
    
    def get(self, request):
        # Get filter parameters
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        status_filter = request.GET.get('status', '')
        
        # Default to a range that includes existing data if no dates provided
        if not start_date or not end_date:
            # Check if we have any orders to determine a good date range
            first_order = Order.objects.order_by('order_date').first()
            last_order = Order.objects.order_by('-order_date').first()
            
            if first_order and last_order:
                # Use the range from first to last order
                start_date = first_order.order_date.date()
                end_date = last_order.order_date.date()
            else:
                # Fallback to last 30 days if no orders
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        
        # Base queryset with proper timezone handling
        date_filter = get_date_range_filter(start_date, end_date, 'order_date')
        orders = Order.objects.filter(
            **date_filter
        ).select_related('user').prefetch_related('items')
        
        # Apply status filter
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        # Calculate statistics
        total_orders = orders.count()
        
        # Calculate total revenue
        total_revenue = Decimal('0.00')
        orders_data = []
        
        for order in orders:
            order_total = order.total_amount
            total_revenue += order_total
            orders_data.append({
                'order': order,
                'total': order_total
            })
        
        # Calculate average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0.00')
        
        # Status breakdown
        status_breakdown = {}
        for status_code, status_label in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            if count > 0:
                status_breakdown[status_label] = count
        
        # Top products (by quantity sold)
        top_products = OrderItem.objects.filter(
            order__in=orders
        ).values(
            'variant_size__variant__product__product_name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('snapshot_unit_price')
        ).order_by('-total_quantity')[:10]
        
        context = {
            'start_date': start_date,
            'end_date': end_date,
            'status_filter': status_filter,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'orders_data': orders_data,
            'status_breakdown': status_breakdown,
            'top_products': top_products,
            'status_choices': Order.STATUS_CHOICES,
        }
        
        return render(request, 'reports/admin/sales_report.html', context)
    
    def post(self, request):
        """Handle PDF download requests"""
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        status_filter = request.POST.get('status_filter', '')
        
        if not start_date_str or not end_date_str:
            messages.error(request, "Please provide both start and end dates.")
            return redirect('admin-sales-report')
        
        try:
            # Convert string dates to date objects
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Generate PDF report
            pdf_buffer = generate_sales_report_pdf(start_date, end_date, status_filter)
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date_str}_to_{end_date_str}.pdf"'
            return response
            
        except Exception as e:
            messages.error(request, f"Error generating PDF report: {str(e)}")
            return redirect('admin-sales-report')


class AdminOrderReportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Admin order analytics and reports.
    """
    
    def get(self, request):
        # Get filter parameters
        period = request.GET.get('period', '30')  # days
        
        try:
            days = int(period)
        except ValueError:
            days = 30
        
        # Calculate date range - if no recent orders, use all-time data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Check if we have any orders in this range
        orders_in_range = Order.objects.filter(
            order_date__date__gte=start_date,
            order_date__date__lte=end_date
        ).exists()
        
        # If no orders in default range, expand to include all orders
        if not orders_in_range:
            first_order = Order.objects.order_by('order_date').first()
            if first_order:
                start_date = first_order.order_date.date()
                # Update days for display purposes
                days = (end_date - start_date).days
        
        # Order statistics with proper timezone handling
        date_filter = get_date_range_filter(start_date, end_date, 'order_date')
        orders = Order.objects.filter(
            **date_filter
        ).select_related('user').prefetch_related('items')
        
        # Daily order counts with proper timezone handling
        daily_orders = {}
        current_date = start_date
        while current_date <= end_date:
            daily_filter = get_date_range_filter(current_date, current_date, 'order_date')
            daily_orders[current_date] = orders.filter(**daily_filter).count()
            current_date += timedelta(days=1)
        
        # Status distribution
        status_counts = {}
        for status_code, status_label in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            status_counts[status_label] = count
        
        # Customer analysis
        top_customers = orders.values(
            'user__full_name', 'user__email'
        ).annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:10]
        
        # Calculate revenue by customer
        customer_revenue = {}
        for order in orders:
            customer_key = f"{order.user.full_name} ({order.user.email})"
            if customer_key not in customer_revenue:
                customer_revenue[customer_key] = Decimal('0.00')
            customer_revenue[customer_key] += order.total_amount
        
        # Sort by revenue
        top_customers_by_revenue = sorted(
            customer_revenue.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        context = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_orders': orders.count(),
            'daily_orders': daily_orders,
            'status_counts': status_counts,
            'top_customers': top_customers,
            'top_customers_by_revenue': top_customers_by_revenue,
        }
        
        return render(request, 'reports/admin/order_report.html', context)
    
    def post(self, request):
        """Handle PDF download requests"""
        period = request.POST.get('period', '30')
        
        try:
            days = int(period)
        except ValueError:
            days = 30
        
        try:
            # Generate PDF report
            pdf_buffer = generate_order_analytics_pdf(days)
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="order_analytics_{days}days.pdf"'
            return response
            
        except Exception as e:
            messages.error(request, f"Error generating PDF report: {str(e)}")
            return redirect('admin-order-report')


class AdminFinancialReportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Admin financial reports and analytics.
    """
    
    def get(self, request):
        # Get filter parameters
        period = request.GET.get('period', '30')  # days
        
        try:
            days = int(period)
        except ValueError:
            days = 30
        
        # Calculate date range - if no recent payments, use all-time data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Check if we have any payments in this range
        payments_in_range = Payment.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).exists()
        
        # If no payments in default range, expand to include all payments
        if not payments_in_range:
            first_payment = Payment.objects.order_by('created_at').first()
            if first_payment:
                start_date = first_payment.created_at.date()
                # Update days for display purposes
                days = (end_date - start_date).days
        
        # Payment statistics with proper timezone handling
        date_filter = get_date_range_filter(start_date, end_date, 'created_at')
        payments = Payment.objects.filter(
            **date_filter
        ).select_related('order')
        
        # Payment status breakdown
        payment_status_counts = {}
        for status in ['success', 'pending', 'failed']:
            count = payments.filter(payment_status=status).count()
            payment_status_counts[status.title()] = count
        
        # Payment type breakdown
        payment_type_counts = {}
        for payment_type in ['advance', 'final']:
            count = payments.filter(payment_type=payment_type).count()
            payment_type_counts[payment_type.title()] = count
        
        # Revenue by payment type
        advance_revenue = Decimal('0.00')
        final_revenue = Decimal('0.00')
        
        for payment in payments.filter(payment_status='success'):
            if payment.payment_type == 'advance':
                advance_revenue += payment.amount
            elif payment.payment_type == 'final':
                final_revenue += payment.amount
        
        total_revenue = advance_revenue + final_revenue
        
        # Daily revenue with proper timezone handling
        daily_revenue = {}
        current_date = start_date
        while current_date <= end_date:
            daily_filter = get_date_range_filter(current_date, current_date, 'created_at')
            daily_total = payments.filter(
                payment_status='success',
                **daily_filter
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            daily_revenue[current_date] = daily_total
            current_date += timedelta(days=1)
        
        # Calculate max revenue for progress bars
        max_revenue = max(daily_revenue.values()) if daily_revenue.values() else Decimal('0.00')
        
        context = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'payment_status_counts': payment_status_counts,
            'payment_type_counts': payment_type_counts,
            'advance_revenue': advance_revenue,
            'final_revenue': final_revenue,
            'total_revenue': total_revenue,
            'daily_revenue': daily_revenue,
            'max_revenue': max_revenue,
        }
        
        return render(request, 'reports/admin/financial_report.html', context)
    
    def post(self, request):
        """Handle PDF download requests"""
        period = request.POST.get('period', '30')
        
        try:
            days = int(period)
        except ValueError:
            days = 30
        
        try:
            # Generate PDF report
            pdf_buffer = generate_financial_report_pdf(days)
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="financial_report_{days}days.pdf"'
            return response
            
        except Exception as e:
            messages.error(request, f"Error generating PDF report: {str(e)}")
            return redirect('admin-financial-report')