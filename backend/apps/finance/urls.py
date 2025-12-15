"""
Finance URL Configuration
"""

from django.urls import path
from .views import (
    PaymentCreateView, PaymentVerifyView, PaymentFailureView,
    PaymentRetryView, PaymentHistoryView, PaymentStatusView,
    PaymentWebhookView, InvoiceDownloadView, InvoiceDetailView
)

urlpatterns = [
    path('payments/create/', PaymentCreateView.as_view(), name='payment-create'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('payments/failure/', PaymentFailureView.as_view(), name='payment-failure'),
    path('payments/retry/', PaymentRetryView.as_view(), name='payment-retry'),
    path('payments/history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('payments/status/<int:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
    
    # Invoice endpoints
    path('invoices/<int:order_id>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<int:order_id>/download/', InvoiceDownloadView.as_view(), name='invoice-download'),
]
