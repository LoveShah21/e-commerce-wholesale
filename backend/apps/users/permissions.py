from rest_framework import permissions


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
