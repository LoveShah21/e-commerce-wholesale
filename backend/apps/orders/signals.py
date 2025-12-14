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
    """
    if instance.payment_status == 'success' and instance.payment_type == 'advance':
        order = instance.order
        if order.status == 'pending':
            order.status = 'confirmed'
            order.save()
