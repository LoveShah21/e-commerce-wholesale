"""
Integration tests for admin complaint and feedback views
"""
from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User, Address, Country, State, City, PostalCode
from apps.support.models import Complaint, Feedback
from apps.orders.models import Order, Cart


class AdminComplaintViewTests(TestCase):
    """Tests for admin complaint management views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            user_type='admin'
        )
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123',
            full_name='Customer User',
            user_type='customer'
        )
        
        # Create a complaint
        self.complaint = Complaint.objects.create(
            user=self.customer_user,
            complaint_description='Test complaint description',
            complaint_category='Product Quality',
            status='open'
        )
    
    def test_complaint_list_view_requires_admin(self):
        """Test that complaint list view requires admin authentication"""
        # Try to access without login
        response = self.client.get(reverse('admin-complaint-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login as customer
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse('admin-complaint-list'))
        self.assertEqual(response.status_code, 302)  # Redirect (not authorized)
        
        # Login as admin
        self.client.logout()
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin-complaint-list'))
        self.assertEqual(response.status_code, 200)  # Success
    
    def test_complaint_list_view_displays_complaints(self):
        """Test that complaint list view displays complaints"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin-complaint-list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test complaint description')
        self.assertContains(response, 'Product Quality')
    
    def test_complaint_detail_view_displays_details(self):
        """Test that complaint detail view displays complaint details"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin-complaint-detail', kwargs={'pk': self.complaint.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test complaint description')
        self.assertContains(response, 'Customer User')
        self.assertContains(response, 'Product Quality')
    
    def test_complaint_resolve_updates_status(self):
        """Test that resolving a complaint updates its status"""
        self.client.force_login(self.admin_user)
        
        # Resolve the complaint
        response = self.client.post(
            reverse('admin-complaint-resolve', kwargs={'pk': self.complaint.id}),
            {
                'status': 'resolved',
                'resolution_notes': 'Issue resolved by replacing product'
            }
        )
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify complaint was updated
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'resolved')
        self.assertEqual(self.complaint.resolution_notes, 'Issue resolved by replacing product')
        self.assertIsNotNone(self.complaint.resolution_date)


class AdminFeedbackViewTests(TestCase):
    """Tests for admin feedback viewing"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            user_type='admin'
        )
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123',
            full_name='Customer User',
            user_type='customer'
        )
        
        # Create address components
        country = Country.objects.create(country_name='India', country_code='IN')
        state = State.objects.create(country=country, state_name='Gujarat', state_code='GJ')
        city = City.objects.create(state=state, city_name='Surat')
        postal_code = PostalCode.objects.create(city=city, postal_code='395001')
        
        # Create address
        address = Address.objects.create(
            user=self.customer_user,
            address_line1='123 Test St',
            postal_code=postal_code
        )
        
        # Create cart and order
        cart = Cart.objects.create(user=self.customer_user)
        self.order = Order.objects.create(
            user=self.customer_user,
            delivery_address=address,
            total_amount=1000.00,
            status='delivered'
        )
        
        # Create feedback
        self.feedback = Feedback.objects.create(
            user=self.customer_user,
            order=self.order,
            rating=5,
            feedback_description='Great product and service!'
        )
    
    def test_feedback_list_view_requires_admin(self):
        """Test that feedback list view requires admin authentication"""
        # Try to access without login
        response = self.client.get(reverse('admin-feedback-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login as customer
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse('admin-feedback-list'))
        self.assertEqual(response.status_code, 302)  # Redirect (not authorized)
        
        # Login as admin
        self.client.logout()
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin-feedback-list'))
        self.assertEqual(response.status_code, 200)  # Success
    
    def test_feedback_list_view_displays_feedback(self):
        """Test that feedback list view displays feedback"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin-feedback-list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Great product and service!')
        self.assertContains(response, 'Customer User')
