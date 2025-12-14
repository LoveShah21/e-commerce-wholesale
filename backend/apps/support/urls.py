from django.urls import path
from .views import InquiryListCreateView, ComplaintListCreateView, FeedbackCreateView

urlpatterns = [
    path('inquiries/', InquiryListCreateView.as_view(), name='inquiry-list-create'),
    path('complaints/', ComplaintListCreateView.as_view(), name='complaint-list-create'),
    path('feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
]
