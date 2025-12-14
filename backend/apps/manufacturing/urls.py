from django.urls import path
from .views import (
    RawMaterialListCreateView, RawMaterialDetailView, MaterialQuantityUpdateView,
    MaterialTypeListCreateView, MaterialTypeDetailView,
    SupplierListCreateView, SupplierDetailView,
    MaterialSupplierListCreateView, MaterialSupplierDetailView,
    InventoryViewAPIView, ReorderAlertsView,
    ManufacturingSpecificationListCreateView, ManufacturingSpecificationDetailView
)

urlpatterns = [
    # Raw Material endpoints
    path('materials/', RawMaterialListCreateView.as_view(), name='material-list-create'),
    path('materials/<int:pk>/', RawMaterialDetailView.as_view(), name='material-detail'),
    path('materials/<int:material_id>/quantity/', MaterialQuantityUpdateView.as_view(), name='material-quantity-update'),
    
    # Material Type endpoints
    path('material-types/', MaterialTypeListCreateView.as_view(), name='material-type-list-create'),
    path('material-types/<int:pk>/', MaterialTypeDetailView.as_view(), name='material-type-detail'),
    
    # Supplier endpoints
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier-detail'),
    
    # Material-Supplier association endpoints
    path('material-suppliers/', MaterialSupplierListCreateView.as_view(), name='material-supplier-list-create'),
    path('material-suppliers/<int:pk>/', MaterialSupplierDetailView.as_view(), name='material-supplier-detail'),
    
    # Inventory view endpoints
    path('inventory/', InventoryViewAPIView.as_view(), name='inventory-view'),
    path('inventory/alerts/', ReorderAlertsView.as_view(), name='reorder-alerts'),
    
    # Manufacturing Specification endpoints
    path('specifications/', ManufacturingSpecificationListCreateView.as_view(), name='specification-list-create'),
    path('specifications/<int:pk>/', ManufacturingSpecificationDetailView.as_view(), name='specification-detail'),
]
