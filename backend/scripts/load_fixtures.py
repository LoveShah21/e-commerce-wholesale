#!/usr/bin/env python
"""
Script to load all database fixtures in the correct order.

Usage:
    python scripts/load_fixtures.py
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

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

def load_fixtures():
    """Load all fixtures in the correct order."""
    print("=" * 70)
    print("Loading Database Fixtures")
    print("=" * 70)
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful\n")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Please ensure the database is running and configured correctly.")
        sys.exit(1)
    
    # Load each fixture
    for i, fixture in enumerate(FIXTURES, 1):
        fixture_path = backend_dir / fixture
        
        if not fixture_path.exists():
            print(f"✗ Fixture file not found: {fixture}")
            continue
        
        print(f"[{i}/{len(FIXTURES)}] Loading {fixture}...")
        
        try:
            call_command('loaddata', fixture, verbosity=0)
            print(f"    ✓ Successfully loaded {fixture}\n")
        except Exception as e:
            print(f"    ✗ Error loading {fixture}: {e}\n")
            print("    Continuing with remaining fixtures...\n")
    
    print("=" * 70)
    print("Fixture Loading Complete!")
    print("=" * 70)
    print("\nIMPORTANT: Set passwords for sample users:")
    print("\nRun the following commands in Django shell (python manage.py shell):\n")
    print("from apps.users.models import User")
    print("User.objects.get(email='admin@vaitikan.com').set_password('admin123')")
    print("User.objects.get(email='operator@vaitikan.com').set_password('operator123')")
    print("User.objects.get(email='rajesh.kumar@example.com').set_password('customer123')")
    print("User.objects.get(email='priya.sharma@example.com').set_password('customer123')")
    print("User.objects.get(email='amit.patel@example.com').set_password('customer123')")
    print("\nOr run: python scripts/set_user_passwords.py")
    print()

if __name__ == '__main__':
    load_fixtures()
