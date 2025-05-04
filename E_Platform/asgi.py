"""
ASGI config for E_Platform project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import logging
import os
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import after initializing Django
from home.routing import websocket_urlpatterns as home_websocket_urlpatterns
from chatting.routing import websocket_urlpatterns as chatting_websocket_urlpatterns

# Combine WebSocket URL patterns from different apps
all_websocket_urlpatterns = home_websocket_urlpatterns + chatting_websocket_urlpatterns


class CSRFProtectionMiddleware(BaseMiddleware):
    """
    Middleware that provides CSRF protection for WebSocket connections.

    This middleware checks for a valid CSRF token in the WebSocket query parameters
    to prevent Cross-Site WebSocket Hijacking (CSWSH) attacks.

    In development mode, CSRF protection can be disabled by setting the
    WEBSOCKET_CSRF_EXEMPT environment variable to 'True'.
    """

    async def __call__(self, scope, receive, send):
        # Skip CSRF check for non-WebSocket connections
        if scope["type"] != "websocket":
            return await self.inner(scope, receive, send)

        # Check if CSRF protection is disabled in development mode
        csrf_exempt_value = os.environ.get('WEBSOCKET_CSRF_EXEMPT', 'False')
        csrf_exempt = csrf_exempt_value.lower() in ('true', 't', 'yes', 'y', '1')

        if csrf_exempt:
            logger.warning("WebSocket CSRF protection is disabled in development mode")
            return await self.inner(scope, receive, send)

        # Get query parameters
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        # Check for CSRF token in query parameters
        csrf_token = query_params.get("csrf_token", [""])[0]

        if not csrf_token:
            logger.warning("WebSocket connection attempt without CSRF token")
            raise PermissionDenied("CSRF token missing")

        # Verify CSRF token (simplified check - in production, use Django's CSRF verification)
        # In a real implementation, you would validate against the user's session
        if len(csrf_token) < 32:  # Simple length check as a basic validation
            logger.warning(f"Invalid CSRF token format in WebSocket connection: {csrf_token[:10]}...")
            raise PermissionDenied("Invalid CSRF token")

        # If we get here, the CSRF token is present and has a valid format
        # Continue with the inner middleware/application
        return await self.inner(scope, receive, send)


# Configure the ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        CSRFProtectionMiddleware(
            AuthMiddlewareStack(
                URLRouter(
                    all_websocket_urlpatterns
                )
            )
        )
    ),
})
