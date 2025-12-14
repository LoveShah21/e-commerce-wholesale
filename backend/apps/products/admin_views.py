from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.db import transaction
from apps.users.permissions import admin_required
from .models import (
    Product, ProductVariant, VariantSize, Stock, ProductImage,
    Fabric, Color, Pattern, Sleeve, Pocket, Size
)
from services.utils import generate_sku


class AdminProductListView(View):
    """Admin view for listing and managing products"""
    
    @admin_required
    def get(self, request):
        products = Product.objects.all().prefetch_related(
            'images', 'variants__variant_sizes__stock_record'
        ).annotate(
            variant_count=Count('variants')
        )
        
        # Apply search
        search_query = request.GET.get('search', '')
        if search_query:
            products = products.filter(
                Q(product_name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply filters
        fabric_id = request.GET.get('fabric')
        color_id = request.GET.get('color')
        pattern_id = request.GET.get('pattern')
        
        if fabric_id:
            products = products.filter(variants__fabric_id=fabric_id).distinct()
        if color_id:
            products = products.filter(variants__color_id=color_id).distinct()
        if pattern_id:
            products = products.filter(variants__pattern_id=pattern_id).distinct()
        
        products = products.order_by('-created_at')
        
        # Get filter options
        fabrics = Fabric.objects.all()
        colors = Color.objects.all()
        patterns = Pattern.objects.all()
        
        context = {
            'products': products,
            'fabrics': fabrics,
            'colors': colors,
            'patterns': patterns,
            'search_query': search_query,
            'selected_fabric': fabric_id,
            'selected_color': color_id,
            'selected_pattern': pattern_id,
        }
        
        return render(request, 'products/admin/list.html', context)


class AdminProductCreateView(View):
    """Admin view for creating a new product"""
    
    @admin_required
    def get(self, request):
        context = {
            'fabrics': Fabric.objects.all(),
            'colors': Color.objects.all(),
            'patterns': Pattern.objects.all(),
            'sleeves': Sleeve.objects.all(),
            'pockets': Pocket.objects.all(),
            'sizes': Size.objects.all(),
        }
        return render(request, 'products/admin/create.html', context)
    
    @admin_required
    def post(self, request):
        try:
            with transaction.atomic():
                # Create product
                product = Product.objects.create(
                    product_name=request.POST.get('product_name'),
                    description=request.POST.get('description', '')
                )
                
                messages.success(request, f'Product "{product.product_name}" created successfully!')
                return redirect('admin-product-edit', pk=product.id)
                
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            context = {
                'fabrics': Fabric.objects.all(),
                'colors': Color.objects.all(),
                'patterns': Pattern.objects.all(),
                'sleeves': Sleeve.objects.all(),
                'pockets': Pocket.objects.all(),
                'sizes': Size.objects.all(),
                'form_data': request.POST,
            }
            return render(request, 'products/admin/create.html', context)


class AdminProductEditView(View):
    """Admin view for editing a product and managing variants"""
    
    @admin_required
    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.prefetch_related(
                'images',
                'variants__fabric',
                'variants__color',
                'variants__pattern',
                'variants__sleeve',
                'variants__pocket',
                'variants__variant_sizes__size',
                'variants__variant_sizes__stock_record'
            ),
            pk=pk
        )
        
        context = {
            'product': product,
            'fabrics': Fabric.objects.all(),
            'colors': Color.objects.all(),
            'patterns': Pattern.objects.all(),
            'sleeves': Sleeve.objects.all(),
            'pockets': Pocket.objects.all(),
            'sizes': Size.objects.all(),
        }
        return render(request, 'products/admin/edit.html', context)
    
    @admin_required
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        
        try:
            product.product_name = request.POST.get('product_name')
            product.description = request.POST.get('description', '')
            product.save()
            
            messages.success(request, 'Product updated successfully!')
            return redirect('admin-product-edit', pk=product.id)
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            return redirect('admin-product-edit', pk=product.id)


class AdminProductDeleteView(View):
    """Admin view for deleting a product"""
    
    @admin_required
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product_name = product.product_name
        
        try:
            product.delete()
            messages.success(request, f'Product "{product_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
        
        return redirect('admin-product-list')


class AdminVariantCreateView(View):
    """Admin view for creating a variant"""
    
    @admin_required
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        
        try:
            with transaction.atomic():
                variant = ProductVariant.objects.create(
                    product=product,
                    fabric_id=request.POST.get('fabric'),
                    color_id=request.POST.get('color'),
                    pattern_id=request.POST.get('pattern'),
                    sleeve_id=request.POST.get('sleeve'),
                    pocket_id=request.POST.get('pocket'),
                    base_price=request.POST.get('base_price'),
                    sku=generate_sku('SHIRT')
                )
                
                messages.success(request, 'Variant created successfully!')
                
        except Exception as e:
            messages.error(request, f'Error creating variant: {str(e)}')
        
        return redirect('admin-product-edit', pk=product_id)


class AdminVariantUpdateView(View):
    """Admin view for updating a variant"""
    
    @admin_required
    def post(self, request, variant_id):
        variant = get_object_or_404(ProductVariant, pk=variant_id)
        
        try:
            variant.fabric_id = request.POST.get('fabric')
            variant.color_id = request.POST.get('color')
            variant.pattern_id = request.POST.get('pattern')
            variant.sleeve_id = request.POST.get('sleeve')
            variant.pocket_id = request.POST.get('pocket')
            variant.base_price = request.POST.get('base_price')
            variant.save()
            
            messages.success(request, 'Variant updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating variant: {str(e)}')
        
        return redirect('admin-product-edit', pk=variant.product.id)


class AdminVariantDeleteView(View):
    """Admin view for deleting a variant"""
    
    @admin_required
    def post(self, request, variant_id):
        variant = get_object_or_404(ProductVariant, pk=variant_id)
        product_id = variant.product.id
        
        try:
            variant.delete()
            messages.success(request, 'Variant deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting variant: {str(e)}')
        
        return redirect('admin-product-edit', pk=product_id)


class AdminVariantSizeCreateView(View):
    """Admin view for adding a size to a variant"""
    
    @admin_required
    def post(self, request, variant_id):
        variant = get_object_or_404(ProductVariant, pk=variant_id)
        
        try:
            with transaction.atomic():
                variant_size = VariantSize.objects.create(
                    variant=variant,
                    size_id=request.POST.get('size'),
                    stock_quantity=request.POST.get('stock_quantity', 0)
                )
                
                # Create stock record
                Stock.objects.create(
                    variant_size=variant_size,
                    quantity_in_stock=request.POST.get('stock_quantity', 0),
                    quantity_reserved=0
                )
                
                messages.success(request, 'Size added successfully!')
                
        except Exception as e:
            messages.error(request, f'Error adding size: {str(e)}')
        
        return redirect('admin-product-edit', pk=variant.product.id)


class AdminVariantSizeUpdateView(View):
    """Admin view for updating stock for a variant size"""
    
    @admin_required
    def post(self, request, variant_size_id):
        variant_size = get_object_or_404(VariantSize, pk=variant_size_id)
        
        try:
            with transaction.atomic():
                stock, created = Stock.objects.get_or_create(
                    variant_size=variant_size,
                    defaults={'quantity_in_stock': 0, 'quantity_reserved': 0}
                )
                
                stock.quantity_in_stock = request.POST.get('quantity_in_stock', 0)
                stock.save()
                
                messages.success(request, 'Stock updated successfully!')
                
        except Exception as e:
            messages.error(request, f'Error updating stock: {str(e)}')
        
        return redirect('admin-product-edit', pk=variant_size.variant.product.id)


class AdminVariantSizeDeleteView(View):
    """Admin view for deleting a variant size"""
    
    @admin_required
    def post(self, request, variant_size_id):
        variant_size = get_object_or_404(VariantSize, pk=variant_size_id)
        product_id = variant_size.variant.product.id
        
        try:
            variant_size.delete()
            messages.success(request, 'Size deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting size: {str(e)}')
        
        return redirect('admin-product-edit', pk=product_id)


class AdminProductImageUploadView(View):
    """Admin view for uploading product images"""
    
    @admin_required
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        
        try:
            # Get the highest display order
            max_order = ProductImage.objects.filter(product=product).aggregate(
                max_order=Sum('display_order')
            )['max_order'] or 0
            
            ProductImage.objects.create(
                product=product,
                image_url=request.POST.get('image_url'),
                alt_text=request.POST.get('alt_text', ''),
                is_primary=request.POST.get('is_primary') == 'on',
                display_order=max_order + 1
            )
            
            # If this is set as primary, unset others
            if request.POST.get('is_primary') == 'on':
                ProductImage.objects.filter(product=product).exclude(
                    image_url=request.POST.get('image_url')
                ).update(is_primary=False)
            
            messages.success(request, 'Image uploaded successfully!')
            
        except Exception as e:
            messages.error(request, f'Error uploading image: {str(e)}')
        
        return redirect('admin-product-edit', pk=product_id)


class AdminProductImageDeleteView(View):
    """Admin view for deleting a product image"""
    
    @admin_required
    def post(self, request, image_id):
        image = get_object_or_404(ProductImage, pk=image_id)
        product_id = image.product.id
        
        try:
            image.delete()
            messages.success(request, 'Image deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting image: {str(e)}')
        
        return redirect('admin-product-edit', pk=product_id)
