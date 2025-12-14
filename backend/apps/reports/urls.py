from django.urls import path
from .views import InvoiceDownloadView, SalesReportView

urlpatterns = [
    path('invoice/<int:order_id>/', InvoiceDownloadView.as_view(), name='download-invoice'),
    path('sales/', SalesReportView.as_view(), name='sales-report'),
]
