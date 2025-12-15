from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from apps.users.permissions import IsAdminOrReadOnly, IsAdmin
from services.cache_service import CacheService
from .models import (
    Product, ProductVariant, VariantSize, Stock, ProductImage
)
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductCreateSerializer,
    ProductUpdateSerializer, ProductVariantSerializer, ProductVariantCreateSerializer,
    ProductVariantUpdateSerializer, VariantSizeSerializer, VariantSizeCreateSerializer,
    StockUpdateSerializer, ProductImageSerializer, ProductImageCreateSerializer
)


class ProductListCreateView(generics.ListCreateAPIView):
    """
    List all products or create a new product.
    GET: Public access (with caching)
    POST: Admin only (invalidates cache)
    
    Optimized with select_related and prefetch_related for better performance.
    Implements caching for product list queries.
    """
    queryset = Product.objects.all().prefetch_related(
        'images',
        'variants__fabric',
        'variants__color',
        'variants__pattern',
        'variants__sleeve',
        'variants__pocket'
    ).order_by('-created_at')
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('variants__fabric', 'variants__color', 'variants__pattern')
    search_fields = ('product_name', 'description')
    ordering_fields = ('product_name', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductListSerializer
    
    def list(self, request, *args, **kwargs):
        """Override list to implement caching."""
        # Build cache key from query parameters
        filters = {
            'fabric': request.query_params.get('variants__fabric'),
            'color': request.query_params.get('variants__color'),
            'pattern': request.query_params.get('variants__pattern'),
            'search': request.query_params.get('search'),
            'ordering': request.query_params.get('ordering', '-created_at'),
            'page': request.query_params.get('page', '1'),
        }
        
        # Try to get from cache
        cached_response = CacheService.get_product_list_cache(filters)
        if cached_response is not None:
            return Response(cached_response)
        
        # Get data from database
        response = super().list(request, *args, **kwargs)
        
        # Cache the response data
        CacheService.set_product_list_cache(response.data, filters)
        
        return response
    
    def create(self, request, *args, **kwargs):
        """Override create to invalidate cache."""
        response = super().create(request, *args, **kwargs)
        
        # Invalidate product cache after creation
        CacheService.invalidate_product_cache()
        
        return response


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product.
    GET: Public access (with caching)
    PUT/PATCH/DELETE: Admin only (invalidates cache)
    
    Optimized with comprehensive prefetch_related and select_related.
    Implements caching for product detail queries.
    """
    queryset = Product.objects.all().prefetch_related(
        'images',
        'variants__fabric',
        'variants__color',
        'variants__pattern',
        'variants__sleeve',
        'variants__pocket',
        'variants__sizes__size',
        'variants__sizes__stock_record'
    )
    permission_classes = (IsAdminOrReadOnly,)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductUpdateSerializer
        return ProductDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to implement caching."""
        product_id = kwargs.get('pk')
        
        # Try to get from cache
        cached_data = CacheService.get_product_detail_cache(product_id)
        if cached_data is not None:
            return Response(cached_data)
        
        # Get data from database
        response = super().retrieve(request, *args, **kwargs)
        
        # Cache the response data
        CacheService.set_product_detail_cache(product_id, response.data)
        
        return response
    
    def update(self, request, *args, **kwargs):
        """Override update to invalidate cache."""
        response = super().update(request, *args, **kwargs)
        
        # Invalidate cache for this product and product list
        product_id = kwargs.get('pk')
        CacheService.invalidate_product_cache(product_id)
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to invalidate cache."""
        product_id = kwargs.get('pk')
        response = super().destroy(request, *args, **kwargs)
        
        # Invalidate cache for this product and product list
        CacheService.invalidate_product_cache(product_id)
        
        return response


class ProductVariantListCreateView(APIView):
    """
    List variants for a product or create a new variant.
    GET: Public access
    POST: Admin only
    """
    permission_classes = (IsAdminOrReadOnly,)
    
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        variants = product.variants.all().select_related(
            'fabric', 'color', 'pattern', 'sleeve', 'pocket'
        ).prefetch_related(
            'sizes__size',
            'sizes__stock_record'
        )
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)
    
    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductVariantCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                variant = serializer.save(product=product)
            
            # Return full variant data
            response_serializer = ProductVariantSerializer(variant)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product variant.
    GET: Public access
    PUT/PATCH/DELETE: Admin only
    
    Optimized with select_related and prefetch_related.
    """
    queryset = ProductVariant.objects.all().select_related(
        'product',
        'fabric',
        'color',
        'pattern',
        'sleeve',
        'pocket'
    ).prefetch_related(
        'sizes__size',
        'sizes__stock_record'
    )
    permission_classes = (IsAdminOrReadOnly,)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductVariantUpdateSerializer
        return ProductVariantSerializer


class VariantSizeListCreateView(APIView):
    """
    List sizes for a variant or add a new size.
    GET: Public access
    POST: Admin only
    """
    permission_classes = (IsAdminOrReadOnly,)
    
    def get(self, request, variant_id):
        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            return Response(
                {'error': 'Variant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        sizes = variant.sizes.all().select_related('size', 'stock_record')
        serializer = VariantSizeSerializer(sizes, many=True)
        return Response(serializer.data)
    
    def post(self, request, variant_id):
        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            return Response(
                {'error': 'Variant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = VariantSizeCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                variant_size = serializer.save(variant=variant)
                # Create stock record
                Stock.objects.create(
                    variant_size=variant_size,
                    quantity_in_stock=serializer.validated_data.get('stock_quantity', 0)
                )
            
            # Return full size data
            response_serializer = VariantSizeSerializer(variant_size)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockUpdateView(APIView):
    """
    Get or update stock for a variant size.
    GET: Public access (for stock availability checks)
    PUT/PATCH: Admin only
    """
    
    def get_permissions(self):
        """Allow public GET, but require admin for other methods."""
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsAdmin()]
    
    def get(self, request, variant_size_id):
        """Get stock availability for a variant size."""
        try:
            variant_size = VariantSize.objects.select_related(
                'stock_record'
            ).get(id=variant_size_id)
        except VariantSize.DoesNotExist:
            return Response(
                {'error': 'Variant size not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create stock record
        stock, created = Stock.objects.get_or_create(
            variant_size=variant_size,
            defaults={
                'quantity_in_stock': variant_size.stock_quantity,
                'quantity_reserved': 0
            }
        )
        
        return Response({
            'variant_size_id': variant_size_id,
            'quantity_in_stock': stock.quantity_in_stock,
            'quantity_reserved': stock.quantity_reserved,
            'quantity_available': stock.quantity_available
        })
    
    def patch(self, request, variant_size_id):
        try:
            variant_size = VariantSize.objects.get(id=variant_size_id)
        except VariantSize.DoesNotExist:
            return Response(
                {'error': 'Variant size not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StockUpdateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Get or create stock record
                stock, created = Stock.objects.get_or_create(
                    variant_size=variant_size,
                    defaults={'quantity_in_stock': 0, 'quantity_reserved': 0}
                )
                
                # Update stock fields
                if 'quantity_in_stock' in serializer.validated_data:
                    stock.quantity_in_stock = serializer.validated_data['quantity_in_stock']
                
                if 'quantity_reserved' in serializer.validated_data:
                    stock.quantity_reserved = serializer.validated_data['quantity_reserved']
                
                stock.save()
            
            return Response({
                'message': 'Stock updated successfully',
                'quantity_in_stock': stock.quantity_in_stock,
                'quantity_reserved': stock.quantity_reserved,
                'quantity_available': stock.quantity_available
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductImageUploadView(APIView):
    """
    Upload images for a product.
    POST: Admin only
    """
    permission_classes = (IsAdmin,)
    
    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductImageCreateSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.save(product=product)
            response_serializer = ProductImageSerializer(image)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
