"""
Utility Functions for Service Layer

Common utility functions for SKU generation, price calculation, and tax calculation.
"""

import uuid
import logging
from decimal import Decimal
from typing import Optional
from datetime import datetime


logger = logging.getLogger(__name__)


def generate_sku(prefix: str = "SKU") -> str:
    """
    Generate a unique SKU (Stock Keeping Unit) identifier.
    
    The SKU is generated using a combination of prefix, timestamp, and UUID
    to ensure uniqueness across the system.
    
    Args:
        prefix: Optional prefix for the SKU (default: "SKU")
        
    Returns:
        A unique SKU string in format: PREFIX-TIMESTAMP-UUID
        
    Example:
        >>> sku = generate_sku("SHIRT")
        >>> print(sku)  # SHIRT-20231214-A1B2C3D4
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8].upper()
    sku = f"{prefix}-{timestamp}-{unique_id}"
    
    logger.debug(f"Generated SKU: {sku}")
    return sku


def calculate_price_with_markup(
    base_price: Decimal,
    markup_percentage: Decimal
) -> Decimal:
    """
    Calculate final price by applying a markup percentage to the base price.
    
    The calculation follows the formula:
    final_price = base_price * (1 + markup_percentage / 100)
    
    Args:
        base_price: The base price before markup
        markup_percentage: The markup percentage to apply (e.g., 10 for 10%)
        
    Returns:
        The final price with markup applied, rounded to 2 decimal places
        
    Example:
        >>> base = Decimal('100.00')
        >>> markup = Decimal('10.00')
        >>> final = calculate_price_with_markup(base, markup)
        >>> print(final)  # 110.00
    """
    if base_price < 0:
        raise ValueError("Base price cannot be negative")
    
    if markup_percentage < 0:
        raise ValueError("Markup percentage cannot be negative")
    
    markup_multiplier = Decimal('1') + (markup_percentage / Decimal('100'))
    final_price = base_price * markup_multiplier
    
    # Round to 2 decimal places
    final_price = final_price.quantize(Decimal('0.01'))
    
    logger.debug(
        f"Calculated price: base={base_price}, markup={markup_percentage}%, "
        f"final={final_price}"
    )
    
    return final_price


def calculate_tax(
    amount: Decimal,
    tax_percentage: Decimal
) -> Decimal:
    """
    Calculate tax amount based on the given amount and tax percentage.
    
    The calculation follows the formula:
    tax_amount = amount * (tax_percentage / 100)
    
    Args:
        amount: The amount to calculate tax on
        tax_percentage: The tax percentage to apply (e.g., 18 for 18% GST)
        
    Returns:
        The tax amount, rounded to 2 decimal places
        
    Example:
        >>> amount = Decimal('1000.00')
        >>> tax_rate = Decimal('18.00')
        >>> tax = calculate_tax(amount, tax_rate)
        >>> print(tax)  # 180.00
    """
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    
    if tax_percentage < 0:
        raise ValueError("Tax percentage cannot be negative")
    
    tax_amount = amount * (tax_percentage / Decimal('100'))
    
    # Round to 2 decimal places
    tax_amount = tax_amount.quantize(Decimal('0.01'))
    
    logger.debug(
        f"Calculated tax: amount={amount}, tax_rate={tax_percentage}%, "
        f"tax_amount={tax_amount}"
    )
    
    return tax_amount


def calculate_total_with_tax(
    subtotal: Decimal,
    tax_percentage: Decimal
) -> tuple[Decimal, Decimal]:
    """
    Calculate tax amount and total amount including tax.
    
    Args:
        subtotal: The subtotal amount before tax
        tax_percentage: The tax percentage to apply
        
    Returns:
        A tuple of (tax_amount, total_amount)
        
    Example:
        >>> subtotal = Decimal('1000.00')
        >>> tax_rate = Decimal('18.00')
        >>> tax, total = calculate_total_with_tax(subtotal, tax_rate)
        >>> print(f"Tax: {tax}, Total: {total}")  # Tax: 180.00, Total: 1180.00
    """
    tax_amount = calculate_tax(subtotal, tax_percentage)
    total_amount = subtotal + tax_amount
    
    return tax_amount, total_amount
