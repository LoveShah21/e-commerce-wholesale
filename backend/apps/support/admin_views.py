from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.db import transaction
from django.utils import timezone
from apps.users.permissions import AdminRequiredMixin
from .models import Inquiry, QuotationRequest, QuotationPrice, Complaint, Feedback
from apps.products.models import Product, ProductVariant, VariantSize


class AdminInquiryListView(AdminRequiredMixin, View):
    """Admin view for listing all inquiries"""
    
    def get(self, request):
        inquiries = Inquiry.objects.select_related('user').prefetch_related(
            'quotation_requests__variant_size__variant__product',
            'quotation_requests__prices'
        ).order_by('-inquiry_date')
        
        # Apply status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            inquiries = inquiries.filter(status=status_filter)
        
        # Apply search
        search_query = request.GET.get('search', '')
        if search_query:
            inquiries = inquiries.filter(
                Q(inquiry_description__icontains=search_query) |
                Q(user__full_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        context = {
            'inquiries': inquiries,
            'status_filter': status_filter,
            'search_query': search_query,
            'status_choices': Inquiry.STATUS_CHOICES,
        }
        
        return render(request, 'support/admin/inquiry_list.html', context)


class AdminInquiryDetailView(AdminRequiredMixin, View):
    """Admin view for viewing inquiry details and managing quotations"""
    
    def get(self, request, pk):
        inquiry = get_object_or_404(
            Inquiry.objects.select_related('user').prefetch_related(
                Prefetch(
                    'quotation_requests',
                    queryset=QuotationRequest.objects.select_related(
                        'variant_size__variant__product',
                        'variant_size__variant__fabric',
                        'variant_size__variant__color',
                        'variant_size__variant__pattern',
                        'variant_size__size'
                    ).prefetch_related('prices')
                )
            ),
            pk=pk
        )
        
        # Get all products for quotation request form
        products = Product.objects.prefetch_related(
            'variants__fabric',
            'variants__color',
            'variants__pattern',
            'variants__sizes__size'
        ).all()
        
        context = {
            'inquiry': inquiry,
            'products': products,
        }
        
        return render(request, 'support/admin/inquiry_detail.html', context)


class AdminQuotationRequestCreateView(AdminRequiredMixin, View):
    """Admin view for creating a quotation request"""
    
    def post(self, request, inquiry_id):
        inquiry = get_object_or_404(Inquiry, pk=inquiry_id)
        
        try:
            with transaction.atomic():
                quotation_request = QuotationRequest.objects.create(
                    inquiry=inquiry,
                    variant_size_id=request.POST.get('variant_size'),
                    requested_quantity=request.POST.get('requested_quantity'),
                    customization_type=request.POST.get('customization_type', ''),
                    customization_details=request.POST.get('customization_details', '')
                )
                
                # Update inquiry status to reviewed
                if inquiry.status == 'pending':
                    inquiry.status = 'reviewed'
                    inquiry.save()
                
                messages.success(request, 'Quotation request created successfully!')
                
        except Exception as e:
            messages.error(request, f'Error creating quotation request: {str(e)}')
        
        return redirect('admin-inquiry-detail', pk=inquiry_id)


class AdminQuotationPriceCreateView(AdminRequiredMixin, View):
    """Admin view for providing a price quote"""
    
    def post(self, request, quotation_request_id):
        quotation_request = get_object_or_404(QuotationRequest, pk=quotation_request_id)
        
        try:
            with transaction.atomic():
                # Parse dates
                valid_from = timezone.datetime.strptime(
                    request.POST.get('valid_from'), '%Y-%m-%d'
                )
                valid_until = timezone.datetime.strptime(
                    request.POST.get('valid_until'), '%Y-%m-%d'
                )
                
                # Make timezone aware
                valid_from = timezone.make_aware(valid_from)
                valid_until = timezone.make_aware(valid_until)
                
                quotation_price = QuotationPrice.objects.create(
                    quotation=quotation_request,
                    unit_price=request.POST.get('unit_price'),
                    customization_charge_per_unit=request.POST.get('customization_charge_per_unit', 0),
                    quoted_quantity=request.POST.get('quoted_quantity'),
                    valid_from=valid_from,
                    valid_until=valid_until
                )
                
                # Update quotation request status to quoted
                quotation_request.status = 'quoted'
                quotation_request.save()
                
                # Update inquiry status to quoted
                inquiry = quotation_request.inquiry
                inquiry.status = 'quoted'
                inquiry.save()
                
                messages.success(request, 'Quotation price provided successfully!')
                
        except Exception as e:
            messages.error(request, f'Error providing quotation price: {str(e)}')
        
        return redirect('admin-inquiry-detail', pk=quotation_request.inquiry.id)


class AdminQuotationPriceSendView(AdminRequiredMixin, View):
    """Admin view for sending a quotation to customer"""
    
    def post(self, request, quotation_price_id):
        quotation_price = get_object_or_404(QuotationPrice, pk=quotation_price_id)
        
        try:
            if quotation_price.status != 'pending':
                messages.warning(request, 'Quotation has already been sent or processed.')
                return redirect('admin-inquiry-detail', pk=quotation_price.quotation.inquiry.id)
            
            # Update status to sent
            quotation_price.status = 'sent'
            quotation_price.save()
            
            # TODO: Send notification to customer (email/SMS)
            
            messages.success(request, 'Quotation sent to customer successfully!')
            
        except Exception as e:
            messages.error(request, f'Error sending quotation: {str(e)}')
        
        return redirect('admin-inquiry-detail', pk=quotation_price.quotation.inquiry.id)


class AdminQuotationStatusUpdateView(AdminRequiredMixin, View):
    """Admin view for updating quotation status"""
    
    def post(self, request, quotation_request_id):
        quotation_request = get_object_or_404(QuotationRequest, pk=quotation_request_id)
        
        try:
            new_status = request.POST.get('status')
            
            if new_status in dict(QuotationRequest.STATUS_CHOICES):
                quotation_request.status = new_status
                quotation_request.save()
                
                messages.success(request, f'Quotation status updated to {new_status}!')
            else:
                messages.error(request, 'Invalid status value.')
                
        except Exception as e:
            messages.error(request, f'Error updating quotation status: {str(e)}')
        
        return redirect('admin-inquiry-detail', pk=quotation_request.inquiry.id)


class AdminComplaintListView(AdminRequiredMixin, View):
    """Admin view for listing all complaints"""
    
    def get(self, request):
        complaints = Complaint.objects.select_related('user', 'order').prefetch_related('order__items').order_by('-complaint_date')
        
        # Apply status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            complaints = complaints.filter(status=status_filter)
        
        # Apply category filter
        category_filter = request.GET.get('category', '')
        if category_filter:
            complaints = complaints.filter(complaint_category__icontains=category_filter)
        
        # Apply search
        search_query = request.GET.get('search', '')
        if search_query:
            complaints = complaints.filter(
                Q(complaint_description__icontains=search_query) |
                Q(user__full_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(complaint_category__icontains=search_query)
            )
        
        context = {
            'complaints': complaints,
            'status_filter': status_filter,
            'category_filter': category_filter,
            'search_query': search_query,
            'status_choices': Complaint.STATUS_CHOICES,
        }
        
        return render(request, 'support/admin/complaint_list.html', context)


class AdminComplaintDetailView(AdminRequiredMixin, View):
    """Admin view for viewing complaint details and resolving complaints"""
    
    def get(self, request, pk):
        complaint = get_object_or_404(
            Complaint.objects.select_related('user', 'order').prefetch_related('order__items'),
            pk=pk
        )
        
        context = {
            'complaint': complaint,
            'status_choices': Complaint.STATUS_CHOICES,
        }
        
        return render(request, 'support/admin/complaint_detail.html', context)


class AdminComplaintResolveView(AdminRequiredMixin, View):
    """Admin view for resolving a complaint"""
    
    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        
        try:
            new_status = request.POST.get('status')
            resolution_notes = request.POST.get('resolution_notes', '')
            
            if new_status not in dict(Complaint.STATUS_CHOICES):
                messages.error(request, 'Invalid status value.')
                return redirect('admin-complaint-detail', pk=pk)
            
            # Update complaint status
            complaint.status = new_status
            
            # If status is resolved, set resolution date
            if new_status == 'resolved' and complaint.resolution_date is None:
                complaint.resolution_date = timezone.now()
            
            # Update resolution notes if provided
            if resolution_notes:
                complaint.resolution_notes = resolution_notes
            
            complaint.save()
            
            messages.success(request, f'Complaint status updated to {new_status}!')
            
        except Exception as e:
            messages.error(request, f'Error updating complaint: {str(e)}')
        
        return redirect('admin-complaint-detail', pk=pk)


class AdminFeedbackListView(AdminRequiredMixin, View):
    """Admin view for viewing all customer feedback"""
    
    def get(self, request):
        feedbacks = Feedback.objects.select_related('user', 'order').prefetch_related('order__items').order_by('-feedback_date')
        
        # Apply rating filter
        rating_filter = request.GET.get('rating', '')
        if rating_filter:
            feedbacks = feedbacks.filter(rating=rating_filter)
        
        # Apply search
        search_query = request.GET.get('search', '')
        if search_query:
            feedbacks = feedbacks.filter(
                Q(feedback_description__icontains=search_query) |
                Q(user__full_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        context = {
            'feedbacks': feedbacks,
            'rating_filter': rating_filter,
            'search_query': search_query,
        }
        
        return render(request, 'support/admin/feedback_list.html', context)
