#!/usr/bin/env python
"""
Script to set passwords for sample users after loading fixtures.

Usage:
    python scripts/set_user_passwords.py
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

from apps.users.models import User

# User credentials: (email, password, role)
USERS = [
    ('admin@vaitikan.com', 'admin123', 'Admin'),
    ('operator@vaitikan.com', 'operator123', 'Operator'),
    ('rajesh.kumar@example.com', 'customer123', 'Customer'),
    ('priya.sharma@example.com', 'customer123', 'Customer'),
    ('amit.patel@example.com', 'customer123', 'Customer'),
]

def set_passwords():
    """Set passwords for all sample users."""
    print("=" * 70)
    print("Setting Passwords for Sample Users")
    print("=" * 70)
    print()
    
    for email, password, role in USERS:
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            print(f"✓ Password set for {role}: {email}")
        except User.DoesNotExist:
            print(f"✗ User not found: {email}")
        except Exception as e:
            print(f"✗ Error setting password for {email}: {e}")
    
    print()
    print("=" * 70)
    print("Password Setup Complete!")
    print("=" * 70)
    print("\nSample Login Credentials:")
    print("-" * 70)
    for email, password, role in USERS:
        print(f"{role:12} | {email:35} | {password}")
    print("-" * 70)
    print()

if __name__ == '__main__':
    set_passwords()
