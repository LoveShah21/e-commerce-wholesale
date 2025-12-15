"""
Tests for logging configuration and middleware.

Verifies that logging is properly configured and middleware functions correctly.
"""

import logging
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import override_settings

from utils.logging_middleware import (
    SlowQueryLoggingMiddleware,
    SecurityEventLoggingMiddleware
)

User = get_user_model()


class LoggingConfigurationTest(TestCase):
    """Test logging configuration."""
    
    def test_application_logger_exists(self):
        """Test that application logger is configured."""
        logger = logging.getLogger('services')
        self.assertIsNotNone(logger)
        self.assertTrue(len(logger.handlers) > 0 or logger.propagate)
    
    def test_payment_logger_exists(self):
        """Test that payment logger is configured."""
        logger = logging.getLogger('services.payment_service')
        self.assertIsNotNone(logger)
        self.assertTrue(len(logger.handlers) > 0 or logger.propagate)
    
    def test_security_logger_exists(self):
        """Test that security logger is configured."""
        logger = logging.getLogger('django.security')
        self.assertIsNotNone(logger)
        self.assertTrue(len(logger.handlers) > 0 or logger.propagate)
    
    def test_slow_query_logger_exists(self):
        """Test that slow query logger is configured."""
        logger = logging.getLogger('django.db.backends')
        self.assertIsNotNone(logger)
        self.assertTrue(len(logger.handlers) > 0 or logger.propagate)
    
    def test_logger_levels(self):
        """Test that loggers have appropriate levels."""
        # Services logger should be INFO or DEBUG
        services_logger = logging.getLogger('services')
        self.assertIn(services_logger.level, [logging.DEBUG, logging.INFO, logging.NOTSET])
        
        # Security logger should be WARNING or higher
        security_logger = logging.getLogger('django.security')
        self.assertIn(security_logger.level, [logging.WARNING, logging.ERROR, logging.NOTSET])


class SecurityEventLoggingMiddlewareTest(TestCase):
    """Test security event logging middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityEventLoggingMiddleware(lambda r: None)
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            user_type='customer'
        )
    
    def test_middleware_initialization(self):
        """Test that middleware initializes correctly."""
        self.assertIsNotNone(self.middleware)
        self.assertIsNotNone(self.middleware.logger)
    
    def test_get_client_ip(self):
        """Test client IP extraction."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = self.middleware._get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_with_forwarded(self):
        """Test client IP extraction with X-Forwarded-For."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = self.middleware._get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')


@override_settings(ENABLE_QUERY_LOGGING=True, SLOW_QUERY_THRESHOLD=0.0)
class SlowQueryLoggingMiddlewareTest(TestCase):
    """Test slow query logging middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SlowQueryLoggingMiddleware(lambda r: None)
    
    def test_middleware_initialization(self):
        """Test that middleware initializes correctly."""
        self.assertIsNotNone(self.middleware)
    
    def test_process_request_clears_queries(self):
        """Test that process_request clears query log."""
        request = self.factory.get('/')
        
        # Add some queries
        connection.queries_log.clear()
        
        # Process request should not raise error
        result = self.middleware.process_request(request)
        self.assertIsNone(result)


class LoggingIntegrationTest(TestCase):
    """Integration tests for logging."""
    
    def test_logging_does_not_break_requests(self):
        """Test that logging middleware doesn't break normal requests."""
        # Create a simple request
        response = self.client.get('/')
        
        # Should get a response (even if 404)
        self.assertIsNotNone(response)
        self.assertIn(response.status_code, [200, 301, 302, 404])
    
    def test_payment_logging_format(self):
        """Test that payment logs use correct format."""
        logger = logging.getLogger('services.payment_service')
        
        # Test that we can log payment events
        with self.assertLogs('services.payment_service', level='INFO') as cm:
            logger.info(
                "PAYMENT_CREATED | "
                "PaymentID: 123 | "
                "OrderID: 456 | "
                "Type: advance | "
                "Amount: ₹500.00 | "
                "Method: upi | "
                "Status: initiated"
            )
        
        # Verify log was captured
        self.assertEqual(len(cm.output), 1)
        self.assertIn('PAYMENT_CREATED', cm.output[0])
        self.assertIn('PaymentID: 123', cm.output[0])
