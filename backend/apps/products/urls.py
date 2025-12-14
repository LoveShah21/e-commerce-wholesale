from django.urls import path
from .views import (
    ProductListCreateView, ProductDetailView, ProductVariantListCreateView,
    ProductVariantDetailView, VariantSizeListCreateView, StockUpdateView,
    ProductImageUploadView
)

urlpatterns = [
    # Product endpoints
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    
    # Variant endpoints
    path('<int:product_id>/variants/', ProductVariantListCreateView.as_view(), name='product-variant-list-create'),
    path('variants/<int:pk>/', ProductVariantDetailView.as_view(), name='variant-detail'),
    
    # Size endpoints
    path('variants/<int:variant_id>/sizes/', VariantSizeListCreateView.as_view(), name='variant-size-list-create'),
    
    # Stock endpoints
    path('sizes/<int:variant_size_id>/stock/', StockUpdateView.as_view(), name='stock-update'),
    
    # Image endpoints
    path('<int:product_id>/images/', ProductImageUploadView.as_view(), name='product-image-upload'),
]
