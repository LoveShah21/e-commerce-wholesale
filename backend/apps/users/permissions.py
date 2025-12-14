from rest_framework import permissions
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from functools import wraps


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to all users,
    but write access only to admin users.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'


class IsOperator(permissions.BasePermission):
    """
    Custom permission to only allow operator users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'operator'


class IsAdminOrOperator(permissions.BasePermission):
    """
    Custom permission to allow admin or operator users.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.user_type in ['admin', 'operator'])


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow users to access their own objects,
    or allow admin users to access any object.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access any object
        if request.user.user_type == 'admin':
            return True
        
        # Check if object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        if obj == request.user:
            return True
        
        return False


# Mixin for class-based views requiring admin access
class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin for class-based views that checks that the user is logged in and is an admin.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'admin'
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('dashboard-web')


# Decorator for view functions/methods requiring admin access
def admin_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is an admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if request.user.user_type != 'admin':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard-web')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


# Decorator for view functions/methods requiring admin or operator access
def admin_or_operator_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is an admin or operator.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if request.user.user_type not in ['admin', 'operator']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard-web')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
