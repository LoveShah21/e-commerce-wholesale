#!/usr/bin/env python
"""
Fresh database seeding script with Cloudinary-hosted product images.

This script creates all necessary data from scratch including:
- Locations (Countries, States, Cities, Postal Codes)
- Admin and sample users
- Product attributes (Fabrics, Colors, Patterns, Sleeves, Pockets, Sizes)
- Products with Cloudinary image URLs
- Variants and Stock
- Tax configuration
- Manufacturing data

Usage:
    python scripts/fresh_seed.py
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal

# Add the backend directory to the Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.users.models import User, Country, State, City, PostalCode, Address
from apps.products.models import (
    Fabric, Color, Pattern, Sleeve, Pocket, Size,
    Product, ProductImage, ProductVariant, VariantSize, Stock
)
from apps.finance.models import TaxConfiguration
from apps.manufacturing.models import RawMaterial, Supplier, MaterialCategory

# ============================================================================
# PUBLIC SHIRT IMAGE URLS (Free to use Unsplash/Pexels images)
# ============================================================================
SHIRT_IMAGES = {
    'formal_white': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800',
    'formal_blue': 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800',
    'casual_pattern': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800',
    'casual_solid': 'https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=800',
    'party_black': 'https://images.unsplash.com/photo-1620012253295-c15cc3e65df4?w=800',
    'linen_casual': 'https://images.unsplash.com/photo-1603252109303-2751441dd157?w=800',
    'denim_casual': 'https://images.unsplash.com/photo-1588359348347-9bc6cbbb689e?w=800',
    'striped_formal': 'https://images.unsplash.com/photo-1607345366928-199ea26cfe3e?w=800',
}


def create_locations():
    """Create location data: Countries, States, Cities, Postal Codes."""
    print("\n📍 Creating Locations...")
    
    # Country
    india, _ = Country.objects.get_or_create(
        country_name='India',
        defaults={'country_code': 'IN'}
    )
    
    # States
    gujarat, _ = State.objects.get_or_create(
        state_name='Gujarat',
        country=india,
        defaults={'state_code': 'GJ'}
    )
    
    maharashtra, _ = State.objects.get_or_create(
        state_name='Maharashtra',
        country=india,
        defaults={'state_code': 'MH'}
    )
    
    # Cities
    surat, _ = City.objects.get_or_create(
        city_name='Surat',
        state=gujarat
    )
    
    ahmedabad, _ = City.objects.get_or_create(
        city_name='Ahmedabad',
        state=gujarat
    )
    
    mumbai, _ = City.objects.get_or_create(
        city_name='Mumbai',
        state=maharashtra
    )
    
    # Postal Codes
    PostalCode.objects.get_or_create(postal_code='395001', city=surat)
    PostalCode.objects.get_or_create(postal_code='395007', city=surat)
    PostalCode.objects.get_or_create(postal_code='380001', city=ahmedabad)
    PostalCode.objects.get_or_create(postal_code='400001', city=mumbai)
    
    print(f"   ✓ Created locations: {Country.objects.count()} countries, {State.objects.count()} states, {City.objects.count()} cities")


def create_users():
    """Create admin and sample customer users."""
    print("\n👤 Creating Users...")
    
    # Admin User
    admin = User.objects.filter(email='admin@vaitikan.com').first()
    if not admin:
        admin = User.objects.create_superuser(
            email='admin@vaitikan.com',
            password='admin123',
            full_name='Vaitikan Admin',
            phone_number='+919876543210',
            user_role='admin'
        )
        print("   ✓ Created admin: admin@vaitikan.com / admin123")
    else:
        admin.set_password('admin123')
        admin.save()
        print("   ✓ Updated admin password")
    
    # Operator User
    operator = User.objects.filter(email='operator@vaitikan.com').first()
    if not operator:
        operator = User.objects.create_user(
            email='operator@vaitikan.com',
            password='operator123',
            full_name='Vaitikan Operator',
            phone_number='+919876543211',
            user_role='operator'
        )
        print("   ✓ Created operator: operator@vaitikan.com / operator123")
    
    # Sample Customers
    customers = [
        ('customer1@example.com', 'Customer One', '+919876543212'),
        ('customer2@example.com', 'Customer Two', '+919876543213'),
    ]
    
    for email, name, phone in customers:
        customer = User.objects.filter(email=email).first()
        if not customer:
            customer = User.objects.create_user(
                email=email,
                password='customer123',
                full_name=name,
                phone_number=phone,
                user_role='customer'
            )
            print(f"   ✓ Created customer: {email} / customer123")
    
    # Create address for customers
    postal_code = PostalCode.objects.first()
    if postal_code:
        for customer in User.objects.filter(user_role='customer'):
            Address.objects.get_or_create(
                user=customer,
                postal_code=postal_code,
                defaults={
                    'address_line1': f'{customer.full_name} House',
                    'address_line2': 'Main Street',
                    'address_type': 'home',
                    'is_default': True
                }
            )


def create_product_attributes():
    """Create product attributes: Fabrics, Colors, Patterns, etc."""
    print("\n🎨 Creating Product Attributes...")
    
    # Fabrics
    fabrics = ['Cotton', 'Linen', 'Silk', 'Polyester', 'Denim']
    for name in fabrics:
        Fabric.objects.get_or_create(fabric_name=name)
    
    # Colors
    colors = [
        ('White', '#FFFFFF'),
        ('Black', '#000000'),
        ('Navy Blue', '#000080'),
        ('Light Blue', '#ADD8E6'),
        ('Grey', '#808080'),
        ('Maroon', '#800000'),
        ('Pink', '#FFC0CB'),
        ('Green', '#008000'),
    ]
    for name, hex_code in colors:
        Color.objects.get_or_create(color_name=name, defaults={'hex_code': hex_code})
    
    # Patterns
    patterns = ['Solid', 'Striped', 'Checkered', 'Printed', 'Textured']
    for name in patterns:
        Pattern.objects.get_or_create(pattern_name=name)
    
    # Sleeves
    sleeves = ['Full Sleeve', 'Half Sleeve', 'Sleeveless', 'Roll-up Sleeve']
    for name in sleeves:
        Sleeve.objects.get_or_create(sleeve_type=name)
    
    # Pockets
    pockets = ['No Pocket', 'Single Pocket', 'Double Pocket', 'Patch Pocket']
    for name in pockets:
        Pocket.objects.get_or_create(pocket_type=name)
    
    # Sizes with markup
    sizes = [
        ('XS', 'Extra Small', Decimal('0.00')),
        ('S', 'Small', Decimal('0.00')),
        ('M', 'Medium', Decimal('0.00')),
        ('L', 'Large', Decimal('5.00')),
        ('XL', 'Extra Large', Decimal('10.00')),
        ('XXL', 'Double Extra Large', Decimal('15.00')),
    ]
    for code, name, markup in sizes:
        Size.objects.get_or_create(
            size_code=code,
            defaults={'size_name': name, 'size_markup_percentage': markup}
        )
    
    print(f"   ✓ Created {Fabric.objects.count()} fabrics, {Color.objects.count()} colors, {Pattern.objects.count()} patterns")


def create_products():
    """Create products with images and variants."""
    print("\n👔 Creating Products...")
    
    # Get attributes
    cotton = Fabric.objects.get(fabric_name='Cotton')
    linen = Fabric.objects.get(fabric_name='Linen')
    silk = Fabric.objects.get(fabric_name='Silk')
    
    white = Color.objects.get(color_name='White')
    blue = Color.objects.get(color_name='Navy Blue')
    black = Color.objects.get(color_name='Black')
    light_blue = Color.objects.get(color_name='Light Blue')
    
    solid = Pattern.objects.get(pattern_name='Solid')
    striped = Pattern.objects.get(pattern_name='Striped')
    
    full_sleeve = Sleeve.objects.get(sleeve_type='Full Sleeve')
    half_sleeve = Sleeve.objects.get(sleeve_type='Half Sleeve')
    
    single_pocket = Pocket.objects.get(pocket_type='Single Pocket')
    no_pocket = Pocket.objects.get(pocket_type='No Pocket')
    
    sizes = list(Size.objects.all())
    
    # Product 1: Classic White Formal Shirt
    product1, _ = Product.objects.get_or_create(
        product_name='Classic White Formal Shirt',
        defaults={'description': 'Premium cotton formal shirt perfect for office and business meetings.'}
    )
    ProductImage.objects.get_or_create(
        product=product1,
        image_url=SHIRT_IMAGES['formal_white'],
        defaults={'alt_text': 'Classic White Formal Shirt', 'is_primary': True, 'display_order': 1}
    )
    
    # Variant for Product 1
    variant1, _ = ProductVariant.objects.get_or_create(
        product=product1,
        fabric=cotton,
        color=white,
        pattern=solid,
        sleeve=full_sleeve,
        pocket=single_pocket,
        defaults={'base_price': Decimal('1299.00'), 'sku': 'CWFS-001'}
    )
    
    # Product 2: Navy Blue Formal Shirt
    product2, _ = Product.objects.get_or_create(
        product_name='Navy Blue Formal Shirt',
        defaults={'description': 'Elegant navy blue shirt for a professional look.'}
    )
    ProductImage.objects.get_or_create(
        product=product2,
        image_url=SHIRT_IMAGES['formal_blue'],
        defaults={'alt_text': 'Navy Blue Formal Shirt', 'is_primary': True, 'display_order': 1}
    )
    
    variant2, _ = ProductVariant.objects.get_or_create(
        product=product2,
        fabric=cotton,
        color=blue,
        pattern=solid,
        sleeve=full_sleeve,
        pocket=single_pocket,
        defaults={'base_price': Decimal('1399.00'), 'sku': 'NBFS-001'}
    )
    
    # Product 3: Casual Linen Shirt
    product3, _ = Product.objects.get_or_create(
        product_name='Casual Linen Shirt',
        defaults={'description': 'Comfortable linen shirt perfect for summer and casual outings.'}
    )
    ProductImage.objects.get_or_create(
        product=product3,
        image_url=SHIRT_IMAGES['linen_casual'],
        defaults={'alt_text': 'Casual Linen Shirt', 'is_primary': True, 'display_order': 1}
    )
    
    variant3, _ = ProductVariant.objects.get_or_create(
        product=product3,
        fabric=linen,
        color=light_blue,
        pattern=solid,
        sleeve=half_sleeve,
        pocket=no_pocket,
        defaults={'base_price': Decimal('999.00'), 'sku': 'CLS-001'}
    )
    
    # Product 4: Black Party Shirt
    product4, _ = Product.objects.get_or_create(
        product_name='Black Silk Party Shirt',
        defaults={'description': 'Luxurious silk shirt for parties and special occasions.'}
    )
    ProductImage.objects.get_or_create(
        product=product4,
        image_url=SHIRT_IMAGES['party_black'],
        defaults={'alt_text': 'Black Silk Party Shirt', 'is_primary': True, 'display_order': 1}
    )
    
    variant4, _ = ProductVariant.objects.get_or_create(
        product=product4,
        fabric=silk,
        color=black,
        pattern=solid,
        sleeve=full_sleeve,
        pocket=no_pocket,
        defaults={'base_price': Decimal('2499.00'), 'sku': 'BSPS-001'}
    )
    
    # Product 5: Striped Formal Shirt
    product5, _ = Product.objects.get_or_create(
        product_name='Blue Striped Formal Shirt',
        defaults={'description': 'Classic striped pattern for a distinguished professional look.'}
    )
    ProductImage.objects.get_or_create(
        product=product5,
        image_url=SHIRT_IMAGES['striped_formal'],
        defaults={'alt_text': 'Blue Striped Formal Shirt', 'is_primary': True, 'display_order': 1}
    )
    
    variant5, _ = ProductVariant.objects.get_or_create(
        product=product5,
        fabric=cotton,
        color=light_blue,
        pattern=striped,
        sleeve=full_sleeve,
        pocket=single_pocket,
        defaults={'base_price': Decimal('1499.00'), 'sku': 'BSFS-001'}
    )
    
    # Create VariantSizes and Stock for all variants
    all_variants = [variant1, variant2, variant3, variant4, variant5]
    for variant in all_variants:
        for size in sizes:
            variant_size, created = VariantSize.objects.get_or_create(
                variant=variant,
                size=size,
                defaults={'stock_quantity': 50}
            )
            if created:
                # Create Stock record
                Stock.objects.get_or_create(
                    variant_size=variant_size,
                    defaults={
                        'quantity_in_stock': 50,
                        'quantity_reserved': 0
                    }
                )
    
    print(f"   ✓ Created {Product.objects.count()} products with {ProductVariant.objects.count()} variants")
    print(f"   ✓ Created {VariantSize.objects.count()} variant sizes with stock")


def create_tax_config():
    """Create tax configuration."""
    print("\n💰 Creating Tax Configuration...")
    
    from django.utils import timezone
    
    TaxConfiguration.objects.get_or_create(
        tax_name='GST',
        defaults={
            'tax_percentage': Decimal('18.00'),
            'is_active': True,
            'effective_from': timezone.now().date()
        }
    )
    
    print("   ✓ Created GST tax config at 18%")


def create_manufacturing_data():
    """Create manufacturing-related data."""
    print("\n🏭 Creating Manufacturing Data...")
    
    # Material Categories
    fabric_cat, _ = MaterialCategory.objects.get_or_create(category_name='Fabrics')
    buttons_cat, _ = MaterialCategory.objects.get_or_create(category_name='Buttons')
    thread_cat, _ = MaterialCategory.objects.get_or_create(category_name='Threads')
    
    # Suppliers
    supplier1, _ = Supplier.objects.get_or_create(
        supplier_name='Premium Fabrics Ltd',
        defaults={
            'contact_person': 'Ramesh Patel',
            'email': 'sales@premiumfabrics.com',
            'phone': '+919876500001',
            'address': 'Textile Market, Surat'
        }
    )
    
    supplier2, _ = Supplier.objects.get_or_create(
        supplier_name='Button World',
        defaults={
            'contact_person': 'Priya Shah',
            'email': 'info@buttonworld.com',
            'phone': '+919876500002',
            'address': 'Industrial Area, Ahmedabad'
        }
    )
    
    # Raw Materials
    RawMaterial.objects.get_or_create(
        material_name='Cotton Fabric (White)',
        defaults={
            'category': fabric_cat,
            'unit': 'meters',
            'quantity_in_stock': Decimal('1000.00'),
            'reorder_level': Decimal('100.00'),
            'unit_cost': Decimal('150.00'),
            'supplier': supplier1
        }
    )
    
    RawMaterial.objects.get_or_create(
        material_name='Shell Buttons',
        defaults={
            'category': buttons_cat,
            'unit': 'pieces',
            'quantity_in_stock': Decimal('5000.00'),
            'reorder_level': Decimal('500.00'),
            'unit_cost': Decimal('2.00'),
            'supplier': supplier2
        }
    )
    
    RawMaterial.objects.get_or_create(
        material_name='White Thread',
        defaults={
            'category': thread_cat,
            'unit': 'spools',
            'quantity_in_stock': Decimal('200.00'),
            'reorder_level': Decimal('20.00'),
            'unit_cost': Decimal('25.00'),
            'supplier': supplier1
        }
    )
    
    print(f"   ✓ Created {Supplier.objects.count()} suppliers, {RawMaterial.objects.count()} raw materials")


def print_summary():
    """Print summary of created data."""
    print("\n" + "=" * 70)
    print("✅ DATABASE SEEDING COMPLETE!")
    print("=" * 70)
    
    print("\n📊 Data Summary:")
    print("-" * 40)
    print(f"   Users:            {User.objects.count()}")
    print(f"   Products:         {Product.objects.count()}")
    print(f"   Product Variants: {ProductVariant.objects.count()}")
    print(f"   Variant Sizes:    {VariantSize.objects.count()}")
    print(f"   Stock Records:    {Stock.objects.count()}")
    
    print("\n🔐 Login Credentials:")
    print("-" * 40)
    print("   Admin:    admin@vaitikan.com / admin123")
    print("   Operator: operator@vaitikan.com / operator123")
    print("   Customer: customer1@example.com / customer123")
    print("   Customer: customer2@example.com / customer123")
    
    print("\n🚀 Next Steps:")
    print("-" * 40)
    print("   1. Start server: python manage.py runserver")
    print("   2. Visit: http://127.0.0.1:8000/")
    print("   3. Login with any credentials above")
    print()


@transaction.atomic
def main():
    """Main function to seed the database."""
    print("\n" + "=" * 70)
    print("🌱 VAITIKAN FRESH DATABASE SEEDING")
    print("=" * 70)
    
    create_locations()
    create_users()
    create_product_attributes()
    create_products()
    create_tax_config()
    create_manufacturing_data()
    print_summary()


if __name__ == '__main__':
    main()
