#!/usr/bin/env python
"""
Comprehensive script to seed the database with fixtures and set user passwords.

Usage:
    python scripts/seed_database.py [--skip-fixtures] [--skip-passwords]
    
Options:
    --skip-fixtures    Skip loading fixtures (only set passwords)
    --skip-passwords   Skip setting passwords (only load fixtures)
"""

import os
import sys
import django
import argparse
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from apps.users.models import User

# Fixture files in the order they should be loaded
FIXTURES = [
    'database/fixtures/01_locations.json',
    'database/fixtures/02_users.json',
    'database/fixtures/03_product_attributes.json',
    'database/fixtures/04_products.json',
    'database/fixtures/05_variant_sizes_stock.json',
    'database/fixtures/06_orders_payments.json',
    'database/fixtures/07_manufacturing.json',
    'database/fixtures/08_support.json',
]

# User credentials: (email, password, role)
USERS = [
    ('admin@vaitikan.com', 'admin123', 'Admin'),
    ('operator@vaitikan.com', 'operator123', 'Operator'),
    ('rajesh.kumar@example.com', 'customer123', 'Customer'),
    ('priya.sharma@example.com', 'customer123', 'Customer'),
    ('amit.patel@example.com', 'customer123', 'Customer'),
]

def load_fixtures():
    """Load all fixtures in the correct order."""
    print("\n" + "=" * 70)
    print("STEP 1: Loading Database Fixtures")
    print("=" * 70)
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Please ensure the database is running and configured correctly.")
        return False
    
    # Load each fixture
    success_count = 0
    for i, fixture in enumerate(FIXTURES, 1):
        fixture_path = backend_dir / fixture
        
        if not fixture_path.exists():
            print(f"✗ Fixture file not found: {fixture}")
            continue
        
        print(f"[{i}/{len(FIXTURES)}] Loading {fixture}...")
        
        try:
            call_command('loaddata', fixture, verbosity=0)
            print(f"    ✓ Successfully loaded")
            success_count += 1
        except Exception as e:
            print(f"    ✗ Error: {e}")
            print("    Continuing with remaining fixtures...")
    
    print(f"\n✓ Loaded {success_count}/{len(FIXTURES)} fixtures successfully")
    return True

def set_passwords():
    """Set passwords for all sample users."""
    print("\n" + "=" * 70)
    print("STEP 2: Setting User Passwords")
    print("=" * 70)
    print()
    
    success_count = 0
    for email, password, role in USERS:
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            print(f"✓ Password set for {role:12} | {email}")
            success_count += 1
        except User.DoesNotExist:
            print(f"✗ User not found: {email}")
        except Exception as e:
            print(f"✗ Error setting password for {email}: {e}")
    
    print(f"\n✓ Set passwords for {success_count}/{len(USERS)} users")
    return True

def print_summary():
    """Print summary of loaded data."""
    print("\n" + "=" * 70)
    print("DATABASE SEEDING COMPLETE!")
    print("=" * 70)
    
    print("\n📊 Sample Data Summary:")
    print("-" * 70)
    
    try:
        from apps.users.models import User, Country, State, City
        from apps.products.models import Product, ProductVariant, Size
        from apps.orders.models import Order, Cart
        from apps.manufacturing.models import RawMaterial, Supplier
        from apps.support.models import Inquiry, Complaint, Feedback
        
        print(f"  Users:              {User.objects.count()}")
        print(f"  Countries:          {Country.objects.count()}")
        print(f"  States:             {State.objects.count()}")
        print(f"  Cities:             {City.objects.count()}")
        print(f"  Products:           {Product.objects.count()}")
        print(f"  Product Variants:   {ProductVariant.objects.count()}")
        print(f"  Sizes:              {Size.objects.count()}")
        print(f"  Orders:             {Order.objects.count()}")
        print(f"  Carts:              {Cart.objects.count()}")
        print(f"  Raw Materials:      {RawMaterial.objects.count()}")
        print(f"  Suppliers:          {Supplier.objects.count()}")
        print(f"  Inquiries:          {Inquiry.objects.count()}")
        print(f"  Complaints:         {Complaint.objects.count()}")
        print(f"  Feedback:           {Feedback.objects.count()}")
    except Exception as e:
        print(f"  (Could not fetch counts: {e})")
    
    print("-" * 70)
    
    print("\n🔐 Sample Login Credentials:")
    print("-" * 70)
    print(f"{'Role':<12} | {'Email':<35} | {'Password'}")
    print("-" * 70)
    for email, password, role in USERS:
        print(f"{role:<12} | {email:<35} | {password}")
    print("-" * 70)
    
    print("\n✅ You can now:")
    print("  1. Start the development server: python manage.py runserver")
    print("  2. Login with any of the sample credentials above")
    print("  3. Explore the application with pre-populated data")
    print()

def main():
    """Main function to orchestrate database seeding."""
    parser = argparse.ArgumentParser(
        description='Seed the database with fixtures and set user passwords'
    )
    parser.add_argument(
        '--skip-fixtures',
        action='store_true',
        help='Skip loading fixtures (only set passwords)'
    )
    parser.add_argument(
        '--skip-passwords',
        action='store_true',
        help='Skip setting passwords (only load fixtures)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("VAITIKAN DATABASE SEEDING SCRIPT")
    print("=" * 70)
    
    success = True
    
    if not args.skip_fixtures:
        if not load_fixtures():
            success = False
    else:
        print("\n⏭️  Skipping fixture loading")
    
    if not args.skip_passwords:
        if not set_passwords():
            success = False
    else:
        print("\n⏭️  Skipping password setup")
    
    if success:
        print_summary()
    else:
        print("\n⚠️  Database seeding completed with some errors.")
        print("Please review the output above for details.")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
