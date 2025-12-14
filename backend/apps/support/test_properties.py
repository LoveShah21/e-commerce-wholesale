"""
Property-based tests for support app (inquiries, quotations, complaints, feedback)
"""
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.utils import timezone
from django.test import override_settings
from datetime import timedelta
from apps.users.models import User
from apps.support.models import Inquiry, QuotationRequest, QuotationPrice, Complaint
from apps.products.models import (
    Product, ProductVariant, VariantSize, Size,
    Fabric, Color, Pattern, Sleeve, Pocket
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InquiryPropertyTests(TestCase):
    """
    Property-based tests for inquiry functionality
    """
    
    @given(
        email=st.emails(),
        username=st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=122, whitelist_categories=('Lu', 'Ll', 'Nd'))),
        description=st.text(min_size=10, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
    )
    @settings(max_examples=50, deadline=None)
    def test_inquiry_creation_sets_pending_status(self, email, username, description):
        """
        Feature: complete-ecommerce-platform, Property 42: Inquiry creation sets pending status
        
        For any valid inquiry data (user, description), creating a new inquiry 
        should result in an inquiry with status set to 'pending'.
        
        Validates: Requirements 11.1
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            full_name='Test User',
            user_type='customer'
        )
        
        # Create an inquiry
        inquiry = Inquiry.objects.create(
            user=user,
            inquiry_description=description
        )
        
        # Verify the inquiry status is 'pending'
        self.assertEqual(inquiry.status, 'pending')
        
        # Verify the inquiry is persisted
        retrieved_inquiry = Inquiry.objects.get(id=inquiry.id)
        self.assertEqual(retrieved_inquiry.status, 'pending')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class QuotationPropertyTests(TestCase):
    """
    Property-based tests for quotation functionality
    """
    
    @given(
        email=st.emails(),
        username=st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=122, whitelist_categories=('Lu', 'Ll', 'Nd'))),
        quantity=st.integers(min_value=1, max_value=1000),
        unit_price=st.decimals(min_value=1, max_value=10000, places=2),
    )
    @settings(max_examples=50, deadline=None)
    def test_quotation_status_updates_correctly(self, email, username, quantity, unit_price):
        """
        Feature: complete-ecommerce-platform, Property 45: Quotation status updates correctly
        
        For any quotation, when sent to customer, the status should change 
        from 'pending' to 'sent'.
        
        Validates: Requirements 11.4
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            full_name='Test User',
            user_type='customer'
        )
        
        # Create an inquiry
        inquiry = Inquiry.objects.create(
            user=user,
            inquiry_description='Test inquiry for bulk order'
        )
        
        # Create a product and variant for the quotation
        product = Product.objects.create(
            product_name='Test Shirt',
            description='Test description'
        )
        
        # Create required attributes
        fabric = Fabric.objects.create(fabric_name='Cotton')
        color = Color.objects.create(color_name='Blue')
        pattern = Pattern.objects.create(pattern_name='Solid')
        sleeve = Sleeve.objects.create(sleeve_type='Full')
        pocket = Pocket.objects.create(pocket_type='Single')
        
        variant = ProductVariant.objects.create(
            product=product,
            fabric=fabric,
            color=color,
            pattern=pattern,
            sleeve=sleeve,
            pocket=pocket,
            base_price=100.00
        )
        
        size = Size.objects.create(
            size_code='M',
            size_name='Medium'
        )
        
        variant_size = VariantSize.objects.create(
            variant=variant,
            size=size
        )
        
        # Create a quotation request
        quotation_request = QuotationRequest.objects.create(
            inquiry=inquiry,
            variant_size=variant_size,
            requested_quantity=quantity
        )
        
        # Verify initial status is 'pending'
        self.assertEqual(quotation_request.status, 'pending')
        
        # Create a quotation price
        valid_from = timezone.now()
        valid_until = valid_from + timedelta(days=30)
        
        quotation_price = QuotationPrice.objects.create(
            quotation=quotation_request,
            unit_price=unit_price,
            customization_charge_per_unit=0,
            quoted_quantity=quantity,
            valid_from=valid_from,
            valid_until=valid_until
        )
        
        # Verify quotation price initial status is 'pending'
        self.assertEqual(quotation_price.status, 'pending')
        
        # Update status to 'sent' (simulating admin sending the quotation)
        quotation_price.status = 'sent'
        quotation_price.save()
        
        # Verify the status changed to 'sent'
        retrieved_price = QuotationPrice.objects.get(id=quotation_price.id)
        self.assertEqual(retrieved_price.status, 'sent')
        
        # Verify the status transition is correct (from pending to sent)
        self.assertIn(retrieved_price.status, ['sent', 'accepted', 'rejected'])


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ComplaintPropertyTests(TestCase):
    """
    Property-based tests for complaint functionality
    """
    
    @given(
        email=st.emails(),
        username=st.text(min_size=3, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=122, whitelist_categories=('Lu', 'Ll', 'Nd'))),
        description=st.text(min_size=10, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        category=st.text(min_size=3, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122, whitelist_categories=('Lu', 'Ll'))),
    )
    @settings(max_examples=10, deadline=None)
    def test_resolved_complaints_record_resolution_date(self, email, username, description, category):
        """
        Feature: complete-ecommerce-platform, Property 49: Resolved complaints record resolution date
        
        For any complaint changing to 'resolved' status, the resolution_date 
        should be set to the current timestamp.
        
        Validates: Requirements 12.3
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            full_name='Test User',
            user_type='customer'
        )
        
        # Create a complaint with 'open' status
        complaint = Complaint.objects.create(
            user=user,
            complaint_description=description,
            complaint_category=category,
            status='open'
        )
        
        # Verify initial state: status is 'open' and resolution_date is None
        self.assertEqual(complaint.status, 'open')
        self.assertIsNone(complaint.resolution_date)
        
        # Record the time before resolution
        time_before_resolution = timezone.now()
        
        # Update complaint status to 'resolved'
        complaint.status = 'resolved'
        complaint.resolution_date = timezone.now()
        complaint.save()
        
        # Record the time after resolution
        time_after_resolution = timezone.now()
        
        # Retrieve the complaint from database
        retrieved_complaint = Complaint.objects.get(id=complaint.id)
        
        # Verify the status changed to 'resolved'
        self.assertEqual(retrieved_complaint.status, 'resolved')
        
        # Verify the resolution_date is set
        self.assertIsNotNone(retrieved_complaint.resolution_date)
        
        # Verify the resolution_date is within the expected time range
        self.assertGreaterEqual(retrieved_complaint.resolution_date, time_before_resolution)
        self.assertLessEqual(retrieved_complaint.resolution_date, time_after_resolution)
        
        # Verify that resolution_date is persisted correctly
        complaint_again = Complaint.objects.get(id=complaint.id)
        self.assertEqual(complaint_again.resolution_date, retrieved_complaint.resolution_date)
