# WebSocket CSRF Protection

## Overview

This document explains the Cross-Site Request Forgery (CSRF) protection implemented for WebSocket connections in the
E-Platform project.

## The Issue

WebSocket connections in the E-Platform project are protected against Cross-Site WebSocket Hijacking (CSWSH) attacks
using CSRF tokens. This protection is implemented in the `CSRFProtectionMiddleware` in `E_Platform/asgi.py`.

The middleware requires a valid CSRF token to be included in the WebSocket connection's query parameters. If the token
is missing or invalid, the connection is rejected with a "CSRF token missing" error.

```
django.core.exceptions.PermissionDenied: CSRF token missing
```

## Frontend Implementation

The frontend JavaScript code in `static/home/js/websocket-notifications.js` attempts to include the CSRF token in the
WebSocket connection URL:

```javascript
// Get CSRF token from cookie or Django's csrftoken input
function getCSRFToken() {
    // Try to get from cookie first
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

    if (cookieValue) {
        return cookieValue;
    }

    // If not in cookie, try to get from hidden input
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }

    console.error('CSRF token not found. WebSocket connection may fail.');
    return '';
}

// Add CSRF token to WebSocket URL as a query parameter
const csrfToken = getCSRFToken();
const wsUrl = `${wsProtocol}//${wsHost}/ws/notifications/${userId}/?csrf_token=${csrfToken}`;
```

However, in some development environments or certain browser configurations, the CSRF token might not be properly
retrieved or passed to the server.

## Solution

To facilitate development, we've added an environment variable-based bypass for CSRF protection in development mode. The
middleware now checks for an environment variable called `WEBSOCKET_CSRF_EXEMPT`, and if it's set to `true`, it will
skip the CSRF token validation for WebSocket connections.

```python
# Check if CSRF protection is disabled in development mode
csrf_exempt = os.environ.get('WEBSOCKET_CSRF_EXEMPT', 'False').lower() == 'true'

if csrf_exempt:
    logger.warning("WebSocket CSRF protection is disabled in development mode")
    return await self.inner(scope, receive, send)
```

## Usage

### Development Mode

For development, you can disable WebSocket CSRF protection by setting the `WEBSOCKET_CSRF_EXEMPT` environment variable
to `true`:

```bash
export WEBSOCKET_CSRF_EXEMPT=true
python manage.py runserver
```

Or use the provided script:

```bash
./run_with_websocket_csrf_exempt.sh
```

### Production Mode

In production, CSRF protection should always be enabled to prevent CSWSH attacks. Make sure the `WEBSOCKET_CSRF_EXEMPT`
environment variable is not set or is set to `false`.

## Security Considerations

- **Development Only**: The CSRF exemption should only be used in development environments, never in production.
- **Production Security**: In production, ensure that WebSocket connections include valid CSRF tokens.
- **Alternative Approaches**: If you're experiencing issues with CSRF tokens in production, consider:
    - Debugging the frontend code to ensure CSRF tokens are properly retrieved and passed
    - Implementing a more robust CSRF token validation mechanism
    - Using other security measures like origin validation and authentication

## Further Improvements

Future improvements to the WebSocket CSRF protection could include:

1. Path-based exemptions (exempt specific WebSocket paths)
2. More robust CSRF token validation (using Django's built-in CSRF validation)
3. Better error messages and debugging information