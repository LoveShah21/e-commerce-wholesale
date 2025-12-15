#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command

print("Testing order loading...")
try:
    call_command('loaddata', 'database/fixtures/06_orders_payments.json', verbosity=2)
    print("✓ Success!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
