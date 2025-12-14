"""
Base Service Class

Provides common functionality for all service classes including
transaction handling and logging.
"""

import logging
from django.db import transaction
from typing import Callable, Any


logger = logging.getLogger(__name__)


class BaseService:
    """
    Base service class that provides transaction handling and logging.
    
    All service classes should inherit from this base class to ensure
    consistent transaction management and error handling.
    """
    
    @staticmethod
    def execute_in_transaction(func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function within a database transaction.
        
        If any exception occurs during execution, the transaction will be
        rolled back automatically. This ensures atomicity for critical operations.
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The return value of the executed function
            
        Raises:
            Any exception raised by the function will be propagated after rollback
        """
        try:
            with transaction.atomic():
                logger.debug(f"Starting transaction for {func.__name__}")
                result = func(*args, **kwargs)
                logger.debug(f"Transaction completed successfully for {func.__name__}")
                return result
        except Exception as e:
            logger.error(f"Transaction failed for {func.__name__}: {str(e)}")
            raise
    
    @classmethod
    def log_info(cls, message: str) -> None:
        """Log an info message with the service class name."""
        logger.info(f"[{cls.__name__}] {message}")
    
    @classmethod
    def log_error(cls, message: str, exc_info: bool = False) -> None:
        """Log an error message with the service class name."""
        logger.error(f"[{cls.__name__}] {message}", exc_info=exc_info)
    
    @classmethod
    def log_warning(cls, message: str) -> None:
        """Log a warning message with the service class name."""
        logger.warning(f"[{cls.__name__}] {message}")
    
    @classmethod
    def log_debug(cls, message: str) -> None:
        """Log a debug message with the service class name."""
        logger.debug(f"[{cls.__name__}] {message}")
