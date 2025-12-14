from .models import Payment
from apps.orders.models import Order
from django.db.models import Sum

class FinanceService:
    @staticmethod
    def get_order_payment_summary(order):
        """
        Calculate amount paid and pending for an order.
        """
        payments = Payment.objects.filter(order=order, payment_status='success')
        total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        total_due = order.items.aggregate(
            total=Sum(models.F('quantity') * models.F('snapshot_unit_price'))
        )['total'] or 0 # simplified logical approximation

        # In reality order total should be stored or calculated from OrderItemDetail
        # But we don't have OrderItemDetail view model in Python, so we query items.
        
        # Calculate from OrderItem
        total_order_value = 0
        for item in order.items.all():
            total_order_value += item.quantity * item.snapshot_unit_price
            
        remaining_balance = total_order_value - total_paid
        
        return {
            'total_order_value': total_order_value,
            'total_paid': total_paid,
            'remaining_balance': remaining_balance,
            'payment_status': 'fully_paid' if remaining_balance <= 0 else 'partially_paid' if total_paid > 0 else 'unpaid'
        }

    @staticmethod
    def verify_advance_payment(order):
        """
        Check if 50% advance has been paid.
        """
        summary = FinanceService.get_order_payment_summary(order)
        required_advance = summary['total_order_value'] * 0.5
        
        return summary['total_paid'] >= required_advance
