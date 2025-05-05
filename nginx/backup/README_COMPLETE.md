# E_Platform Nginx Reverse Proxy Implementation

This directory contains a comprehensive implementation for replacing the dual server architecture (Django-Daphne) with Nginx as a reverse proxy for E_Platform.

## Overview

The implementation provides:

1. A complete Nginx configuration for routing traffic based on URL paths and protocols
2. Systemd service files for running Django and Daphne as background services
3. Deployment and testing scripts
4. Detailed installation and troubleshooting guides

## Key Features

- **Single Entry Point**: All traffic (HTTP and WebSockets) goes through Nginx
- **Path-Based Routing**: Routes requests to appropriate backend services based on URL paths
- **Protocol Handling**: Properly handles both HTTP and WebSocket protocols
- **SSL/HTTPS Support**: Configuration for secure HTTPS connections
- **Performance Optimizations**: Caching, compression, and other performance enhancements
- **Security Hardening**: Rate limiting, security headers, and other security measures

## Files

- `eplatform_complete.conf`: Main Nginx server configuration with detailed comments
- `eplatform-django-service.conf`: Systemd service for Django (using Gunicorn)
- `eplatform-daphne-service.conf`: Systemd service for Daphne
- `deploy_complete.sh`: Comprehensive deployment script
- `test_complete.sh`: Testing script to verify the setup
- `INSTALLATION.md`: Detailed installation guide
- `TROUBLESHOOTING.md`: Comprehensive troubleshooting guide

## Architecture

```
                   ┌─────────────────┐
                   │                 │
 ┌─────────────┐   │                 │   ┌─────────────────┐
 │             │   │                 │   │                 │
 │  Clients    ├───►     Nginx      ├───►  Django (8000)  │
 │             │   │  Reverse Proxy  │   │                 │
 └─────────────┘   │                 │   └─────────────────┘
                   │                 │
                   │                 │   ┌─────────────────┐
                   │                 │   │                 │
                   └────────┬────────┘   │  Daphne (8001)  │
                            │            │                 │
                            │            └────────┬────────┘
                            │                     │
                            │                     │
                            │    ┌────────────────▼─┐
                            │    │                  │
                            └────►      Redis       │
                                 │                  │
                                 └──────────────────┘
```

## Traffic Routing

- **HTTP Requests** (`/`): Routed to Django (port 8000)
- **WebSocket Connections** (`/ws/`): Routed to Daphne (port 8001)
- **Static Files** (`/static/`): Served directly by Nginx
- **Media Files** (`/media/`): Served directly by Nginx
- **API Endpoints** (`/api/`): Routed to Django with specific optimizations
- **Admin Interface** (`/admin/`): Routed to Django with additional security

## Installation

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

Quick start:

```bash
# Deploy using the automated script
sudo bash deploy_complete.sh

# Test the setup
bash test_complete.sh
```

## Troubleshooting

For troubleshooting common issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Security Considerations

This implementation includes several security enhancements:

1. **Rate Limiting**: Prevents brute force attacks and DoS attempts
2. **Security Headers**: Adds headers to prevent XSS, clickjacking, and other attacks
3. **SSL Configuration**: Secure TLS settings for HTTPS (when enabled)
4. **Connection Timeouts**: Appropriate timeout settings to prevent resource exhaustion
5. **Error Handling**: Custom error pages and logging

## Performance Optimizations

The configuration includes several performance optimizations:

1. **Gzip Compression**: Reduces bandwidth usage and improves load times
2. **Caching**: Static files are cached with appropriate headers
3. **Connection Pooling**: Keeps connections open for better performance
4. **Buffer Tuning**: Optimized buffer settings for different types of content
5. **Worker Process Management**: Efficient handling of concurrent connections

## Customization

You may need to customize the configuration for your specific environment:

1. Update paths in the configuration files to match your installation
2. Adjust worker processes and connection limits based on your server resources
3. Configure SSL certificates for HTTPS
4. Modify rate limiting settings based on your traffic patterns

## Support

If you encounter any issues with this implementation, please:

1. Check the troubleshooting guide first
2. Review the Nginx and systemd logs for specific errors
3. Consult the Nginx, Django, and Daphne documentation for more information
