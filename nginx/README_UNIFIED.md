# E_Platform Unified Nginx Setup

This guide explains how to set up E_Platform with Nginx as a reverse proxy, replacing the dual server architecture (Django-Daphne) with a single entry point.

## Overview

### Previous Architecture

Previously, E_Platform used a dual-server architecture:
- Django server on port 8000 for HTTP requests
- Daphne server on port 8001 for WebSockets
- Client-side code had to handle connecting to different ports

### New Architecture

The new architecture uses Nginx as a reverse proxy:
- Nginx listens on port 80 (and optionally 443 for HTTPS)
- Nginx routes requests based on URL path:
  - `/ws/*` paths go to Daphne (WebSockets)
  - All other paths go to Django (HTTP)
- Client-side code connects to the same host for both HTTP and WebSockets

## Setup Instructions

### Prerequisites

- Arch Linux
- Nginx (`sudo pacman -S nginx`)
- Python virtual environment with Django, Daphne, and Gunicorn
- Redis server for Channels

### Development Setup

For development, you can use the provided script:

```bash
sudo bash run_with_nginx.sh
```

This script:
1. Sets up a temporary Nginx configuration
2. Starts Django on port 8000
3. Starts Daphne on port 8001
4. Configures Nginx to route traffic appropriately

### Production Setup

For production, follow these steps:

1. **Install required packages**

   ```bash
   sudo pacman -S nginx
   sudo systemctl enable nginx
   ```

2. **Deploy the configuration**

   ```bash
   sudo bash nginx/deploy_unified.sh
   ```

3. **Test the setup**

   ```bash
   sudo bash nginx/test_unified.sh
   ```

4. **Configure SSL (recommended)**

   Edit `nginx/eplatform_unified.conf` and uncomment the HTTPS server block.
   
   For Let's Encrypt certificates:
   
   ```bash
   sudo pacman -S certbot certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

## Configuration Files

### Main Files

- `nginx/eplatform_unified.conf`: Main Nginx server configuration
- `nginx/nginx.conf`: Global Nginx settings
- `nginx/eplatform-django.service`: Systemd service for Django (using Gunicorn)
- `nginx/eplatform-daphne.service`: Systemd service for Daphne

### Scripts

- `nginx/deploy_unified.sh`: Production deployment script
- `nginx/test_unified.sh`: Testing script
- `run_with_nginx.sh`: Development setup script

## Client-Side Changes

The client-side JavaScript has been updated to work with the unified setup:

- WebSocket connections now use the same host as HTTP connections
- No more port switching based on development/production environment
- Simplified connection logic

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**

   - Check Nginx error logs: `sudo tail -f /var/log/nginx/eplatform_error.log`
   - Verify Daphne is running: `systemctl status eplatform-daphne.service`
   - Check browser console for WebSocket errors

2. **Static Files Not Loading**

   - Check file permissions
   - Verify paths in Nginx configuration
   - Run `python manage.py collectstatic`

3. **502 Bad Gateway**

   - Check if backend services are running
   - Verify ports in Nginx configuration match service ports

### Logs

- Nginx: `/var/log/nginx/eplatform_*.log`
- Django (Gunicorn): `/var/log/eplatform/gunicorn-*.log`
- Daphne: `/var/log/eplatform/daphne-access.log`

## Performance Tuning

### Nginx Optimizations

- **Worker Processes**: Set `worker_processes` to match CPU cores
- **Worker Connections**: Increase `worker_connections` for high traffic
- **Keepalive**: Adjust `keepalive_timeout` based on traffic patterns
- **Gzip Compression**: Enable for text-based content types
- **Caching**: Add caching for static assets

### WebSocket Optimizations

- **Proxy Buffers**: Adjust `proxy_buffers` and `proxy_buffer_size`
- **Timeouts**: Set appropriate `proxy_read_timeout` values
- **Connection Pooling**: Enable keepalive connections

## Security Considerations

- **HTTPS**: Always use SSL/TLS in production
- **HTTP/2**: Enable for better performance (requires HTTPS)
- **Security Headers**: Add headers like HSTS, CSP, etc.
- **Rate Limiting**: Implement for sensitive endpoints
- **Access Control**: Restrict access to admin areas

## Maintenance

- Regularly check logs for errors
- Update SSL certificates before they expire
- Monitor resource usage and adjust configuration as needed
