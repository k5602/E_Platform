# E_Platform Enhanced Nginx Reverse Proxy Setup

This directory contains configuration files and scripts for setting up Nginx as a reverse proxy for the E_Platform application, replacing the dual server architecture (Django-Daphne) with a unified entry point.

## Features

- **Single Entry Point**: All traffic (HTTP and WebSocket) goes through Nginx
- **Path-Based Routing**: Routes traffic to appropriate backend services based on URL paths
- **Protocol Handling**: Properly handles both HTTP and WebSocket protocols
- **Security Hardening**: Includes security headers, rate limiting, and other protections
- **Performance Optimization**: Caching, compression, and other performance enhancements
- **SSL/HTTPS Support**: Ready-to-use HTTPS configuration (requires certificates)
- **Detailed Logging**: Comprehensive logging for troubleshooting
- **Health Checks**: Endpoint for monitoring system health

## Files

- `eplatform_enhanced.conf` - Enhanced Nginx server configuration with detailed comments
- `nginx.conf` - Global Nginx settings
- `eplatform-django-enhanced.service` - Systemd service for Django (using Gunicorn)
- `eplatform-daphne-enhanced.service` - Systemd service for Daphne (WebSockets)
- `deploy_enhanced.sh` - Deployment script
- `test_enhanced.sh` - Testing script
- `INSTALLATION.md` - Detailed installation guide
- `TROUBLESHOOTING.md` - Comprehensive troubleshooting guide

## Architecture

```
                   ┌─────────────────────┐
                   │                     │
 Client Request    │                     │
─────────────────► │       NGINX        │
                   │                     │
                   │                     │
                   └─────────┬───────────┘
                             │
                             │
                             ▼
          ┌─────────────────────────────────┐
          │                                 │
          ▼                                 ▼
┌─────────────────────┐         ┌─────────────────────┐
│                     │         │                     │
│  Django (Gunicorn)  │         │  Daphne (WebSocket) │
│    127.0.0.1:8000   │         │    127.0.0.1:8001   │
│                     │         │                     │
└─────────────────────┘         └─────────────────────┘
          │                                 │
          │                                 │
          ▼                                 ▼
┌─────────────────────┐         ┌─────────────────────┐
│                     │         │                     │
│     PostgreSQL      │         │        Redis        │
│                     │         │                     │
└─────────────────────┘         └─────────────────────┘
```

## Setup Instructions

### Quick Setup

For a quick setup, use the provided deployment script:

```bash
# Make the script executable
chmod +x nginx/deploy_enhanced.sh

# Run the deployment script as root
sudo bash nginx/deploy_enhanced.sh
```

### Testing the Setup

After deployment, test your setup:

```bash
# Make the script executable
chmod +x nginx/test_enhanced.sh

# Run the test script
bash nginx/test_enhanced.sh
```

### Manual Setup

For detailed manual setup instructions, see [INSTALLATION.md](INSTALLATION.md).

## URL Routing

The Nginx configuration routes traffic based on URL paths:

- `/static/*` → Served directly by Nginx from staticfiles directory
- `/media/*` → Served directly by Nginx from media directory
- `/ws/*` → Routed to Daphne (WebSocket server) on port 8001
- `/api/*` → Routed to Django (Gunicorn) on port 8000 with API-specific optimizations
- `/admin/*` → Routed to Django with additional security measures
- All other paths → Routed to Django

## Security Features

The enhanced configuration includes several security features:

- **HTTP Security Headers**: XSS protection, content type options, frame options
- **Rate Limiting**: Prevents abuse of API and admin endpoints
- **SSL/HTTPS Support**: Ready for secure HTTPS connections
- **Content Security Policy**: Restricts resource loading to prevent XSS
- **IP Restrictions**: Optional IP-based access control for admin area
- **File Access Protection**: Prevents access to hidden files
- **Request Timeouts**: Configurable timeouts for different types of requests

## Performance Optimizations

- **Static File Caching**: Long cache times for static assets
- **Gzip Compression**: Reduces bandwidth usage
- **Buffer Optimizations**: Tuned buffer sizes for different content types
- **Connection Handling**: Optimized for both short and long-lived connections
- **Worker Process Management**: Automatically scales based on CPU cores

## Troubleshooting

If you encounter issues, refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting steps.

## Customization

To customize the configuration for your specific needs:

1. Edit `eplatform_enhanced.conf` to change server settings
2. Modify service files to adjust worker counts, timeouts, etc.
3. Update environment variables in service files for database connections

## Production Considerations

Before deploying to production:

1. Replace `your_domain.com` with your actual domain name
2. Set up SSL certificates (Let's Encrypt recommended)
3. Enable HTTPS and configure redirects
4. Review and adjust rate limits based on expected traffic
5. Set Django's `DEBUG = False` in production settings
6. Secure database credentials and sensitive information
7. Set up regular backups
8. Configure log rotation

## Maintenance

Regular maintenance tasks:

1. Keep Nginx and all dependencies updated
2. Monitor log files for errors
3. Check for security advisories
4. Rotate logs to prevent disk space issues
5. Periodically test the setup with the test script
