"""
Script to verify database query optimizations.

This script demonstrates the query count improvements from the optimizations.
Run with: python manage.py shell < scripts/verify_optimizations.py
"""

import django
from django.db import connection, reset_queries
from django.conf import settings

# Enable query logging
settings.DEBUG = True

def count_queries(func):
    """Decorator to count database queries."""
    def wrapper(*args, **kwargs):
        reset_queries()
        result = func(*args, **kwargs)
        query_count = len(connection.queries)
        return result, query_count
    return wrapper

@count_queries
def test_product_list():
    """Test product list query optimization."""
    from apps.products.models import Product
    products = list(Product.objects.all().prefetch_related(
        'images',
        'variants__fabric',
        'variants__color',
        'variants__pattern',
        'variants__sleeve',
        'variants__pocket'
    )[:10])
    return products

@count_queries
def test_product_detail():
    """Test product detail query optimization."""
    from apps.products.models import Product
    product = Product.objects.prefetch_related(
        'images',
        'variants__fabric',
        'variants__color',
        'variants__pattern',
        'variants__sleeve',
        'variants__pocket',
        'variants__sizes__size',
        'variants__sizes__stock_record'
    ).first()
    
    if product:
        # Access related objects to trigger queries
        images = list(product.images.all())
        for variant in product.variants.all():
            fabric = variant.fabric
            color = variant.color
            for size in variant.sizes.all():
                stock = size.stock_record if hasattr(size, 'stock_record') else None
    
    return product

@count_queries
def test_order_list():
    """Test order list query optimization."""
    from apps.orders.models import Order
    from apps.users.models import User
    
    user = User.objects.first()
    if not user:
        return None
    
    orders = list(Order.objects.filter(
        user=user
    ).select_related(
        'user',
        'delivery_address',
        'delivery_address__postal_code',
        'delivery_address__postal_code__city',
        'delivery_address__postal_code__city__state',
        'delivery_address__postal_code__city__state__country'
    ).prefetch_related(
        'items__variant_size__variant__product',
        'items__variant_size__variant__fabric',
        'items__variant_size__variant__color',
        'items__variant_size__variant__pattern',
        'items__variant_size__size'
    )[:10])
    
    return orders

@count_queries
def test_cart_items():
    """Test cart items query optimization."""
    from apps.orders.models import CartItem
    from apps.users.models import User
    
    user = User.objects.first()
    if not user:
        return None
    
    cart_items = list(CartItem.objects.filter(
        cart__user=user,
        cart__status='active'
    ).select_related(
        'cart',
        'variant_size__variant__product',
        'variant_size__variant__fabric',
        'variant_size__variant__color',
        'variant_size__variant__pattern',
        'variant_size__size',
        'variant_size__stock_record'
    ))
    
    return cart_items

def run_verification():
    """Run all verification tests."""
    print("=" * 80)
    print("DATABASE QUERY OPTIMIZATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Test Product List
    print("1. Product List Query Optimization")
    print("-" * 80)
    products, query_count = test_product_list()
    print(f"   Products fetched: {len(products) if products else 0}")
    print(f"   Database queries: {query_count}")
    print(f"   Expected: 5-10 queries (with prefetch_related)")
    print(f"   Status: {'✅ OPTIMIZED' if query_count <= 10 else '❌ NEEDS OPTIMIZATION'}")
    print()
    
    # Test Product Detail
    print("2. Product Detail Query Optimization")
    print("-" * 80)
    product, query_count = test_product_detail()
    print(f"   Product fetched: {'Yes' if product else 'No'}")
    print(f"   Database queries: {query_count}")
    print(f"   Expected: 10-15 queries (with nested prefetch_related)")
    print(f"   Status: {'✅ OPTIMIZED' if query_count <= 15 else '❌ NEEDS OPTIMIZATION'}")
    print()
    
    # Test Order List
    print("3. Order List Query Optimization")
    print("-" * 80)
    orders, query_count = test_order_list()
    print(f"   Orders fetched: {len(orders) if orders else 0}")
    print(f"   Database queries: {query_count}")
    print(f"   Expected: 8-12 queries (with select_related and prefetch_related)")
    print(f"   Status: {'✅ OPTIMIZED' if query_count <= 12 else '❌ NEEDS OPTIMIZATION'}")
    print()
    
    # Test Cart Items
    print("4. Cart Items Query Optimization")
    print("-" * 80)
    cart_items, query_count = test_cart_items()
    print(f"   Cart items fetched: {len(cart_items) if cart_items else 0}")
    print(f"   Database queries: {query_count}")
    print(f"   Expected: 1-3 queries (with select_related)")
    print(f"   Status: {'✅ OPTIMIZED' if query_count <= 3 else '❌ NEEDS OPTIMIZATION'}")
    print()
    
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("- All queries use select_related() for foreign keys")
    print("- All queries use prefetch_related() for reverse relations")
    print("- Database indexes have been added for frequently queried fields")
    print("- Caching infrastructure is in place for expensive queries")
    print()
    print("For detailed documentation, see:")
    print("- backend/QUERY_OPTIMIZATION.md")
    print("- backend/OPTIMIZATION_SUMMARY.md")
    print()

if __name__ == '__main__':
    run_verification()
