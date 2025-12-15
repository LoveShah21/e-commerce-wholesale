"""
Script to test logging configuration.

This script demonstrates the various logging capabilities of the system.
Run with: python manage.py shell < scripts/test_logging.py
Or: python -c "exec(open('scripts/test_logging.py').read())"
"""

import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=" * 80)
print("Testing Logging Configuration")
print("=" * 80)

# Test 1: Application Logger
print("\n1. Testing Application Logger (services)")
app_logger = logging.getLogger('services')
app_logger.info("This is an INFO message from services logger")
app_logger.warning("This is a WARNING message from services logger")
app_logger.error("This is an ERROR message from services logger")
print("✓ Application logger test complete")

# Test 2: Payment Logger
print("\n2. Testing Payment Transaction Logger")
payment_logger = logging.getLogger('services.payment_service')
payment_logger.info(
    "PAYMENT_CREATED | "
    "PaymentID: TEST123 | "
    "OrderID: TEST456 | "
    "Type: advance | "
    "Amount: ₹500.00 | "
    "Method: upi | "
    "Status: initiated"
)
payment_logger.info(
    "PAYMENT_SUCCESS | "
    "PaymentID: TEST123 | "
    "OrderID: TEST456 | "
    "Type: advance | "
    "Amount: ₹500.00 | "
    "Method: upi | "
    "RazorpayPaymentID: pay_test123 | "
    "Status: success"
)
payment_logger.warning(
    "PAYMENT_FAILED | "
    "PaymentID: TEST789 | "
    "OrderID: TEST456 | "
    "Type: final | "
    "Amount: ₹500.00 | "
    "Method: upi | "
    "Reason: Insufficient funds | "
    "Status: failed"
)
print("✓ Payment logger test complete")

# Test 3: Security Logger
print("\n3. Testing Security Logger")
security_logger = logging.getLogger('django.security')
security_logger.warning(
    "Authentication failed: POST /api/users/login/ | "
    "IP: 192.168.1.100 | "
    "User-Agent: TestAgent/1.0"
)
security_logger.warning(
    "Permission denied: GET /api/admin/dashboard | "
    "User: test@example.com (customer) | "
    "IP: 192.168.1.100"
)
print("✓ Security logger test complete")

# Test 4: Error Logger
print("\n4. Testing Error Logger")
error_logger = logging.getLogger('django.request')
error_logger.error(
    "Internal Server Error: GET /api/products/999/ | "
    "Exception: Product matching query does not exist"
)
print("✓ Error logger test complete")

# Test 5: Slow Query Logger
print("\n5. Testing Slow Query Logger")
slow_query_logger = logging.getLogger('django.db.backends')
slow_query_logger.warning(
    "Slow queries detected on GET /api/products/ | "
    "Total queries: 45 | "
    "Total time: 2.345s | "
    "Slow queries: 3"
)
slow_query_logger.warning(
    "Slow Query #1 (1.234s): SELECT * FROM products_product WHERE category_id = 1 ORDER BY created_at DESC"
)
print("✓ Slow query logger test complete")

# Test 6: Order Service Logger
print("\n6. Testing Order Service Logger")
order_logger = logging.getLogger('services.order_service')
order_logger.info("Creating order from cart | CartID: TEST123 | UserID: TEST456")
order_logger.info("Order created successfully | OrderID: TEST789 | Total: ₹1500.00")
print("✓ Order service logger test complete")

# Test 7: Cart Service Logger
print("\n7. Testing Cart Service Logger")
cart_logger = logging.getLogger('services.cart_service')
cart_logger.info("Adding item to cart | CartID: TEST123 | ProductID: TEST456 | Quantity: 2")
cart_logger.info("Cart total calculated | CartID: TEST123 | Total: ₹1000.00")
print("✓ Cart service logger test complete")

print("\n" + "=" * 80)
print("All logging tests completed successfully!")
print("=" * 80)
print("\nLog files created in backend/logs/:")
print("  - application.log (general application logs)")
print("  - errors.log (error-level logs)")
print("  - payments.log (payment transaction logs)")
print("  - security.log (security event logs)")
print("  - slow_queries.log (slow query logs)")
print("\nCheck these files to verify the logs were written correctly.")
print("=" * 80)
