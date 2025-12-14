from django.urls import path
from .views import (
    InquiryListCreateView, InquiryDetailView,
    QuotationRequestCreateView, QuotationRequestDetailView,
    QuotationPriceCreateView, QuotationPriceSendView, QuotationPriceAcceptRejectView,
    ComplaintListCreateView, ComplaintDetailView, ComplaintStatusUpdateView,
    FeedbackCreateView, FeedbackListView, FeedbackDetailView
)
from .admin_views import (
    AdminInquiryListView, AdminInquiryDetailView,
    AdminQuotationRequestCreateView, AdminQuotationPriceCreateView,
    AdminQuotationPriceSendView, AdminQuotationStatusUpdateView,
    AdminComplaintListView, AdminComplaintDetailView, AdminComplaintResolveView,
    AdminFeedbackListView
)

urlpatterns = [
    # Inquiry endpoints
    path('inquiries/', InquiryListCreateView.as_view(), name='inquiry-list-create'),
    path('inquiries/<int:pk>/', InquiryDetailView.as_view(), name='inquiry-detail'),
    
    # Quotation request endpoints
    path('quotation-requests/', QuotationRequestCreateView.as_view(), name='quotation-request-create'),
    path('quotation-requests/<int:pk>/', QuotationRequestDetailView.as_view(), name='quotation-request-detail'),
    
    # Quotation price endpoints
    path('quotation-prices/', QuotationPriceCreateView.as_view(), name='quotation-price-create'),
    path('quotation-prices/<int:pk>/send/', QuotationPriceSendView.as_view(), name='quotation-price-send'),
    path('quotation-prices/<int:pk>/respond/', QuotationPriceAcceptRejectView.as_view(), name='quotation-price-respond'),
    
    # Complaint and feedback endpoints
    path('complaints/', ComplaintListCreateView.as_view(), name='complaint-list-create'),
    path('complaints/<int:pk>/', ComplaintDetailView.as_view(), name='complaint-detail'),
    path('complaints/<int:pk>/status/', ComplaintStatusUpdateView.as_view(), name='complaint-status-update'),
    path('feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
    path('feedback/list/', FeedbackListView.as_view(), name='feedback-list'),
    path('feedback/<int:pk>/', FeedbackDetailView.as_view(), name='feedback-detail'),
    
    # Admin inquiry and quotation management
    path('admin/inquiries/', AdminInquiryListView.as_view(), name='admin-inquiry-list'),
    path('admin/inquiries/<int:pk>/', AdminInquiryDetailView.as_view(), name='admin-inquiry-detail'),
    path('admin/inquiries/<int:inquiry_id>/quotation-requests/', AdminQuotationRequestCreateView.as_view(), name='admin-quotation-request-create'),
    path('admin/quotation-requests/<int:quotation_request_id>/price/', AdminQuotationPriceCreateView.as_view(), name='admin-quotation-price-create'),
    path('admin/quotation-prices/<int:quotation_price_id>/send/', AdminQuotationPriceSendView.as_view(), name='admin-quotation-price-send'),
    path('admin/quotation-requests/<int:quotation_request_id>/status/', AdminQuotationStatusUpdateView.as_view(), name='admin-quotation-status-update'),
    
    # Admin complaint and feedback management
    path('admin/complaints/', AdminComplaintListView.as_view(), name='admin-complaint-list'),
    path('admin/complaints/<int:pk>/', AdminComplaintDetailView.as_view(), name='admin-complaint-detail'),
    path('admin/complaints/<int:pk>/resolve/', AdminComplaintResolveView.as_view(), name='admin-complaint-resolve'),
    path('admin/feedback/', AdminFeedbackListView.as_view(), name='admin-feedback-list'),
]
