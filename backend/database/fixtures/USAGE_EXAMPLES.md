# Fixture Usage Examples

## Getting Started

### Option 1: One-Command Setup (Recommended)

```bash
cd backend
python scripts/seed_database.py
```

**Output:**

```
======================================================================
VAITIKAN DATABASE SEEDING SCRIPT
======================================================================

======================================================================
STEP 1: Loading Database Fixtures
======================================================================
✓ Database connection successful

[1/8] Loading database/fixtures/01_locations.json...
    ✓ Successfully loaded
[2/8] Loading database/fixtures/02_users.json...
    ✓ Successfully loaded
...

✓ Loaded 8/8 fixtures successfully

======================================================================
STEP 2: Setting User Passwords
======================================================================

✓ Password set for Admin        | admin@vaitikan.com
✓ Password set for Operator     | operator@vaitikan.com
✓ Password set for Customer     | rajesh.kumar@example.com
...

======================================================================
DATABASE SEEDING COMPLETE!
======================================================================
```

### Option 2: Step-by-Step Setup

```bash
cd backend

# Step 1: Load fixtures
python scripts/load_fixtures.py

# Step 2: Set passwords
python scripts/set_user_passwords.py
```

### Option 3: Manual Django Commands

```bash
cd backend

# Load each fixture individually
python manage.py loaddata database/fixtures/01_locations.json
python manage.py loaddata database/fixtures/02_users.json
python manage.py loaddata database/fixtures/03_product_attributes.json
python manage.py loaddata database/fixtures/04_products.json
python manage.py loaddata database/fixtures/05_variant_sizes_stock.json
python manage.py loaddata database/fixtures/06_orders_payments.json
python manage.py loaddata database/fixtures/07_manufacturing.json
python manage.py loaddata database/fixtures/08_support.json

# Then set passwords manually in Django shell
python manage.py shell
>>> from apps.users.models import User
>>> User.objects.get(email='admin@vaitikan.com').set_password('admin123')
>>> # ... repeat for other users
```

## Common Scenarios

### Scenario 1: Fresh Development Setup

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE vaitikan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
cd backend
python manage.py migrate

# Seed database
python scripts/seed_database.py

# Start server
python manage.py runserver
```

### Scenario 2: Reset Database with Fresh Data

```bash
# Drop and recreate database
mysql -u root -p -e "DROP DATABASE IF EXISTS vaitikan_db; CREATE DATABASE vaitikan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
cd backend
python manage.py migrate

# Seed database
python scripts/seed_database.py
```

### Scenario 3: Load Only Specific Fixtures

```bash
cd backend

# Load only location and user data
python manage.py loaddata database/fixtures/01_locations.json
python manage.py loaddata database/fixtures/02_users.json
python scripts/set_user_passwords.py
```

### Scenario 4: Update Passwords Only

```bash
cd backend
python scripts/set_user_passwords.py
```

### Scenario 5: Skip Passwords (Load Fixtures Only)

```bash
cd backend
python scripts/seed_database.py --skip-passwords
```

### Scenario 6: Skip Fixtures (Set Passwords Only)

```bash
cd backend
python scripts/seed_database.py --skip-fixtures
```

## Testing the Loaded Data

### Test 1: Login as Admin

```bash
# Start server
python manage.py runserver

# Visit: http://localhost:8000/users/login/
# Email: admin@vaitikan.com
# Password: admin123
```

### Test 2: Browse Products as Customer

```bash
# Login as customer
# Email: rajesh.kumar@example.com
# Password: customer123

# Visit: http://localhost:8000/products/
# You should see 3 products with multiple variants
```

### Test 3: View Orders

```bash
# Login as customer (priya.sharma@example.com)
# Visit: http://localhost:8000/orders/
# You should see 1 delivered order
```

### Test 4: Check Manufacturing Data

```bash
# Login as operator
# Email: operator@vaitikan.com
# Password: operator123

# Visit manufacturing pages to see:
# - 10 raw materials
# - 3 suppliers
# - Manufacturing specifications
```

### Test 5: Verify Data in Django Shell

```bash
python manage.py shell
```

```python
# Check users
from apps.users.models import User
print(f"Total users: {User.objects.count()}")
print(f"Admins: {User.objects.filter(user_type='admin').count()}")
print(f"Customers: {User.objects.filter(user_type='customer').count()}")

