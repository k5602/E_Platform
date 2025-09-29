import hashlib
import time
import logging

from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class LoginRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to rate limit login attempts based on IP address.
    This helps prevent brute force attacks on the login page.
    """

    # Maximum number of login attempts within the time window
    MAX_LOGIN_ATTEMPTS = 5

    # Time window in seconds (5 minutes)
    RATE_LIMIT_WINDOW = 300

    def process_request(self, request):
        """
        Process each request to check if it's a login attempt and if it should be rate limited.
        """
        # Only apply rate limiting to the login URL
        if request.path == '/authentication/login/' and request.method == 'POST':
            # Check if cache is available
            if not hasattr(cache, 'get') or not hasattr(cache, 'set'):
                logger.warning("Cache not available for login rate limiting")
                return

            try:
                # Get client IP address
                ip = self._get_client_ip(request)

                # Create a cache key based on the IP address
                cache_key = f"login_attempts_{self._get_ip_hash(ip)}"

                # Get current login attempts from cache
                login_attempts = cache.get(cache_key, [])

                # Remove attempts outside the time window
                current_time = time.time()
                login_attempts = [attempt for attempt in login_attempts
                                  if current_time - attempt < self.RATE_LIMIT_WINDOW]

                # Check if the number of attempts exceeds the limit
                if len(login_attempts) >= self.MAX_LOGIN_ATTEMPTS:
                    return HttpResponseForbidden(
                        "Too many login attempts. Please try again later."
                    )

                # Add the current attempt
                login_attempts.append(current_time)

                # Update the cache
                cache.set(cache_key, login_attempts, self.RATE_LIMIT_WINDOW)
            except Exception as e:
                # If cache operations fail, log and continue without rate limiting
                logger.error(f"Error in login rate limiting: {e}")
                return

    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_ip_hash(self, ip):
        """
        Create a hash of the IP address to avoid storing raw IP addresses.
        """
        return hashlib.sha256(ip.encode()).hexdigest()
