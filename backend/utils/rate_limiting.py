"""
Rate limiting utilities for API endpoints.
"""
from functools import wraps
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from rest_framework.response import Response
from rest_framework import status


def api_ratelimit(key='ip', rate='100/h', method='ALL', block=True):
    """
    Decorator for rate limiting API endpoints.
    Returns a proper DRF response when rate limit is exceeded.
    
    Args:
        key: What to rate limit on ('ip', 'user', or callable)
        rate: Rate limit string (e.g., '100/h', '10/m')
        method: HTTP methods to rate limit ('ALL', 'GET', 'POST', etc.)
        block: Whether to block requests that exceed the limit
    
    Usage:
        @api_ratelimit(rate='10/m', method='POST')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key=key, rate=rate, method=method, block=block)
        def wrapped_view(request, *args, **kwargs):
            # Check if request was rate limited
            if getattr(request, 'limited', False):
                return Response(
                    {
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests. Please try again later.',
                        'details': {
                            'rate': rate,
                            'retry_after': '60 seconds'
                        }
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def get_user_or_ip(group, request):
    """
    Rate limit key function that uses user ID if authenticated, otherwise IP.
    
    Usage:
        @ratelimit(key=get_user_or_ip, rate='100/h')
        def my_view(request):
            ...
    """
    if request.user.is_authenticated:
        return f'user:{request.user.id}'
    return f'ip:{request.META.get("REMOTE_ADDR", "unknown")}'


# Pre-configured rate limit decorators for common use cases

def rate_limit_strict(view_func):
    """
    Strict rate limiting for sensitive operations (10 requests per minute).
    """
    return api_ratelimit(key=get_user_or_ip, rate='10/m', method='ALL')(view_func)


def rate_limit_auth(view_func):
    """
    Rate limiting for authentication endpoints (5 requests per minute).
    """
    return api_ratelimit(key='ip', rate='5/m', method='POST')(view_func)


def rate_limit_api(view_func):
    """
    Standard rate limiting for API endpoints (100 requests per hour).
    """
    return api_ratelimit(key=get_user_or_ip, rate='100/h', method='ALL')(view_func)


def rate_limit_read(view_func):
    """
    Rate limiting for read operations (200 requests per hour).
    """
    return api_ratelimit(key=get_user_or_ip, rate='200/h', method='GET')(view_func)


def rate_limit_write(view_func):
    """
    Rate limiting for write operations (50 requests per hour).
    """
    return api_ratelimit(key=get_user_or_ip, rate='50/h', method=['POST', 'PUT', 'PATCH', 'DELETE'])(view_func)