# Check products
from apps.products.models import Product, ProductVariant
print(f"Total products: {Product.objects.count()}")
print(f"Total variants: {ProductVariant.objects.count()}")

# Check orders
from apps.orders.models import Order
print(f"Total orders: {Order.objects.count()}")
print(f"Confirmed orders: {Order.objects.filter(status='confirmed').count()}")
print(f"Delivered orders: {Order.objects.filter(status='delivered').count()}")

# Check stock
from apps.products.models import Stock
total_stock = sum(s.quantity_in_stock for s in Stock.objects.all())
print(f"Total stock across all variants: {total_stock} units")

# Check payments
from apps.finance.models import Payment
successful_payments = Payment.objects.filter(payment_status='success')
total_revenue = sum(p.amount for p in successful_payments)
print(f"Total revenue from successful payments: ₹{total_revenue}")
```

## Troubleshooting

### Error: Database connection failed

**Solution:**

```bash
# Check if MySQL is running
mysql -u root -p -e "SELECT 1"

# Verify database exists
mysql -u root -p -e "SHOW DATABASES LIKE 'vaitikan_db'"

# Check settings.py database configuration
```

### Error: Table doesn't exist

**Solution:**

```bash
# Run migrations first
python manage.py migrate

# Then load fixtures
python scripts/seed_database.py
```

### Error: Duplicate key error

**Solution:**

```bash
# Clear existing data
python manage.py flush --no-input

# Reload fixtures
python scripts/seed_database.py
```

### Error: Foreign key constraint fails

**Solution:**

```bash
# Fixtures must be loaded in order
# Use the provided scripts which handle ordering automatically
python scripts/seed_database.py
```

### Error: User already exists

**Solution:**

```bash
# If reloading, flush first
python manage.py flush --no-input
python scripts/seed_database.py

# Or just update passwords
python scripts/set_user_passwords.py
```

## Customizing Fixtures

### Adding More Products

1. Edit `backend/database/fixtures/04_products.json`
2. Add new product entries with unique IDs
3. Reload the fixture:
   ```bash
   python manage.py loaddata database/fixtures/04_products.json
   ```

### Adding More Users

1. Edit `backend/database/fixtures/02_users.json`
2. Add new user entries
3. Reload and set passwords:
   ```bash
   python manage.py loaddata database/fixtures/02_users.json
   python scripts/set_user_passwords.py
   ```

### Modifying Stock Levels

1. Edit `backend/database/fixtures/05_variant_sizes_stock.json`
2. Update `quantity_in_stock` values
3. Reload:
   ```bash
   python manage.py loaddata database/fixtures/05_variant_sizes_stock.json
   ```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Test with Fixtures

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.4
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: vaitikan_db
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run migrations
        run: |
          cd backend
          python manage.py migrate

      - name: Load fixtures
        run: |
          cd backend
          python scripts/seed_database.py

      - name: Run tests
        run: |
          cd backend
          python manage.py test
```

## Best Practices

1. **Always load fixtures in order** - Use the provided scripts
2. **Set passwords after loading** - Fixtures contain placeholder hashes
3. **Use fresh database for testing** - Avoid conflicts with existing data
4. **Version control fixtures** - Track changes to sample data
5. **Document custom fixtures** - Update README when adding new data
6. **Test fixture loading** - Verify JSON syntax before committing
7. **Keep fixtures realistic** - Use data that represents actual use cases

## Quick Reference

| Command                                | Purpose                               |
| -------------------------------------- | ------------------------------------- |
| `python scripts/seed_database.py`      | Complete setup (fixtures + passwords) |
| `python scripts/load_fixtures.py`      | Load fixtures only                    |
| `python scripts/set_user_passwords.py` | Set passwords only                    |
| `python manage.py loaddata <file>`     | Load specific fixture                 |
| `python manage.py flush`               | Clear all data                        |
| `python manage.py migrate`             | Run database migrations               |

## Next Steps

After loading fixtures:

1. ✅ Start development server: `python manage.py runserver`
2. ✅ Login with sample credentials
3. ✅ Test customer workflows (browse, cart, order)
4. ✅ Test admin workflows (manage products, orders)
5. ✅ Test operator workflows (manufacturing, inventory)
6. ✅ Run property-based tests with real data
7. ✅ Develop new features with realistic data context
