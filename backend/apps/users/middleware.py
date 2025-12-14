import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('apps.users')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and their responses.
    Logs request method, path, user, status code, and response time.
    """
    
    def process_request(self, request):
        """
        Called on each request before Django decides which view to execute.
        """
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """
        Called on each response before it's returned to the client.
        """
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Get user info
            user_info = 'Anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"{request.user.email} ({request.user.user_type})"
            
            # Log the request
            log_data = {
                'method': request.method,
                'path': request.path,
                'user': user_info,
                'status': response.status_code,
                'duration': f"{duration:.3f}s"
            }
            
            # Use different log levels based on status code
            if response.status_code >= 500:
                logger.error(f"Request: {log_data}")
            elif response.status_code >= 400:
                logger.warning(f"Request: {log_data}")
            else:
                logger.info(f"Request: {log_data}")
        
        return response
