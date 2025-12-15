"""
Security middleware for the application.
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class HTTPSRedirectMiddleware(MiddlewareMixin):
    """
    Middleware to redirect all HTTP requests to HTTPS in production.
    Only active when DEBUG=False and ENFORCE_HTTPS=True.
    """
    
    def process_request(self, request):
        """
        Redirect HTTP requests to HTTPS if not in debug mode.
        """
        # Skip if in debug mode or HTTPS enforcement is disabled
        if settings.DEBUG or not getattr(settings, 'ENFORCE_HTTPS', False):
            return None
        
        # Skip if already using HTTPS
        if request.is_secure():
            return None
        
        # Skip for health check endpoints
        if request.path in ['/health/', '/api/health/']:
            return None
        
        # Redirect to HTTPS
        url = request.build_absolute_uri(request.get_full_path())
        secure_url = url.replace('http://', 'https://', 1)
        return HttpResponsePermanentRedirect(secure_url)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """
    
    def process_response(self, request, response):
        """
        Add security headers to response.
        """
        # Prevent clickjacking
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (basic policy)
        if not settings.DEBUG:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://checkout.razorpay.com",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "img-src 'self' data: https:",
                "font-src 'self' https://cdn.jsdelivr.net",
                "connect-src 'self' https://api.razorpay.com",
                "frame-src https://api.razorpay.com",
            ]
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Strict Transport Security (only in production with HTTPS)
        if not settings.DEBUG and request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
