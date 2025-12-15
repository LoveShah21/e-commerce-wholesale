"""
Template tags for role-based UI rendering.

These tags help implement conditional navigation and button visibility
based on user roles (customer, admin, operator).
"""
from django import template

register = template.Library()


@register.filter(name='has_role')
def has_role(user, role):
    """
    Check if user has a specific role.
    
    Usage in template:
        {% if user|has_role:"admin" %}
            <!-- Admin-only content -->
        {% endif %}
    
    Args:
        user: User object
        role: Role string ('customer', 'admin', 'operator')
    
    Returns:
        bool: True if user has the specified role
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_type == role


@register.filter(name='is_customer')
def is_customer(user):
    """
    Check if user is a customer.
    
    Usage in template:
        {% if user|is_customer %}
            <!-- Customer-only content -->
        {% endif %}
    """
    return has_role(user, 'customer')


@register.filter(name='is_admin')
def is_admin(user):
    """
    Check if user is an admin.
    
    Usage in template:
        {% if user|is_admin %}
            <!-- Admin-only content -->
        {% endif %}
    """
    return has_role(user, 'admin')


@register.filter(name='is_operator')
def is_operator(user):
    """
    Check if user is an operator.
    
    Usage in template:
        {% if user|is_operator %}
            <!-- Operator-only content -->
        {% endif %}
    """
    return has_role(user, 'operator')


@register.simple_tag
def user_dashboard_url(user):
    """
    Get the appropriate dashboard URL for the user's role.
    
    Usage in template:
        <a href="{% user_dashboard_url user %}">Dashboard</a>
    
    Args:
        user: User object
    
    Returns:
        str: URL path for the user's dashboard
    """
    if not user or not user.is_authenticated:
        return '/login/'
    
    if user.user_type == 'admin':
        return '/dashboard/'
    elif user.user_type == 'operator':
        return '/dashboard/'
    elif user.user_type == 'customer':
        return '/dashboard/'
    else:
        return '/'


@register.simple_tag
def can_access_admin_features(user):
    """
    Check if user can access admin features.
    
    Usage in template:
        {% can_access_admin_features user as can_access %}
        {% if can_access %}
            <!-- Admin features -->
        {% endif %}
    
    Args:
        user: User object
    
    Returns:
        bool: True if user can access admin features
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_type == 'admin'


@register.simple_tag
def can_access_manufacturing(user):
    """
    Check if user can access manufacturing features.
    
    Usage in template:
        {% can_access_manufacturing user as can_access %}
        {% if can_access %}
            <!-- Manufacturing features -->
        {% endif %}
    
    Args:
        user: User object
    
    Returns:
        bool: True if user can access manufacturing features
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_type in ['admin', 'operator']


@register.simple_tag
def can_manage_products(user):
    """
    Check if user can manage products.
    
    Args:
        user: User object
    
    Returns:
        bool: True if user can manage products
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_type == 'admin'


@register.simple_tag
def can_manage_orders(user):
    """
    Check if user can manage orders.
    
    Args:
        user: User object
    
    Returns:
        bool: True if user can manage orders
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_type in ['admin', 'operator']


@register.simple_tag
def can_view_analytics(user):
    """
    Check if user can view analytics.
    
    Args:
        user: User object
    
    Returns:
        bool: True if user can view analytics
    """
    if not user or not user.is_authenticated:
        return False
    return user.user_type == 'admin'
