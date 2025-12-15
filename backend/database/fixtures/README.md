# Database Fixtures

This directory contains Django fixtures for seeding the database with sample data for development and testing.

## Fixtures Overview

The fixtures are organized in the following order (must be loaded in this sequence due to foreign key dependencies):

1. **01_locations.json** - Countries, States, Cities, and Postal Codes

   - 1 Country (India)
   - 4 States (Maharashtra, Gujarat, Karnataka, Delhi)
   - 6 Cities (Mumbai, Pune, Ahmedabad, Surat, Bangalore, New Delhi)
   - 7 Postal Codes

2. **02_users.json** - Users and Addresses

   - 1 Admin user (admin@vaitikan.com)
   - 1 Operator user (operator@vaitikan.com)
   - 3 Customer users (rajesh.kumar@example.com, priya.sharma@example.com, amit.patel@example.com)
   - 3 Addresses for customers

3. **03_product_attributes.json** - Product Attributes

   - 5 Fabrics (Cotton, Linen, Silk, Polyester, Cotton Blend)
   - 6 Colors (White, Blue, Black, Pink, Grey, Navy Blue)
   - 5 Patterns (Solid, Striped, Checked, Printed, Dotted)
   - 4 Sleeve Types (Full Sleeve, Half Sleeve, Sleeveless, Three Quarter)
   - 3 Pocket Types (No Pocket, Single Pocket, Double Pocket)
   - 5 Sizes (S, M, L, XL, XXL)

4. **04_products.json** - Products, Variants, and Images

   - 3 Products (Classic Formal Shirt, Casual Cotton Shirt, Designer Party Shirt)
   - 8 Product Variants with different combinations
   - 4 Product Images

5. **05_variant_sizes_stock.json** - Variant Sizes and Stock Records

   - 19 Variant Size combinations
   - 19 Stock records with quantities

6. **06_orders_payments.json** - Orders, Payments, Invoices, and Tax Configuration

   - 1 Tax Configuration (GST 18%)
   - 2 Carts (1 checked out, 1 active)
   - 2 Cart Items
   - 3 Orders (confirmed, processing, delivered)
   - 5 Order Items
   - 4 Payments (3 advance, 1 final)
   - 2 Invoices

7. **07_manufacturing.json** - Manufacturing Data

   - 4 Material Types (Fabric, Thread, Button, Packaging)
   - 3 Suppliers
   - 10 Raw Materials
   - 7 Material-Supplier associations
   - 13 Manufacturing Specifications

8. **08_support.json** - Support Data
   - 2 Inquiries
   - 1 Quotation Request
   - 1 Quotation Price
   - 2 Complaints (1 resolved, 1 in progress)
   - 2 Feedback entries

## Loading Fixtures

### Load All Fixtures

To load all fixtures in the correct order, use the provided script:

```bash
cd backend
python manage.py loaddata database/fixtures/01_locations.json
python manage.py loaddata database/fixtures/02_users.json
python manage.py loaddata database/fixtures/03_product_attributes.json
python manage.py loaddata database/fixtures/04_products.json
python manage.py loaddata database/fixtures/05_variant_sizes_stock.json
python manage.py loaddata database/fixtures/06_orders_payments.json
python manage.py loaddata database/fixtures/07_manufacturing.json
python manage.py loaddata database/fixtures/08_support.json
```

Or use the load script:

```bash
cd backend
python scripts/load_fixtures.py
```

### Load Individual Fixtures

You can also load individual fixtures:

```bash
python manage.py loaddata database/fixtures/01_locations.json
```

## Sample User Credentials

**Note:** The passwords in the fixtures are hashed placeholders. You'll need to set actual passwords after loading.

To set passwords for sample users:

```bash
python manage.py shell
```

Then in the shell:

```python
from apps.users.models import User

# Set password for admin
admin = User.objects.get(email='admin@vaitikan.com')
admin.set_password('admin123')
admin.save()

# Set password for operator
operator = User.objects.get(email='operator@vaitikan.com')
operator.set_password('operator123')
operator.save()

# Set password for customers
customer1 = User.objects.get(email='rajesh.kumar@example.com')
customer1.set_password('customer123')
customer1.save()

customer2 = User.objects.get(email='priya.sharma@example.com')
customer2.set_password('customer123')
customer2.save()

customer3 = User.objects.get(email='amit.patel@example.com')
customer3.set_password('customer123')
customer3.save()
```

### Sample Login Credentials (after setting passwords)

- **Admin:** admin@vaitikan.com / admin123
- **Operator:** operator@vaitikan.com / operator123
- **Customer 1:** rajesh.kumar@example.com / customer123
- **Customer 2:** priya.sharma@example.com / customer123
- **Customer 3:** amit.patel@example.com / customer123

## Resetting the Database

To reset the database and reload fixtures:

```bash
# Drop and recreate database (MySQL)
mysql -u root -p -e "DROP DATABASE IF EXISTS vaitikan_db; CREATE DATABASE vaitikan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
python manage.py migrate

# Load fixtures
python scripts/load_fixtures.py

# Set user passwords (see above)
```

## Notes

- Fixtures must be loaded in the specified order due to foreign key dependencies
- The fixture data is for development and testing purposes only
- Product images referenced in fixtures may not exist; update image URLs as needed
- Invoice URLs point to non-existent files; generate actual invoices through the application
- Payment data uses test Razorpay IDs; use actual Razorpay test mode for real testing
- Stock quantities are set to reasonable values for testing order placement
- Manufacturing specifications are provided for a subset of variant sizes

## Customization

To add more sample data:

1. Create new fixture files following Django's fixture format
2. Ensure proper foreign key references
3. Add to the loading sequence in the correct order
4. Update this README with the new fixture information
