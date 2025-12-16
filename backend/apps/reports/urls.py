from django.urls import path
from .views import InvoiceDownloadView, SalesReportView
from .admin_views import (
    AdminReportsListView, AdminSalesReportView, 
    AdminOrderReportView, AdminFinancialReportView
)

urlpatterns = [
    # API endpoints
    path('invoice/<int:order_id>/', InvoiceDownloadView.as_view(), name='download-invoice'),
    path('sales/', SalesReportView.as_view(), name='sales-report'),
    
    # Admin web views
    path('admin/', AdminReportsListView.as_view(), name='admin-reports-list'),
    path('admin/sales/', AdminSalesReportView.as_view(), name='admin-sales-report'),
    path('admin/orders/', AdminOrderReportView.as_view(), name='admin-order-report'),
    path('admin/financial/', AdminFinancialReportView.as_view(), name='admin-financial-report'),
]
