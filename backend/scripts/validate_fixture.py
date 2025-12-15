#!/usr/bin/env python
"""
Script to validate a specific fixture file.
"""

import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python validate_fixture.py <fixture_file>")
    sys.exit(1)

fixture_file = sys.argv[1]
backend_dir = Path(__file__).resolve().parent.parent
fixture_path = backend_dir / fixture_file

print(f"Validating {fixture_path.name}...")
print("=" * 70)

with open(fixture_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total items: {len(data)}\n")

# Group by model
models = {}
for item in data:
    model = item.get('model', 'unknown')
    if model not in models:
        models[model] = []
    models[model].append(item)

print("Models in fixture:")
for model, items in sorted(models.items()):
    print(f"  {model}: {len(items)} items")
    # Show first item fields
    if items:
        fields = items[0].get('fields', {})
        print(f"    Fields: {', '.join(fields.keys())}")

print("\n" + "=" * 70)
print("Validation complete!")
