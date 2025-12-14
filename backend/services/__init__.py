"""
Service Layer for Vaitikan E-commerce Platform

This package contains business logic services that handle complex operations
and transactions, separated from views for maintainability and testability.
"""

from .base import BaseService
from .utils import generate_sku, calculate_price_with_markup, calculate_tax

__all__ = [
    'BaseService',
    'generate_sku',
    'calculate_price_with_markup',
    'calculate_tax',
]
