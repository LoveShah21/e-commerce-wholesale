from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.users.web_views import WebLoginView, WebRegisterView, web_logout, ProfileView
from apps.products.web_views import ProductListView, ProductDetailView
from apps.products.admin_views import (
    AdminProductListView, AdminProductCreateView, AdminProductEditView, AdminProductDeleteView,
    AdminVariantCreateView, AdminVariantUpdateView, AdminVariantDeleteView,
    AdminVariantSizeCreateView, AdminVariantSizeUpdateView, AdminVariantSizeDeleteView,
    AdminProductImageUploadView, AdminProductImageDeleteView
)
from apps.dashboard.web_views import DashboardWebView
from apps.orders.web_views import OrderListView
from apps.orders.cart_web_views import CartView, CheckoutView, OrderTrackingView, FinalPaymentView
from apps.support.web_views import InquirySubmissionView, InquiryListView, FeedbackSubmissionView, ComplaintListView
from apps.support.admin_views import (
    AdminInquiryListView, AdminInquiryDetailView,
    AdminComplaintListView, AdminComplaintDetailView, AdminComplaintResolveView,
    AdminFeedbackListView
)
from apps.users.admin_views import (
    AdminUserListView, AdminUserDetailView, AdminUserCreateView, 
    AdminUserEditView, AdminUserDeleteView, AdminUserStatusToggleView
)
from apps.orders.admin_views import (
    AdminOrderListView, AdminOrderDetailView, AdminOrderMaterialRequirementsView
)
from apps.manufacturing.web_views import (
    inventory_overview, material_list, material_create, material_edit, material_update_quantity, material_update_reorder_level, material_delete,
    supplier_list, supplier_create, supplier_edit, supplier_delete,
    material_supplier_list, material_supplier_create, material_supplier_edit, material_supplier_delete,
    material_type_create,
    manufacturing_spec_list, manufacturing_spec_create, manufacturing_spec_edit, manufacturing_spec_delete,
    manufacturing_orders_list, manufacturing_order_materials
)
from apps.finance.web_views import (
    PaymentSuccessView, PaymentFailureView, PaymentHistoryView, OrderPaymentView,
    InvoicePreviewView
)
from apps.reports.admin_views import (
    AdminReportsListView, AdminSalesReportView, 
    AdminOrderReportView, AdminFinancialReportView
)
from django.views.generic import TemplateView

