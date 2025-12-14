from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderListCreateView, OrderDetailView, CartViewSet, CartItemViewSet
from .admin_views import (
    AdminOrderListView, AdminOrderDetailView, AdminOrderMaterialRequirementsView
)

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    
    # Admin order management URLs
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:order_id>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:order_id>/materials/', AdminOrderMaterialRequirementsView.as_view(), name='admin-order-materials'),
]
