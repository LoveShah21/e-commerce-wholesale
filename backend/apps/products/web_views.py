from django.shortcuts import render, get_object_or_404
from django.views import View
from django.db.models import Q, Min
from .models import Product, Fabric, Color, Pattern

class ProductListView(View):
    def get(self, request):
        products = Product.objects.all().prefetch_related('images', 'variants__variant_sizes__stock_record')
        
        # Apply filters
        fabric_id = request.GET.get('fabric')
        color_id = request.GET.get('color')
        pattern_id = request.GET.get('pattern')
        search_query = request.GET.get('search')
        
        if fabric_id:
            products = products.filter(variants__fabric_id=fabric_id).distinct()
        if color_id:
            products = products.filter(variants__color_id=color_id).distinct()
        if pattern_id:
            products = products.filter(variants__pattern_id=pattern_id).distinct()
        if search_query:
            products = products.filter(
                Q(product_name__icontains=search_query) | 
                Q(description__icontains=search_query)
            ).distinct()
        
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
            'selected_fabric': fabric_id,
            'selected_color': color_id,
            'selected_pattern': pattern_id,
            'search_query': search_query or '',
        }
        
        return render(request, 'products/list.html', context)

class ProductDetailView(View):
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
        return render(request, 'products/detail.html', {'product': product})
