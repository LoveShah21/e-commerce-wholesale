from rest_framework import generics, permissions
from .models import Inquiry, Complaint, Feedback
from .serializers import InquirySerializer, ComplaintSerializer, FeedbackSerializer

class InquiryListCreateView(generics.ListCreateAPIView):
    serializer_class = InquirySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Inquiry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ComplaintListCreateView(generics.ListCreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Complaint.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
