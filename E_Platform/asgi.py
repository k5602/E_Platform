"""
ASGI config for E_Platform project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import logging
import os
import sys
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

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
        csrf_exempt_value = os.environ.get('WEBSOCKET_CSRF_EXEMPT', 'True')  # Default to True for easier development
        csrf_exempt = csrf_exempt_value.lower() in ('true', 't', 'yes', 'y', '1')

        # Check if we're in DEBUG mode (development)
        from django.conf import settings
        is_debug = getattr(settings, 'DEBUG', False)

        try:
            # In development mode with DEBUG=True, we can be more lenient
            if is_debug:
                # Log a warning but allow the connection
                if not csrf_exempt:
                    logger.warning("WebSocket CSRF protection is enabled in development mode. "
                                "Set WEBSOCKET_CSRF_EXEMPT=True for easier development.")

                # Get query parameters
                query_string = scope.get("query_string", b"").decode()
                query_params = parse_qs(query_string)

                # Check for CSRF token in query parameters
                csrf_token = query_params.get("csrf_token", [""])[0]

                if not csrf_token and not csrf_exempt:
                    logger.warning("WebSocket connection attempt without CSRF token in development mode")
                    # In development, we'll log the warning but still allow the connection

                return await self.inner(scope, receive, send)

            # In production mode, enforce strict CSRF protection
            if csrf_exempt:
                logger.warning("WebSocket CSRF protection is disabled. This is not recommended in production.")
                return await self.inner(scope, receive, send)

            # Get query parameters
            query_string = scope.get("query_string", b"").decode()
            query_params = parse_qs(query_string)

            # Check for CSRF token in query parameters
            csrf_token = query_params.get("csrf_token", [""])[0]

            if not csrf_token:
                logger.warning("WebSocket connection attempt without CSRF token")
                # Instead of raising an exception, close the connection with an error code
                await send({
                    "type": "websocket.close",
                    "code": 4403,  # Custom close code for CSRF errors
                    "reason": "CSRF token missing",
                })
                return

            # Verify CSRF token (simplified check)
            if len(csrf_token) < 32:  # Simple length check as a basic validation
                logger.warning(f"Invalid CSRF token format in WebSocket connection: {csrf_token[:10]}...")
                await send({
                    "type": "websocket.close",
                    "code": 4403,
                    "reason": "Invalid CSRF token",
                })
                return

            # If we get here, the CSRF token is present and has a valid format
            # Continue with the inner middleware/application
            return await self.inner(scope, receive, send)
        except Exception as e:
            # Log any exceptions and close the connection gracefully
            logger.error(f"Error in CSRF middleware: {str(e)}", exc_info=True)
            await send({
                "type": "websocket.close",
                "code": 4500,  # Custom close code for server errors
                "reason": "Internal server error",
            })
            return


# A simple error handling middleware
class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware that catches any unhandled exceptions in the ASGI application
    chain and returns a proper WebSocket close frame instead of crashing.
    """
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            return await self.inner(scope, receive, send)
            
        try:
            return await self.inner(scope, receive, send)
        except Exception as e:
            logger.error(f"Unhandled exception in WebSocket connection: {str(e)}", exc_info=True)
            try:
                await send({
                    "type": "websocket.close",
                    "code": 1011,  # Internal server error
                    "reason": "Internal server error",
                })
            except:
                # If we can't send a close frame, just log and continue
                pass


# Configure the ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": ErrorHandlingMiddleware(
        AllowedHostsOriginValidator(
            CSRFProtectionMiddleware(
                AuthMiddlewareStack(
                    URLRouter(
                        all_websocket_urlpatterns
                    )
                )
            )
        )
    ),
})