urlpatterns = [
    # Admin Product Management Routes (must be before admin.site.urls)
    path('admin/products/', AdminProductListView.as_view(), name='admin-product-list'),
    path('admin/products/create/', AdminProductCreateView.as_view(), name='admin-product-create'),
    path('admin/products/<int:pk>/edit/', AdminProductEditView.as_view(), name='admin-product-edit'),
    path('admin/products/<int:pk>/delete/', AdminProductDeleteView.as_view(), name='admin-product-delete'),
    path('admin/products/<int:product_id>/variants/create/', AdminVariantCreateView.as_view(), name='admin-variant-create'),
    path('admin/products/variants/<int:variant_id>/update/', AdminVariantUpdateView.as_view(), name='admin-variant-update'),
    path('admin/products/variants/<int:variant_id>/delete/', AdminVariantDeleteView.as_view(), name='admin-variant-delete'),
    path('admin/products/variants/<int:variant_id>/sizes/add/', AdminVariantSizeCreateView.as_view(), name='admin-variant-size-create'),
    path('admin/products/sizes/<int:variant_size_id>/stock/update/', AdminVariantSizeUpdateView.as_view(), name='admin-variant-size-update'),
    path('admin/products/sizes/<int:variant_size_id>/delete/', AdminVariantSizeDeleteView.as_view(), name='admin-variant-size-delete'),
    path('admin/products/<int:product_id>/images/upload/', AdminProductImageUploadView.as_view(), name='admin-product-image-upload'),
    path('admin/products/images/<int:image_id>/delete/', AdminProductImageDeleteView.as_view(), name='admin-product-image-delete'),
    
    # Admin Support Routes (must be before admin.site.urls)
    path('admin/inquiries/', AdminInquiryListView.as_view(), name='admin-inquiry-list'),
    path('admin/inquiries/<int:pk>/', AdminInquiryDetailView.as_view(), name='admin-inquiry-detail'),
    path('admin/complaints/', AdminComplaintListView.as_view(), name='admin-complaint-list'),
    path('admin/complaints/<int:pk>/', AdminComplaintDetailView.as_view(), name='admin-complaint-detail'),
    path('admin/complaints/<int:pk>/resolve/', AdminComplaintResolveView.as_view(), name='admin-complaint-resolve'),
    path('admin/feedback/', AdminFeedbackListView.as_view(), name='admin-feedback-list'),
    
    # Admin Order Management Routes (must be before admin.site.urls)
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:order_id>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:order_id>/materials/', AdminOrderMaterialRequirementsView.as_view(), name='admin-order-materials'),
    
    # Admin User Management Routes (must be before admin.site.urls)
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/create/', AdminUserCreateView.as_view(), name='admin-user-create'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/edit/', AdminUserEditView.as_view(), name='admin-user-edit'),
    path('admin/users/<int:user_id>/delete/', AdminUserDeleteView.as_view(), name='admin-user-delete'),
    path('admin/users/<int:user_id>/toggle-status/', AdminUserStatusToggleView.as_view(), name='admin-user-status-toggle'),
    
    # Admin Reports Routes (must be before admin.site.urls)
    path('admin/reports/', AdminReportsListView.as_view(), name='admin-reports-list'),
    path('admin/reports/sales/', AdminSalesReportView.as_view(), name='admin-sales-report'),
    path('admin/reports/orders/', AdminOrderReportView.as_view(), name='admin-order-report'),
    path('admin/reports/financial/', AdminFinancialReportView.as_view(), name='admin-financial-report'),
    

    
    # Django Admin (must come after custom admin/* routes)
    path('admin/', admin.site.urls),
    
    # Web Routes
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', WebLoginView.as_view(), name='login'),
    path('register/', WebRegisterView.as_view(), name='register'),
    path('logout/', web_logout, name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Product Routes (Customer)
    path('products/', ProductListView.as_view(), name='product-list-web'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail-web'),
    
    # Cart and Checkout Routes
    path('cart/', CartView.as_view(), name='cart-web'),
    path('checkout/', CheckoutView.as_view(), name='checkout-web'),
    
    # Order Routes
    path('orders/', OrderListView.as_view(), name='order-list-web'),
    path('orders/<int:order_id>/final-payment/', FinalPaymentView.as_view(), name='final-payment-web'),
    path('order-tracking/<int:order_id>/', OrderTrackingView.as_view(), name='order-tracking-web'),
    
    # Support Routes
    path('inquiry/', InquirySubmissionView.as_view(), name='inquiry-web'),
    path('inquiries/', InquiryListView.as_view(), name='inquiries-list-web'),
    path('feedback/', FeedbackSubmissionView.as_view(), name='feedback-web'),
    path('complaints/', ComplaintListView.as_view(), name='complaints-list-web'),
    
    # Dashboard
    path('dashboard/', DashboardWebView.as_view(), name='dashboard-web'),

    # Inventory Management Routes
    path('inventory/', inventory_overview, name='inventory-overview-web'),
    path('inventory/materials/', material_list, name='material-list-web'),
    path('inventory/materials/create/', material_create, name='material-create-web'),
    path('inventory/materials/<int:material_id>/edit/', material_edit, name='material-edit-web'),
    path('inventory/materials/<int:material_id>/quantity/', material_update_quantity, name='material-quantity-update-web'),
    path('inventory/materials/<int:material_id>/reorder-level/', material_update_reorder_level, name='material-reorder-level-update-web'),
    path('inventory/materials/<int:material_id>/delete/', material_delete, name='material-delete-web'),
    path('inventory/suppliers/', supplier_list, name='supplier-list-web'),
    path('inventory/suppliers/create/', supplier_create, name='supplier-create-web'),
    path('inventory/suppliers/<int:supplier_id>/edit/', supplier_edit, name='supplier-edit-web'),
    path('inventory/suppliers/<int:supplier_id>/delete/', supplier_delete, name='supplier-delete-web'),
    path('inventory/material-suppliers/', material_supplier_list, name='material-supplier-list-web'),
    path('inventory/material-suppliers/create/', material_supplier_create, name='material-supplier-create-web'),
    path('inventory/material-suppliers/<int:ms_id>/edit/', material_supplier_edit, name='material-supplier-edit-web'),
    path('inventory/material-suppliers/<int:ms_id>/delete/', material_supplier_delete, name='material-supplier-delete-web'),
    path('inventory/material-types/create/', material_type_create, name='material-type-create-web'),

    # Manufacturing Workflow Routes
    path('manufacturing/specifications/', manufacturing_spec_list, name='manufacturing-spec-list-web'),
    path('manufacturing/specifications/create/', manufacturing_spec_create, name='manufacturing-spec-create-web'),
    path('manufacturing/specifications/<int:spec_id>/edit/', manufacturing_spec_edit, name='manufacturing-spec-edit-web'),
    path('manufacturing/specifications/<int:spec_id>/delete/', manufacturing_spec_delete, name='manufacturing-spec-delete-web'),
    path('manufacturing/orders/', manufacturing_orders_list, name='manufacturing-orders-web'),
    path('manufacturing/orders/<int:order_id>/materials/', manufacturing_order_materials, name='manufacturing-order-materials-web'),

    # Payment Routes
    path('payments/success/', PaymentSuccessView.as_view(), name='payment-success-web'),
    path('payments/failure/', PaymentFailureView.as_view(), name='payment-failure-web'),
    path('payments/history/', PaymentHistoryView.as_view(), name='payment-history-web'),
    path('payments/order/<int:order_id>/', OrderPaymentView.as_view(), name='order-payment-web'),
    
    # Invoice Routes
    path('invoices/<int:order_id>/preview/', InvoicePreviewView.as_view(), name='invoice-preview-web'),

    # API Routes
    path('api/users/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/support/', include('apps.support.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/manufacturing/', include('apps.manufacturing.urls')),
    path('api/', include('apps.finance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'django.views.defaults.page_not_found'
handler403 = 'django.views.defaults.permission_denied'
handler500 = 'django.views.defaults.server_error'
