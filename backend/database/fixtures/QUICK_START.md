# Quick Start Guide - Database Fixtures

## Quick Setup (Recommended)

The easiest way to seed your database with sample data:

```bash
cd backend
python scripts/seed_database.py
```

This single command will:

1. Load all fixtures in the correct order
2. Set passwords for all sample users
3. Display a summary of loaded data
4. Show login credentials

## Manual Setup

If you prefer to load fixtures manually:

### Step 1: Load Fixtures

```bash
cd backend
python scripts/load_fixtures.py
```

### Step 2: Set User Passwords

```bash
python scripts/set_user_passwords.py
```

## Individual Fixture Loading

To load specific fixtures only:

```bash
cd backend

# Load locations
python manage.py loaddata database/fixtures/01_locations.json

# Load users
python manage.py loaddata database/fixtures/02_users.json

# Load product attributes
python manage.py loaddata database/fixtures/03_product_attributes.json

# And so on...
```

## Login Credentials

After seeding, you can login with these credentials:

| Role     | Email                    | Password    |
| -------- | ------------------------ | ----------- |
| Admin    | admin@vaitikan.com       | admin123    |
| Operator | operator@vaitikan.com    | operator123 |
| Customer | rajesh.kumar@example.com | customer123 |
| Customer | priya.sharma@example.com | customer123 |
| Customer | amit.patel@example.com   | customer123 |

## Resetting Database

To completely reset and reseed the database:

```bash
# Drop and recreate database (MySQL)
mysql -u root -p -e "DROP DATABASE IF EXISTS vaitikan_db; CREATE DATABASE vaitikan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
cd backend
python manage.py migrate

# Seed database
python scripts/seed_database.py
```

## What Gets Loaded?

- **Locations**: 1 country, 4 states, 6 cities, 7 postal codes
- **Users**: 1 admin, 1 operator, 3 customers with addresses
- **Products**: 3 products, 8 variants, 19 variant sizes with stock
- **Orders**: 3 orders with items, 4 payments, 2 invoices
- **Manufacturing**: 10 raw materials, 3 suppliers, 13 specifications
- **Support**: 2 inquiries, 1 quotation, 2 complaints, 2 feedback entries

## Troubleshooting

### Database Connection Error

Make sure your database is running and configured in `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vaitikan_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Foreign Key Constraint Errors

Fixtures must be loaded in order. Use the provided scripts which handle the correct order automatically.

### User Already Exists Error

If you're reloading fixtures, you may need to clear existing data first:

```bash
python manage.py flush --no-input
python scripts/seed_database.py
```

## Next Steps

After seeding:

1. Start the development server:

   ```bash
   python manage.py runserver
   ```

2. Access the application at `http://localhost:8000`

3. Login with any of the sample credentials

4. Explore the pre-populated data:
   - Browse products as a customer
   - Manage orders as an admin
   - View manufacturing data as an operator

## Need Help?

See the full documentation in `README.md` for more details about the fixture structure and customization options.
