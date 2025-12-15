"""
Property-based tests for user authentication and role-based access.

These tests verify universal properties that should hold across all inputs.
"""
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
import uuid

User = get_user_model()


class RoleBasedNavigationPropertiesTest(TestCase):
    """Property-based tests for role-based navigation."""
    
    def setUp(self):
        """Set up test data that's needed for all tests."""
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Create users with different roles
        self.customer = User.objects.create_user(
            username=f'customer_{unique_id}',
            email=f'customer_{unique_id}@test.com',
            password='testpass123',
            full_name='Customer User',
            user_type='customer'
        )
        
        self.admin = User.objects.create_user(
            username=f'admin_{unique_id}',
            email=f'admin_{unique_id}@test.com',
            password='testpass123',
            full_name='Admin User',
            user_type='admin'
        )
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()
        
        self.operator = User.objects.create_user(
            username=f'operator_{unique_id}',
            email=f'operator_{unique_id}@test.com',
            password='testpass123',
            full_name='Operator User',
            user_type='operator'
        )
        
        self.client = Client()
    
    @given(
        role=st.sampled_from(['customer', 'admin', 'operator'])
    )
    @settings(max_examples=10, deadline=None)
    def test_property_57_navigation_is_role_appropriate(self, role):
        """
        Feature: complete-ecommerce-platform, Property 57: Navigation is role-appropriate
        
        For any user, the navigation menu should only include links to features
        accessible by their role.
        
        Validates: Requirements 14.2
        """
        # Select user based on role
        if role == 'customer':
            user = self.customer
        elif role == 'admin':
            user = self.admin
        else:  # operator
            user = self.operator
        
        # Login as the user
        self.client.force_login(user)
        
        # Get the dashboard page (which includes navigation)
        response = self.client.get('/dashboard/')
        
        # Check if response is successful
        if response.status_code != 200:
            self.fail(f"Dashboard page returned error: {response.status_code}")
        
        content = response.content.decode('utf-8')
        
        # Define role-specific navigation items
        customer_only_items = [
            'Shopping Cart',
            'My Orders',
            'Payment History',
            'Submit Inquiry',
            'Submit Feedback'
        ]
        
        admin_only_items = [
            'Products',  # Admin product management
            'Manufacturing',
            'Specifications',
            'Inquiries',
            'Complaints',
            'Feedback',
            'Inventory',
            'Users',
            'Reports'
        ]
        
        operator_only_items = [
            'Manufacturing Orders',
            'Specifications',
            'Inventory'
        ]
        
        # Verify customer navigation
        if role == 'customer':
            # Customer should see customer-only items
            for item in customer_only_items:
                self.assertIn(
                    item,
                    content,
                    f"Customer should see '{item}' in navigation"
                )
            
            # Customer should NOT see admin-only items (except common ones)
            admin_specific = ['Users', 'Reports', 'Complaints']
            for item in admin_specific:
                self.assertNotIn(
                    item,
                    content,
                    f"Customer should NOT see '{item}' in navigation"
                )
        
        # Verify admin navigation
        elif role == 'admin':
            # Admin should see admin items
            for item in admin_only_items:
                self.assertIn(
                    item,
                    content,
                    f"Admin should see '{item}' in navigation"
                )
            
            # Admin should NOT see customer-specific items
            customer_specific = ['Shopping Cart', 'Payment History', 'Submit Inquiry', 'Submit Feedback']
            for item in customer_specific:
                self.assertNotIn(
                    item,
                    content,
                    f"Admin should NOT see '{item}' in navigation"
                )
        
        # Verify operator navigation
        elif role == 'operator':
            # Operator should see operator items
            for item in operator_only_items:
                self.assertIn(
                    item,
                    content,
                    f"Operator should see '{item}' in navigation"
                )
            
            # Operator should NOT see customer-specific items
            customer_specific = ['Shopping Cart', 'Payment History', 'Submit Inquiry', 'Submit Feedback']
            for item in customer_specific:
                self.assertNotIn(
                    item,
                    content,
                    f"Operator should NOT see '{item}' in navigation"
                )
            
            # Operator should NOT see admin-specific items
            admin_specific = ['Users', 'Reports', 'Complaints']
            for item in admin_specific:
                self.assertNotIn(
                    item,
                    content,
                    f"Operator should NOT see '{item}' in navigation"
                )
        
        # Verify all users see Dashboard
        self.assertIn(
            'Dashboard',
            content,
            f"All authenticated users should see 'Dashboard' in navigation"
        )
    
    def test_template_tags_work_correctly(self):
        """
        Test that template tags correctly identify user roles.
        This is a unit test to ensure the template tags function properly.
        """
        from apps.users.templatetags.role_tags import has_role, is_customer, is_admin, is_operator
        
        # Test customer
        self.assertTrue(has_role(self.customer, 'customer'))
        self.assertFalse(has_role(self.customer, 'admin'))
        self.assertFalse(has_role(self.customer, 'operator'))
        self.assertTrue(is_customer(self.customer))
        self.assertFalse(is_admin(self.customer))
        self.assertFalse(is_operator(self.customer))
        
        # Test admin
        self.assertTrue(has_role(self.admin, 'admin'))
        self.assertFalse(has_role(self.admin, 'customer'))
        self.assertFalse(has_role(self.admin, 'operator'))
        self.assertFalse(is_customer(self.admin))
        self.assertTrue(is_admin(self.admin))
        self.assertFalse(is_operator(self.admin))
        
        # Test operator
        self.assertTrue(has_role(self.operator, 'operator'))
        self.assertFalse(has_role(self.operator, 'customer'))
        self.assertFalse(has_role(self.operator, 'admin'))
        self.assertFalse(is_customer(self.operator))
        self.assertFalse(is_admin(self.operator))
        self.assertTrue(is_operator(self.operator))
        
        # Test unauthenticated user
        self.assertFalse(has_role(None, 'customer'))
        self.assertFalse(is_customer(None))
        self.assertFalse(is_admin(None))
        self.assertFalse(is_operator(None))
    
    def test_dashboard_redirects_by_role(self):
        """
        Test that dashboard redirects users to appropriate dashboards based on role.
        """
        # Test customer dashboard
        self.client.force_login(self.customer)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Dashboard', response.content)
        
        # Test admin dashboard
        self.client.force_login(self.admin)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        # Admin should see business metrics
        self.assertIn(b'Total Sales', response.content)
        
        # Test operator dashboard
        self.client.force_login(self.operator)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Operator Dashboard', response.content)
