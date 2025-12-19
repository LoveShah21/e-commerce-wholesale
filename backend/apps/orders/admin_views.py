"""
Admin views for order management.

Provides web views for:
- Order list with filters
- Order detail with material requirements
- Order status updates
- Payment status tracking
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from decimal import Decimal

from .models import Order, OrderItem
from apps.finance.models import Payment
from apps.users.permissions import AdminRequiredMixin, AdminOrOperatorRequiredMixin
from apps.manufacturing.services import ManufacturingService
from services.order_service import OrderService
from services.payment_service import PaymentService


class AdminOrderListView(LoginRequiredMixin, AdminOrOperatorRequiredMixin, View):
    """
    Admin order list page with filters.
    
    Validates: Requirements 8.1
    """
    
    def get(self, request):
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        payment_status = request.GET.get('payment_status', '')
        
        # Base queryset with proper prefetching for total_amount calculation
        orders = Order.objects.select_related(
            'user', 'delivery_address'
        ).prefetch_related(
            'items',  # This is needed for the total_amount property
            'items__variant_size__variant__product',
            'items__variant_size__size'
        ).order_by('-order_date')
        
        # Apply filters
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        if search_query:
            orders = orders.filter(
                Q(id__icontains=search_query) |
                Q(user__full_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        if date_from:
            orders = orders.filter(order_date__gte=date_from)
        
        if date_to:
            orders = orders.filter(order_date__lte=date_to)
        
        # Filter by payment status
        if payment_status:
            if payment_status == 'advance_paid':
                # Orders with successful advance payment
                advance_payment_ids = Payment.objects.filter(
                    payment_type='advance',
                    payment_status='success'
                ).values_list('order_id', flat=True)
                orders = orders.filter(id__in=advance_payment_ids)
            elif payment_status == 'final_paid':
                # Orders with successful final payment
                final_payment_ids = Payment.objects.filter(
                    payment_type='final',
                    payment_status='success'
                ).values_list('order_id', flat=True)
                orders = orders.filter(id__in=final_payment_ids)
            elif payment_status == 'fully_paid':
                # Orders with both payments successful
                advance_ids = set(Payment.objects.filter(
                    payment_type='advance',
                    payment_status='success'
                ).values_list('order_id', flat=True))
                final_ids = set(Payment.objects.filter(
                    payment_type='final',
                    payment_status='success'
                ).values_list('order_id', flat=True))
                fully_paid_ids = advance_ids.intersection(final_ids)
                orders = orders.filter(id__in=fully_paid_ids)
            elif payment_status == 'pending':
                # Orders without successful advance payment
                advance_payment_ids = Payment.objects.filter(
                    payment_type='advance',
                    payment_status='success'
                ).values_list('order_id', flat=True)
                orders = orders.exclude(id__in=advance_payment_ids)
        
        # Pagination
        paginator = Paginator(orders, 20)  # 20 orders per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add payment status to each order
        orders_with_totals = []
        for order in page_obj:
            # Get payment status
            advance_payment = Payment.objects.filter(
                order=order,
                payment_type='advance',
                payment_status='success'
            ).first()
            final_payment = Payment.objects.filter(
                order=order,
                payment_type='final',
                payment_status='success'
            ).first()
            
            order.advance_paid = advance_payment is not None
            order.final_paid = final_payment is not None
            order.fully_paid = order.advance_paid and order.final_paid
            
            orders_with_totals.append(order)
        
        # Status choices for filter dropdown
        status_choices = Order.STATUS_CHOICES
        
        context = {
            'page_obj': page_obj,
            'orders': orders_with_totals,
            'status_choices': status_choices,
            'status_filter': status_filter,
            'search_query': search_query,
            'date_from': date_from,
            'date_to': date_to,
            'payment_status': payment_status,
        }
        
        return render(request, 'orders/admin/list.html', context)


class AdminOrderDetailView(LoginRequiredMixin, AdminOrOperatorRequiredMixin, View):
    """
    Admin order detail page with material requirements and payment tracking.
    
    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 10.5
    """
    
    def get(self, request, order_id):
        order = get_object_or_404(
            Order.objects.select_related(
                'user', 'delivery_address', 'delivery_address__postal_code__city',
                'delivery_address__postal_code__city__state', 'delivery_address__postal_code__city__state__country'
            ).prefetch_related(
                'items__variant_size__variant__product',
                'items__variant_size__variant__fabric',
                'items__variant_size__variant__color',
                'items__variant_size__variant__pattern',
                'items__variant_size__variant__sleeve',
                'items__variant_size__variant__pocket',
                'items__variant_size__size'
            ),
            id=order_id
        )
        
        # Get order totals
        try:
            totals = OrderService.get_order_total(order_id)
        except Exception as e:
            messages.error(request, f"Error calculating order total: {str(e)}")
            totals = {
                'subtotal': Decimal('0.00'),
                'tax_amount': Decimal('0.00'),
                'tax_percentage': Decimal('0.00'),
                'total': Decimal('0.00')
            }
        
        # Get payment information
        payments = Payment.objects.filter(order=order).order_by('-created_at')
        
        advance_payment = payments.filter(payment_type='advance').first()
        final_payment = payments.filter(payment_type='final').first()
        
        payment_completion = PaymentService.check_payment_completion(order_id)
        
        # Get material requirements
        material_requirements = None
        material_feasibility = None
        try:
            material_data = ManufacturingService.get_order_material_requirements(order_id)
            material_requirements = material_data['requirements']
            material_feasibility = {
                'is_feasible': material_data['is_feasible'],
                'missing_materials': material_data['missing_materials']
            }
        except Exception as e:
            messages.warning(request, f"Could not load material requirements: {str(e)}")
        
        context = {
            'order': order,
            'totals': totals,
            'payments': payments,
            'advance_payment': advance_payment,
            'final_payment': final_payment,
            'payment_completion': payment_completion,
            'material_requirements': material_requirements,
            'material_feasibility': material_feasibility,
            'status_choices': Order.STATUS_CHOICES,
        }
        
        return render(request, 'orders/admin/detail.html', context)
    
    def post(self, request, order_id):
        """Handle order status updates"""
        order = get_object_or_404(Order, id=order_id)
        
        action = request.POST.get('action')
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')
            
            try:
                OrderService.update_order_status(
                    order_id=order_id,
                    new_status=new_status,
                    user=request.user,
                    notes=notes
                )
                messages.success(request, f'Order status updated to {new_status}')
                
                # If status is processing, consume materials
                if new_status == 'processing':
                    try:
                        ManufacturingService.consume_materials_for_order(order)
                        messages.success(request, 'Materials consumed for production')
                    except Exception as e:
                        messages.error(request, f'Error consuming materials: {str(e)}')
                
            except Exception as e:
                messages.error(request, f'Error updating order status: {str(e)}')
        
        elif action == 'create_advance_payment':
            try:
                payment_method = request.POST.get('payment_method', 'upi')
                result = PaymentService.create_razorpay_order(
                    order_id=order_id,
                    payment_type='advance',
                    payment_method=payment_method
                )
                messages.success(request, 'Advance payment order created')
            except Exception as e:
                messages.error(request, f'Error creating advance payment: {str(e)}')
        
        elif action == 'create_final_payment':
            try:
                payment_method = request.POST.get('payment_method', 'upi')
                result = PaymentService.create_razorpay_order(
                    order_id=order_id,
                    payment_type='final',
                    payment_method=payment_method
                )
                
                # Send email notification to customer
                from services.email_service import EmailService
                email_result = EmailService.send_final_payment_notification(
                    order_id=order_id,
                    payment_amount=float(result['payment'].amount),
                    razorpay_order_id=result['razorpay_order']['id']
                )
                
                if email_result['success']:
                    messages.success(request, 'Final payment order created and notification sent to customer')
                else:
                    messages.success(request, 'Final payment order created')
                    messages.warning(request, f'Email notification failed: {email_result["message"]}')
                    
            except Exception as e:
                messages.error(request, f'Error creating final payment: {str(e)}')
        
        return redirect('admin-order-detail', order_id=order_id)


class AdminOrderMaterialRequirementsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    View material requirements for an order.
    
    Validates: Requirements 10.5
    """
    
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        try:
            material_data = ManufacturingService.get_order_material_requirements(order_id)
            
            context = {
                'order': order,
                'requirements': material_data['requirements'],
                'is_feasible': material_data['is_feasible'],
                'missing_materials': material_data['missing_materials'],
                'total_materials_count': material_data['total_materials_count']
            }
            
            return render(request, 'orders/admin/material_requirements.html', context)
        
        except Exception as e:
            messages.error(request, f'Error loading material requirements: {str(e)}')
            return redirect('admin-order-detail', order_id=order_id)
