import os
import sys
import django
from decimal import Decimal

# Setup Django Environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.users.models import User, Address, Country, State, City, PostalCode
from apps.products.models import Fabric, Color, Pattern, Sleeve, Pocket, Size, Product, ProductVariant, VariantSize, Stock, ProductImage

def create_superuser():
    print("Checking Superuser...")
    email = 'admin@vaitikan.com'
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            username=email,
            email=email,
            password='Password@123',
            full_name='System Admin',
            phone='9876543210'
        )
        print(f"Superuser created: {email} / Password@123")
    else:
        print("Superuser already exists.")

def seed_products():
    print("Seeding Product Data...")
    
    # Attributes
    cotton, _ = Fabric.objects.get_or_create(fabric_name="Egyptian Cotton", description="Premium quality")
    linen, _ = Fabric.objects.get_or_create(fabric_name="Linen", description="Breathable fabric")
    
    blue, _ = Color.objects.get_or_create(color_name="Royal Blue", hex_code="#4169E1")
    white, _ = Color.objects.get_or_create(color_name="Classic White", hex_code="#FFFFFF")
    
    solid, _ = Pattern.objects.get_or_create(pattern_name="Solid")
    checked, _ = Pattern.objects.get_or_create(pattern_name="Checked")
    
    full_sleeve, _ = Sleeve.objects.get_or_create(sleeve_type="Full Sleeve")
    no_pocket, _ = Pocket.objects.get_or_create(pocket_type="No Pocket")
    
    # Sizes
    sizes = []
    for code in ['S', 'M', 'L', 'XL']:
        s, _ = Size.objects.get_or_create(size_code=code, defaults={'size_markup_percentage': 0})
        sizes.append(s)

    # Product 1
    p1, created = Product.objects.get_or_create(
        product_name="Signature Royal Blue Shirt",
        defaults={'description': "A classic royal blue shirt for formal occasions."}
    )
    
    if created:
        # Variant
        v1 = ProductVariant.objects.create(
            product=p1, fabric=cotton, color=blue, pattern=solid, 
            sleeve=full_sleeve, pocket=no_pocket, base_price=Decimal("1200.00")
        )
        # Variant Sizes & Stock
        for size in sizes:
            vs = VariantSize.objects.create(variant=v1, size=size)
            Stock.objects.create(variant_size=vs, quantity_in_stock=50)
            
        ProductImage.objects.create(product=p1, image_url="/static/images/blue_shirt.jpg", is_primary=True)
        print(f"Created Product: {p1.product_name}")
    else:
        print(f"Product already exists: {p1.product_name}")

if __name__ == '__main__':
    try:
        create_superuser()
        seed_products()
        print("Data Seeding Complete!")
    except Exception as e:
        print(f"Error seeding data: {e}")
