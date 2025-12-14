"""
Cart Service

Handles shopping cart operations including adding items, updating quantities,
calculating totals with tax, and managing cart persistence.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction, models
from django.core.exceptions import ValidationError

from apps.orders.models import Cart, CartItem
from apps.products.models import VariantSize, Stock
from apps.finance.models import TaxConfiguration
from services.base import BaseService
from services.utils import calculate_total_with_tax


logger = logging.getLogger(__name__)


class CartService(BaseService):
    """
    Service class for managing shopping cart operations.
    
    Provides methods for cart management including:
    - Getting or creating carts
    - Adding items with stock validation
    - Updating item quantities with stock checking
    - Calculating cart totals with tax
    - Cart persistence across sessions
    """
    
    @classmethod
    def get_or_create_cart(cls, user) -> Cart:
        """
        Get the active cart for a user or create a new one.
        
        Args:
            user: The user object
            
        Returns:
            The active Cart instance for the user
        """
        cart, created = Cart.objects.get_or_create(
            user=user,
            status='active',
            defaults={'user': user}
        )
        
        if created:
            cls.log_info(f"Created new cart {cart.id} for user {user.id}")
        else:
            cls.log_debug(f"Retrieved existing cart {cart.id} for user {user.id}")
            
        return cart
    
    @classmethod
    def add_to_cart(
        cls,
        user,
        variant_size_id: int,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Add an item to the cart with stock validation.
        
        If the item already exists in the cart, the quantity is updated.
        This operation is idempotent - adding the same item twice updates
        the quantity rather than creating duplicates.
        
        Args:
            user: The user object
            variant_size_id: The ID of the VariantSize to add
            quantity: The quantity to add
            
        Returns:
            A dictionary containing the cart item and success status
            
        Raises:
            ValidationError: If stock is insufficient or variant_size doesn't exist
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        
        try:
            variant_size = VariantSize.objects.select_related(
                'variant', 'size', 'stock_record'
            ).get(id=variant_size_id)
        except VariantSize.DoesNotExist:
            cls.log_error(f"VariantSize {variant_size_id} not found")
            raise ValidationError("Product variant not found")
        
        # Check stock availability
        stock = cls._get_or_create_stock(variant_size)
        available_stock = stock.quantity_available
        
        if available_stock < quantity:
            cls.log_warning(
                f"Insufficient stock for variant_size {variant_size_id}: "
                f"requested={quantity}, available={available_stock}"
            )
            raise ValidationError(
                f"Insufficient stock. Only {available_stock} items available."
            )
        
        # Get or create cart
        cart = cls.get_or_create_cart(user)
        
        # Add or update cart item (idempotent operation)
        with transaction.atomic():
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                variant_size=variant_size,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Item already exists, update quantity
                new_quantity = cart_item.quantity + quantity
                
                # Validate new quantity against stock
                if available_stock < new_quantity:
                    raise ValidationError(
                        f"Insufficient stock. Only {available_stock} items available."
                    )
                
                cart_item.quantity = new_quantity
                cart_item.save()
                cls.log_info(
                    f"Updated cart item {cart_item.id} quantity to {new_quantity}"
                )
            else:
                cls.log_info(
                    f"Added new cart item {cart_item.id} with quantity {quantity}"
                )
        
        return {
            'cart_item': cart_item,
            'created': created,
            'message': 'Item added to cart successfully'
        }
    
    @classmethod
    def update_cart_item(
        cls,
        cart_item_id: int,
        quantity: int,
        user
    ) -> CartItem:
        """
        Update the quantity of a cart item with stock validation.
        
        Args:
            cart_item_id: The ID of the CartItem to update
            quantity: The new quantity
            user: The user object (for authorization)
            
        Returns:
            The updated CartItem instance
            
        Raises:
            ValidationError: If stock is insufficient or cart item doesn't exist
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        
        try:
            cart_item = CartItem.objects.select_related(
                'cart', 'variant_size', 'variant_size__stock_record'
            ).get(id=cart_item_id, cart__user=user, cart__status='active')
        except CartItem.DoesNotExist:
            cls.log_error(f"CartItem {cart_item_id} not found for user {user.id}")
            raise ValidationError("Cart item not found")
        
        # Check stock availability
        stock = cls._get_or_create_stock(cart_item.variant_size)
        available_stock = stock.quantity_available
        
        if available_stock < quantity:
            cls.log_warning(
                f"Insufficient stock for cart item {cart_item_id}: "
                f"requested={quantity}, available={available_stock}"
            )
            raise ValidationError(
                f"Insufficient stock. Only {available_stock} items available."
            )
        
        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()
        
        cls.log_info(f"Updated cart item {cart_item_id} quantity to {quantity}")
        
        return cart_item
    
    @classmethod
    def remove_cart_item(cls, cart_item_id: int, user) -> None:
        """
        Remove an item from the cart.
        
        Args:
            cart_item_id: The ID of the CartItem to remove
            user: The user object (for authorization)
            
        Raises:
            ValidationError: If cart item doesn't exist
        """
        try:
            cart_item = CartItem.objects.get(
                id=cart_item_id,
                cart__user=user,
                cart__status='active'
            )
            cart_item.delete()
            cls.log_info(f"Removed cart item {cart_item_id}")
        except CartItem.DoesNotExist:
            cls.log_error(f"CartItem {cart_item_id} not found for user {user.id}")
            raise ValidationError("Cart item not found")
    
    @classmethod
    def calculate_cart_total(cls, cart_id: int) -> Dict[str, Decimal]:
        """
        Calculate the total amount for a cart including tax.
        
        Args:
            cart_id: The ID of the Cart
            
        Returns:
            A dictionary containing:
                - subtotal: Total before tax
                - tax_amount: Tax amount
                - tax_percentage: Tax percentage applied
                - total: Total including tax
        """
        try:
            cart = Cart.objects.prefetch_related(
                'items__variant_size__variant',
                'items__variant_size__size'
            ).get(id=cart_id)
        except Cart.DoesNotExist:
            cls.log_error(f"Cart {cart_id} not found")
            raise ValidationError("Cart not found")
        
        # Calculate subtotal
        subtotal = Decimal('0.00')
        for item in cart.items.all():
            variant = item.variant_size.variant
            size = item.variant_size.size
            
            # Calculate price with size markup
            base_price = variant.base_price
            markup_percentage = size.size_markup_percentage
            item_price = base_price * (Decimal('1') + markup_percentage / Decimal('100'))
            
            subtotal += item_price * item.quantity
        
        # Get active tax configuration
        tax_config = cls._get_active_tax_config()
        tax_percentage = tax_config.tax_percentage if tax_config else Decimal('0.00')
        
        # Calculate tax and total
        tax_amount, total = calculate_total_with_tax(subtotal, tax_percentage)
        
        cls.log_debug(
            f"Cart {cart_id} totals: subtotal={subtotal}, "
            f"tax={tax_amount}, total={total}"
        )
        
        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'tax_percentage': tax_percentage,
            'total': total
        }
    
    @classmethod
    def validate_cart_stock(cls, cart_id: int) -> Dict[str, Any]:
        """
        Validate that all items in the cart have sufficient stock.
        
        Args:
            cart_id: The ID of the Cart
            
        Returns:
            A dictionary containing:
                - valid: Boolean indicating if all items have sufficient stock
                - errors: List of error messages for items with insufficient stock
        """
        try:
            cart = Cart.objects.prefetch_related(
                'items__variant_size__stock_record'
            ).get(id=cart_id)
        except Cart.DoesNotExist:
            cls.log_error(f"Cart {cart_id} not found")
            raise ValidationError("Cart not found")
        
        errors = []
        
        for item in cart.items.all():
            stock = cls._get_or_create_stock(item.variant_size)
            available_stock = stock.quantity_available
            
            if available_stock < item.quantity:
                error_msg = (
                    f"{item.variant_size.variant.product.product_name} "
                    f"({item.variant_size.size.size_code}): "
                    f"Requested {item.quantity}, only {available_stock} available"
                )
                errors.append(error_msg)
                cls.log_warning(f"Stock validation failed for cart item {item.id}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            cls.log_info(f"Cart {cart_id} stock validation passed")
        else:
            cls.log_warning(f"Cart {cart_id} stock validation failed: {errors}")
        
        return {
            'valid': is_valid,
            'errors': errors
        }
    
    @classmethod
    def clear_cart(cls, user) -> None:
        """
        Clear all items from the user's active cart.
        
        Args:
            user: The user object
        """
        cart = Cart.objects.filter(user=user, status='active').first()
        
        if cart:
            cart.items.all().delete()
            cls.log_info(f"Cleared all items from cart {cart.id}")
    
    @staticmethod
    def _get_or_create_stock(variant_size: VariantSize) -> Stock:
        """
        Get or create a Stock record for a VariantSize.
        
        Args:
            variant_size: The VariantSize instance
            
        Returns:
            The Stock instance
        """
        stock, created = Stock.objects.get_or_create(
            variant_size=variant_size,
            defaults={
                'quantity_in_stock': variant_size.stock_quantity,
                'quantity_reserved': 0
            }
        )
        
        if created:
            logger.debug(f"Created stock record for variant_size {variant_size.id}")
        
        return stock
    
    @staticmethod
    def _get_active_tax_config() -> Optional[TaxConfiguration]:
        """
        Get the currently active tax configuration.
        
        Returns:
            The active TaxConfiguration instance or None
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        tax_config = TaxConfiguration.objects.filter(
            is_active=True,
            effective_from__lte=today
        ).filter(
            models.Q(effective_to__gte=today) | models.Q(effective_to__isnull=True)
        ).order_by('-effective_from').first()
        
        return tax_config
