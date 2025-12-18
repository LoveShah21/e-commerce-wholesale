from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

class InquirySubmissionView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'support/inquiry.html')

class InquiryListView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'support/inquiries_list.html')

class FeedbackSubmissionView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'support/feedback.html')

class ComplaintListView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'support/complaints_list.html')
