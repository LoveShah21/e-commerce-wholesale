from django.urls import path
from .views import (
    InquiryListCreateView, InquiryDetailView,
    QuotationRequestCreateView, QuotationRequestDetailView,
    QuotationPriceCreateView, QuotationPriceSendView, QuotationPriceAcceptRejectView,
    ComplaintListCreateView, ComplaintDetailView, ComplaintStatusUpdateView,
    FeedbackCreateView, FeedbackListView, FeedbackDetailView
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
]
