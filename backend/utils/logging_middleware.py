"""
Logging Middleware

Provides middleware for enhanced logging capabilities including:
- Slow query detection and logging
- Request/response body logging (for debugging)
- Performance monitoring
"""

import logging
import time
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
slow_query_logger = logging.getLogger('django.db.backends')


class SlowQueryLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log slow database queries.
    
    Logs queries that exceed the SLOW_QUERY_THRESHOLD setting.
    Only active when ENABLE_QUERY_LOGGING is True.
    """
    
    def process_request(self, request):
        """
        Reset query tracking at the start of each request.
        """
        if settings.ENABLE_QUERY_LOGGING:
            # Reset queries for this request
            connection.queries_log.clear()
        return None
    
    def process_response(self, request, response):
        """
        Log slow queries after the response is generated.
        """
        if not settings.ENABLE_QUERY_LOGGING:
            return response
        
        # Get all queries executed during this request
        queries = connection.queries
        
        if not queries:
            return response
        
        # Calculate total query time
        total_time = sum(float(q.get('time', 0)) for q in queries)
        
        # Log slow queries
        slow_queries = []
        for query in queries:
            query_time = float(query.get('time', 0))
            if query_time >= settings.SLOW_QUERY_THRESHOLD:
                slow_queries.append({
                    'sql': query.get('sql', ''),
                    'time': query_time
                })
        
        if slow_queries:
            slow_query_logger.warning(
                f"Slow queries detected on {request.method} {request.path} | "
                f"Total queries: {len(queries)} | "
                f"Total time: {total_time:.3f}s | "
                f"Slow queries: {len(slow_queries)}"
            )
            
            for idx, sq in enumerate(slow_queries, 1):
                slow_query_logger.warning(
                    f"Slow Query #{idx} ({sq['time']:.3f}s): {sq['sql'][:500]}"
                )
        
        # Log if too many queries (N+1 problem indicator)
        if len(queries) > 50:
            slow_query_logger.warning(
                f"High query count on {request.method} {request.path}: "
                f"{len(queries)} queries in {total_time:.3f}s"
            )
        
        return response


class DetailedRequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for detailed request/response logging.
    
    Logs request and response details for debugging purposes.
    Only active in DEBUG mode or when explicitly enabled.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('apps.users')
        from decouple import config
        self.enabled = settings.DEBUG or config('DETAILED_REQUEST_LOGGING', default=False, cast=bool)
    
    def process_request(self, request):
        """
        Log detailed request information.
        """
        if not self.enabled:
            return None
        
        # Log request details
        log_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'content_type': request.content_type,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        }
        
        # Log user info if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_data['user'] = f"{request.user.email} ({request.user.user_type})"
        
        self.logger.debug(f"Request details: {log_data}")
        
        return None
    
    def process_response(self, request, response):
        """
        Log detailed response information.
        """
        if not self.enabled:
            return response
        
        # Log response details
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'content_type': response.get('Content-Type', 'Unknown'),
        }
        
        self.logger.debug(f"Response details: {log_data}")
        
        return response


class SecurityEventLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log security-related events.
    
    Logs:
    - Failed authentication attempts
    - Permission denied events
    - CSRF failures
    - Suspicious activity
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.security')
    
    def process_response(self, request, response):
        """
        Log security events based on response status.
        """
        # Log authentication failures (401)
        if response.status_code == 401:
            self.logger.warning(
                f"Authentication failed: {request.method} {request.path} | "
                f"IP: {self._get_client_ip(request)} | "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
            )
        
        # Log permission denied (403)
        elif response.status_code == 403:
            user_info = 'Anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"{request.user.email} ({request.user.user_type})"
            
            self.logger.warning(
                f"Permission denied: {request.method} {request.path} | "
                f"User: {user_info} | "
                f"IP: {self._get_client_ip(request)}"
            )
        
        return response
    
    def process_exception(self, request, exception):
        """
        Log security-related exceptions.
        """
        # Log CSRF failures
        if exception.__class__.__name__ == 'PermissionDenied':
            self.logger.warning(
                f"Permission denied exception: {request.method} {request.path} | "
                f"Exception: {str(exception)} | "
                f"IP: {self._get_client_ip(request)}"
            )
        
        return None
    
    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
