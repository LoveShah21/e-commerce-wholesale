from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem
from apps.finance.models import Payment
from apps.products.models import Stock

@receiver(post_save, sender=OrderItem)
def reserve_stock(sender, instance, created, **kwargs):
    """
    When an order item is created, reserve the stock.
    """
    if created:
        variant_size = instance.variant_size
        stock, _ = Stock.objects.get_or_create(variant_size=variant_size)
        stock.quantity_reserved += instance.quantity
        stock.save()

@receiver(post_delete, sender=OrderItem)
def release_stock(sender, instance, **kwargs):
    """
    When an order item is deleted (e.g. cancelled order), release reservation.
    """
    variant_size = instance.variant_size
    try:
        stock = Stock.objects.get(variant_size=variant_size)
        stock.quantity_reserved -= instance.quantity
        if stock.quantity_reserved < 0:
            stock.quantity_reserved = 0
        stock.save()
    except Stock.DoesNotExist:
        pass

@receiver(post_save, sender=Payment)
def update_order_status_on_payment(sender, instance, created, **kwargs):
    """
    Auto-confirm order when advance payment succeeds.
    Reduce stock when final payment succeeds.
    """
    if instance.payment_status == 'success':
        order = instance.order
        
        if instance.payment_type == 'advance':
            # Advance payment successful - confirm order
            if order.status == 'pending':
                order.status = 'confirmed'
                order.save()
        
        elif instance.payment_type == 'final':
            # Final payment successful - reduce actual stock quantities
            reduce_stock_on_final_payment(order)

def reduce_stock_on_final_payment(order):
    """
    Reduce actual stock quantities when final payment is successful.
    This converts reserved stock to actual stock reduction.
    """
    for order_item in order.items.all():
        variant_size = order_item.variant_size
        quantity = order_item.quantity
        
        try:
            # Get or create stock record
            stock, _ = Stock.objects.get_or_create(variant_size=variant_size)
            
            # Reduce actual stock and reserved stock
            stock.quantity_in_stock -= quantity
            stock.quantity_reserved -= quantity
            
            # Ensure stock doesn't go negative
            if stock.quantity_in_stock < 0:
                stock.quantity_in_stock = 0
            if stock.quantity_reserved < 0:
                stock.quantity_reserved = 0
                
            stock.save()
            
            # Also update the variant_size stock_quantity for consistency
            variant_size.stock_quantity = stock.quantity_in_stock
            variant_size.save()
            
            print(f"Stock reduced for {variant_size}: -{quantity} units. New stock: {stock.quantity_in_stock}")
            
        except Exception as e:
            print(f"Error reducing stock for {variant_size}: {str(e)}")
            # Log the error but don't fail the payment process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to reduce stock for order {order.id}, item {order_item.id}: {str(e)}")
