"""
Order Service

Handles order operations including order creation from cart, stock reservation,
price snapshotting, and order status management with business logic.
"""

import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.orders.models import Cart, Order, OrderItem
from apps.products.models import Stock, VariantSize
from apps.users.models import Address
from services.base import BaseService
from services.cart_service import CartService
from services.utils import calculate_price_with_markup


logger = logging.getLogger(__name__)


class OrderService(BaseService):
    """
    Service class for managing order operations.
    
    Provides methods for:
    - Creating orders from carts with atomic transactions
    - Stock reservation during order creation
    - Price snapshotting for order items
    - Order status updates with business logic
    - Stock validation before order creation
    """
    
    @classmethod
    def create_order_from_cart(
        cls,
        user,
        cart_id: int,
        delivery_address_id: int
    ) -> Dict[str, Any]:
        """
        Create an order from a cart with atomic transaction handling.
        
        This method performs the following operations atomically:
        1. Validate cart exists and belongs to user
        2. Validate delivery address
        3. Validate stock availability for all items
        4. Create order record
        5. Create order items with price snapshotting
        6. Reserve stock for all items
        7. Mark cart as checked out
        
        If any step fails, all changes are rolled back.
        
        Args:
            user: The user creating the order
            cart_id: The ID of the cart to convert to order
            delivery_address_id: The ID of the delivery address
            
        Returns:
            A dictionary containing:
                - order: The created Order instance
                - message: Success message
                
        Raises:
            ValidationError: If validation fails or stock is insufficient
        """
        cls.log_info(f"Starting order creation for user {user.id}, cart {cart_id}")
        
        # Execute all operations in a single atomic transaction
        def _create_order():
            # 1. Validate and get cart
            try:
                cart = Cart.objects.prefetch_related(
                    'items__variant_size__variant__product',
                    'items__variant_size__size',
                    'items__variant_size__stock_record'
                ).get(id=cart_id, user=user, status='active')
            except Cart.DoesNotExist:
                cls.log_error(f"Cart {cart_id} not found for user {user.id}")
                raise ValidationError("Cart not found or already checked out")
            
            # Check cart is not empty
            if not cart.items.exists():
                cls.log_error(f"Cart {cart_id} is empty")
                raise ValidationError("Cannot create order from empty cart")
            
            # 2. Validate delivery address
            try:
                delivery_address = Address.objects.get(
                    id=delivery_address_id,
                    user=user
                )
            except Address.DoesNotExist:
                cls.log_error(
                    f"Address {delivery_address_id} not found for user {user.id}"
                )
                raise ValidationError("Delivery address not found")
            
            # 3. Validate stock availability for all items
            stock_errors = []
            for cart_item in cart.items.all():
                stock = cls._get_stock_record(cart_item.variant_size)
                available = stock.quantity_available
                
                if available < cart_item.quantity:
                    product_name = cart_item.variant_size.variant.product.product_name
                    size_code = cart_item.variant_size.size.size_code
                    error_msg = (
                        f"{product_name} ({size_code}): "
                        f"Requested {cart_item.quantity}, only {available} available"
                    )
                    stock_errors.append(error_msg)
            
            if stock_errors:
                cls.log_error(f"Stock validation failed: {stock_errors}")
                raise ValidationError({
                    'stock_errors': stock_errors,
                    'message': 'Insufficient stock for one or more items'
                })
            
            # 4. Create order record
            order = Order.objects.create(
                user=user,
                delivery_address=delivery_address,
                status='pending'
            )
            cls.log_info(f"Created order {order.id}")
            
            # 5. Create order items with price snapshotting and reserve stock
            for cart_item in cart.items.all():
                # Calculate current price (snapshot)
                variant = cart_item.variant_size.variant
                size = cart_item.variant_size.size
                
                base_price = variant.base_price
                markup_percentage = size.size_markup_percentage
                snapshot_price = calculate_price_with_markup(
                    base_price,
                    markup_percentage
                )
                
                # Create order item
                order_item = OrderItem.objects.create(
                    order=order,
                    variant_size=cart_item.variant_size,
                    quantity=cart_item.quantity,
                    snapshot_unit_price=snapshot_price
                )
                cls.log_debug(
                    f"Created order item {order_item.id} with snapshot price {snapshot_price}"
                )
                
                # 6. Reserve stock atomically
                stock = cls._get_stock_record(cart_item.variant_size)
                stock.quantity_reserved += cart_item.quantity
                stock.save()
                cls.log_debug(
                    f"Reserved {cart_item.quantity} units for variant_size {cart_item.variant_size.id}"
                )
            
            # 7. Mark cart as checked out
            cart.status = 'checked_out'
            cart.save()
            cls.log_info(f"Marked cart {cart_id} as checked out")
            
            return order
        
        # Execute in transaction
        try:
            order = cls.execute_in_transaction(_create_order)
            cls.log_info(f"Successfully created order {order.id}")
            
            return {
                'order': order,
                'message': 'Order created successfully'
            }
        except ValidationError:
            raise
        except Exception as e:
            cls.log_error(f"Order creation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create order: {str(e)}")
    
    @classmethod
    def update_order_status(
        cls,
        order_id: int,
        new_status: str,
        user,
        notes: Optional[str] = None
    ) -> Order:
        """
        Update order status with business logic validation.
        
        Business rules:
        - Only admins can update order status
        - Status transitions must be valid
        - Dispatched status requires final payment completion
        - Processing status triggers material deduction (handled elsewhere)
        
        Args:
            order_id: The ID of the order to update
            new_status: The new status value
            user: The user performing the update (must be admin)
            notes: Optional notes about the status change
            
        Returns:
            The updated Order instance
            
        Raises:
            ValidationError: If validation fails or user lacks permissions
        """
        # Verify user is admin
        if user.user_type != 'admin':
            cls.log_error(f"Non-admin user {user.id} attempted to update order status")
            raise ValidationError("Only administrators can update order status")
        
        # Get order
        try:
            order = Order.objects.select_related('user', 'delivery_address').get(
                id=order_id
            )
        except Order.DoesNotExist:
            cls.log_error(f"Order {order_id} not found")
            raise ValidationError("Order not found")
        
        # Validate status value
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            cls.log_error(f"Invalid status: {new_status}")
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Business logic: Dispatched requires final payment
        if new_status == 'dispatched':
            # Check if final payment exists and is successful
            from apps.finance.models import Payment
            
            final_payment = Payment.objects.filter(
                order=order,
                payment_type='final'
            ).first()
            
            if not final_payment or final_payment.payment_status != 'success':
                cls.log_error(
                    f"Cannot dispatch order {order_id}: final payment not completed"
                )
                raise ValidationError(
                    "Order cannot be dispatched without successful final payment"
                )
        
        # Update status
        old_status = order.status
        order.status = new_status
        
        if notes:
            order.notes = notes if not order.notes else f"{order.notes}\n{notes}"
        
        order.save()
        
        cls.log_info(
            f"Updated order {order_id} status from {old_status} to {new_status}"
        )
        
        return order
    
    @classmethod
    def cancel_order(
        cls,
        order_id: int,
        user,
        reason: Optional[str] = None
    ) -> Order:
        """
        Cancel an order and release reserved stock.
        
        Args:
            order_id: The ID of the order to cancel
            user: The user canceling the order
            reason: Optional cancellation reason
            
        Returns:
            The cancelled Order instance
            
        Raises:
            ValidationError: If order cannot be cancelled
        """
        def _cancel_order():
            try:
                order = Order.objects.prefetch_related(
                    'items__variant_size__stock_record'
                ).get(id=order_id)
            except Order.DoesNotExist:
                cls.log_error(f"Order {order_id} not found")
                raise ValidationError("Order not found")
            
            # Verify user can cancel (owner or admin)
            if order.user != user and user.user_type != 'admin':
                cls.log_error(
                    f"User {user.id} attempted to cancel order {order_id} without permission"
                )
                raise ValidationError("You do not have permission to cancel this order")
            
            # Check if order can be cancelled
            if order.status in ['dispatched', 'delivered', 'cancelled']:
                cls.log_error(
                    f"Cannot cancel order {order_id} with status {order.status}"
                )
                raise ValidationError(
                    f"Cannot cancel order with status '{order.status}'"
                )
            
            # Release reserved stock
            for order_item in order.items.all():
                stock = cls._get_stock_record(order_item.variant_size)
                stock.quantity_reserved -= order_item.quantity
                
                # Ensure reserved doesn't go negative
                if stock.quantity_reserved < 0:
                    stock.quantity_reserved = 0
                
                stock.save()
                cls.log_debug(
                    f"Released {order_item.quantity} units for variant_size {order_item.variant_size.id}"
                )
            
            # Update order status
            order.status = 'cancelled'
            if reason:
                order.notes = reason if not order.notes else f"{order.notes}\n{reason}"
            order.save()
            
            cls.log_info(f"Cancelled order {order_id}")
            
            return order
        
        return cls.execute_in_transaction(_cancel_order)
    
    @classmethod
    def get_order_total(cls, order_id: int) -> Dict[str, Decimal]:
        """
        Calculate the total amount for an order including tax.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            A dictionary containing:
                - subtotal: Total before tax
                - tax_amount: Tax amount
                - tax_percentage: Tax percentage applied
                - total: Total including tax
        """
        try:
            order = Order.objects.prefetch_related('items').get(id=order_id)
        except Order.DoesNotExist:
            cls.log_error(f"Order {order_id} not found")
            raise ValidationError("Order not found")
        
        # Calculate subtotal from order items (using snapshot prices)
        subtotal = Decimal('0.00')
        for item in order.items.all():
            subtotal += item.snapshot_unit_price * item.quantity
        
        # Get tax configuration at order date
        from apps.finance.models import TaxConfiguration
        from django.db.models import Q
        
        order_date = order.order_date.date()
        tax_config = TaxConfiguration.objects.filter(
            is_active=True,
            effective_from__lte=order_date
        ).filter(
            Q(effective_to__gte=order_date) | Q(effective_to__isnull=True)
        ).order_by('-effective_from').first()
        
        tax_percentage = tax_config.tax_percentage if tax_config else Decimal('0.00')
        
        # Calculate tax and total
        from services.utils import calculate_total_with_tax
        tax_amount, total = calculate_total_with_tax(subtotal, tax_percentage)
        
        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'tax_percentage': tax_percentage,
            'total': total
        }
    
    @staticmethod
    def _get_stock_record(variant_size: VariantSize) -> Stock:
        """
        Get the Stock record for a VariantSize.
        
        Args:
            variant_size: The VariantSize instance
            
        Returns:
            The Stock instance
            
        Raises:
            ValidationError: If stock record doesn't exist
        """
        try:
            return variant_size.stock_record
        except Stock.DoesNotExist:
            logger.error(f"Stock record not found for variant_size {variant_size.id}")
            raise ValidationError(
                f"Stock record not found for variant size {variant_size.id}"
            )
