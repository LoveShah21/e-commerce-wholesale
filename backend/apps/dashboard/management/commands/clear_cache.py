"""
Management command to clear application caches.

Usage:
    python manage.py clear_cache [--type TYPE]

Options:
    --type: Specific cache type to clear (product, dashboard, tax, inventory, all)
            Default: all
"""

from django.core.management.base import BaseCommand
from services.cache_service import CacheService


class Command(BaseCommand):
    help = 'Clear application caches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='all',
            choices=['product', 'dashboard', 'tax', 'inventory', 'all'],
            help='Type of cache to clear (default: all)'
        )

    def handle(self, *args, **options):
        cache_type = options['type']
        
        self.stdout.write(self.style.WARNING(f'Clearing {cache_type} cache...'))
        
        if cache_type == 'product' or cache_type == 'all':
            CacheService.invalidate_product_cache()
            self.stdout.write(self.style.SUCCESS('✓ Product cache cleared'))
        
        if cache_type == 'dashboard' or cache_type == 'all':
            CacheService.invalidate_dashboard_cache()
            self.stdout.write(self.style.SUCCESS('✓ Dashboard cache cleared'))
        
        if cache_type == 'tax' or cache_type == 'all':
            CacheService.invalidate_tax_config_cache()
            self.stdout.write(self.style.SUCCESS('✓ Tax configuration cache cleared'))
        
        if cache_type == 'inventory' or cache_type == 'all':
            CacheService.invalidate_inventory_cache()
            self.stdout.write(self.style.SUCCESS('✓ Inventory cache cleared'))
        
        if cache_type == 'all':
            CacheService.clear_all_caches()
            self.stdout.write(self.style.SUCCESS('✓ All caches cleared'))
        
        self.stdout.write(self.style.SUCCESS(f'\nCache clearing complete!'))
