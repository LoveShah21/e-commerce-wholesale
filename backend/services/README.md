# Service Layer

This directory contains the service layer for the Vaitikan E-commerce Platform. The service layer implements business logic separated from views for better maintainability and testability.

## Structure

- `base.py` - Base service class with transaction handling and logging utilities
- `utils.py` - Common utility functions (SKU generation, price calculation, tax calculation)
- `tests/` - Unit tests for service layer components

## Base Service Class

The `BaseService` class provides:

- **Transaction Management**: `execute_in_transaction()` method for atomic operations
- **Logging Utilities**: Consistent logging with service class names
- **Error Handling**: Automatic rollback on transaction failures

### Usage Example

```python
from services.base import BaseService

class OrderService(BaseService):
    @classmethod
    def create_order(cls, cart_id, user_id):
        def _create():
            # Business logic here
            cls.log_info(f"Creating order for cart {cart_id}")
            # ... order creation logic
            return order

        return cls.execute_in_transaction(_create)
```

## Utility Functions

### SKU Generation

```python
from services.utils import generate_sku

sku = generate_sku("SHIRT")  # Returns: SHIRT-20231214-A1B2C3D4
```

### Price Calculation with Markup

```python
from decimal import Decimal
from services.utils import calculate_price_with_markup

base_price = Decimal('100.00')
markup = Decimal('10.00')  # 10%
final_price = calculate_price_with_markup(base_price, markup)  # 110.00
```

### Tax Calculation

```python
from decimal import Decimal
from services.utils import calculate_tax, calculate_total_with_tax

amount = Decimal('1000.00')
tax_rate = Decimal('18.00')  # 18% GST

# Calculate tax only
tax = calculate_tax(amount, tax_rate)  # 180.00

# Calculate tax and total together
tax, total = calculate_total_with_tax(amount, tax_rate)  # (180.00, 1180.00)
```

## Testing

Run unit tests for the service layer:

```bash
python manage.py test services.tests
```

Run specific test class:

```bash
python manage.py test services.tests.test_utils.TestSKUGeneration
```

## Logging Configuration

Logging is configured in `config/settings.py`:

- **Console Handler**: INFO level, simple format
- **File Handler**: INFO level, verbose format (logs/application.log)
- **Error File Handler**: ERROR level, verbose format (logs/errors.log)

Service layer logs are written to the `services` logger with DEBUG level in development and INFO level in production.
