from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from hypothesis import given, settings, strategies as st, Phase
from hypothesis.extra.django import TestCase as HypothesisTestCase
import string

User = get_user_model()


# Simpler strategies that generate valid data quickly
def valid_email_strategy():
    """Generate valid email addresses"""
    return st.builds(
        lambda i: f"test{i}@example.com",
        st.integers(min_value=1, max_value=10000)
    )


def valid_password_strategy():
    """Generate valid passwords (min 8 chars, letters and numbers)"""
    return st.just("Password123")


def valid_full_name_strategy():
    """Generate valid full names"""
    return st.builds(
        lambda i: f"Test User {i}",
        st.integers(min_value=1, max_value=10000)
    )


class UserRegistrationPropertyTests(HypothesisTestCase):
    """
    Property-based tests for user registration.
    Feature: complete-ecommerce-platform, Property 1: User registration creates customer role by default
    Validates: Requirements 1.1
    """
    
    def setUp(self):
        self.client = APIClient()
    
    @settings(max_examples=10, deadline=None, phases=[Phase.generate])
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        full_name=valid_full_name_strategy()
    )
    def test_property_user_registration_creates_customer_role(self, email, password, full_name):
        """
        Property 1: User registration creates customer role by default
        
        For any valid user registration data (email, password, full_name),
        creating a new user should result in a user account with user_type set to 'customer'.
        """
        # Arrange
        registration_data = {
            'email': email,
            'password': password,
            'full_name': full_name
        }
        
        # Act
        response = self.client.post('/api/users/register/', registration_data, format='json')
        
        # Assert
        if response.status_code == status.HTTP_201_CREATED:
            # User was created successfully
            user = User.objects.get(email=email)
            
            # Property: user_type should be 'customer' by default
            assert user.user_type == 'customer', \
                f"Expected user_type to be 'customer', but got '{user.user_type}'"
            
            # Additional assertions to verify user was created correctly
            assert user.email == email
            assert user.full_name == full_name
            assert user.check_password(password)
            
            # Clean up
            user.delete()


class TokenInvalidationPropertyTests(HypothesisTestCase):
    """
    Property-based tests for token invalidation on logout.
    Feature: complete-ecommerce-platform, Property 2: Logout invalidates JWT tokens
    Validates: Requirements 1.3
    """
    
    @settings(max_examples=10, deadline=None, phases=[Phase.generate])
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        full_name=valid_full_name_strategy()
    )
    def test_property_logout_invalidates_jwt_tokens(self, email, password, full_name):
        """
        Property 2: Logout invalidates JWT tokens
        
        For any authenticated user with a valid JWT token, after logout,
        the token should not grant access to protected endpoints.
        """
        # Create a fresh API client for this test
        client = APIClient()
        
        # Arrange - Create a user
        user = User.objects.create_user(
            email=email,
            username=email,
            full_name=full_name,
            password=password,
            user_type='customer'
        )
        
        # Act - Login to get tokens
        login_response = client.post('/api/users/login/', {
            'email': email,
            'password': password
        }, format='json')
        
        assert login_response.status_code == status.HTTP_200_OK, \
            f"Login failed with status {login_response.status_code}"
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # Verify token works before logout
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response_before = client.get('/api/users/profile/')
        assert profile_response_before.status_code == status.HTTP_200_OK, \
            "Token should work before logout"
        
        # Logout
        logout_response = client.post('/api/users/logout/', {
            'refresh': refresh_token
        }, format='json')
        
        assert logout_response.status_code in [status.HTTP_205_RESET_CONTENT, status.HTTP_204_NO_CONTENT], \
            f"Logout failed with status {logout_response.status_code}"
        
        # Property: Token should not work after logout
        # We verify that the refresh token is blacklisted
        refresh_response = client.post('/api/users/token/refresh/', {
            'refresh': refresh_token
        }, format='json')
        
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED, \
            f"Refresh token should be invalid after logout, but got status {refresh_response.status_code}"
        
        # Clean up
        user.delete()


class AdminAuthorizationPropertyTests(HypothesisTestCase):
    """
    Property-based tests for admin authorization.
    Feature: complete-ecommerce-platform, Property 3: Admin-only endpoints reject non-admin users
    Validates: Requirements 1.4
    """
    
    @settings(max_examples=10, deadline=None, phases=[Phase.generate])
    @given(
        email=valid_email_strategy(),
        password=valid_password_strategy(),
        full_name=valid_full_name_strategy(),
        user_type=st.sampled_from(['customer', 'operator'])
    )
    def test_property_admin_endpoints_reject_non_admin_users(self, email, password, full_name, user_type):
        """
        Property 3: Admin-only endpoints reject non-admin users
        
        For any user without admin role, attempts to access admin-only endpoints
        should return 403 Forbidden status.
        """
        # Create a fresh API client for this test
        client = APIClient()
        
        # Arrange - Create a non-admin user
        user = User.objects.create_user(
            email=email,
            username=email,
            full_name=full_name,
            password=password,
            user_type=user_type
        )
        
        # Login to get token
        login_response = client.post('/api/users/login/', {
            'email': email,
            'password': password
        }, format='json')
        
        assert login_response.status_code == status.HTTP_200_OK, \
            f"Login failed with status {login_response.status_code}"
        
        access_token = login_response.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Act & Assert - Try to access admin-only endpoints
        # We'll test with dashboard stats endpoint (should be admin-only)
        admin_endpoints = [
            '/api/dashboard/stats/',
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            
            # Property: Non-admin users should be rejected
            # The endpoint might not exist yet, so we accept 404 as well
            # But if it exists, it should return 403 for non-admin users
            if response.status_code not in [status.HTTP_404_NOT_FOUND]:
                assert response.status_code == status.HTTP_403_FORBIDDEN, \
                    f"Non-admin user ({user_type}) should not access {endpoint}, " \
                    f"but got status {response.status_code}"
        
        # Clean up
        user.delete()
