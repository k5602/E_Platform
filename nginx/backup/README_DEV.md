# E_Platform Development Nginx Setup

This guide explains how to set up Nginx as a reverse proxy for E_Platform in development mode.

## Overview

The development configuration:
- Uses HTTP only (no HTTPS)
- Routes traffic based on URL paths
- Provides a single entry point for both HTTP and WebSocket connections
- Includes basic security headers and optimizations
- Simplifies local development

## Files

- `eplatform_dev.conf` - Nginx configuration for development
- `deploy_dev.sh` - Deployment script for development
- `nginx.conf` - Global Nginx settings
- `eplatform-django-enhanced.service` - Systemd service for Django
- `eplatform-daphne-enhanced.service` - Systemd service for Daphne

## Quick Setup

1. Make the deployment script executable:
   ```bash
   chmod +x nginx/deploy_dev.sh
   ```

2. Run the deployment script as root:
   ```bash
   sudo bash nginx/deploy_dev.sh
   ```

3. Access your application at:
   ```
   http://localhost
   ```

## Manual Setup

If you prefer to set up manually:

1. Install Nginx and Redis:
   ```bash
   # Arch Linux
   sudo pacman -S nginx redis
   
   # Ubuntu/Debian
   sudo apt install nginx redis-server
   
   # Fedora/RHEL
   sudo dnf install nginx redis
   ```

2. Create required directories:
   ```bash
   sudo mkdir -p /etc/nginx/sites-available
   sudo mkdir -p /etc/nginx/sites-enabled
   sudo mkdir -p /var/log/eplatform
   ```

3. Set permissions:
   ```bash
   sudo chown -R zero:zero /var/log/eplatform
   sudo chmod 755 /var/log/eplatform
   ```

4. Copy configuration files:
   ```bash
   sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
   sudo cp nginx/eplatform_dev.conf /etc/nginx/sites-available/eplatform.conf
   sudo ln -sf /etc/nginx/sites-available/eplatform.conf /etc/nginx/sites-enabled/eplatform.conf
   ```

5. Set up systemd services:
   ```bash
   sudo cp nginx/eplatform-django-enhanced.service /etc/systemd/system/eplatform-django.service
   sudo cp nginx/eplatform-daphne-enhanced.service /etc/systemd/system/eplatform-daphne.service
   sudo systemctl daemon-reload
   ```

6. Start services:
   ```bash
   sudo systemctl enable redis
   sudo systemctl restart redis
   sudo systemctl enable eplatform-django.service
   sudo systemctl enable eplatform-daphne.service
   sudo systemctl restart eplatform-django.service
   sudo systemctl restart eplatform-daphne.service
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

## URL Routing

The Nginx configuration routes traffic based on URL paths:

- `/static/*` → Served directly by Nginx from staticfiles directory
- `/media/*` → Served directly by Nginx from media directory
- `/ws/*` → Routed to Daphne (WebSocket server) on port 8001
- `/api/*` → Routed to Django (Gunicorn) on port 8000 with API-specific optimizations
- `/admin/*` → Routed to Django with additional security measures
- All other paths → Routed to Django

## Troubleshooting

If you encounter issues:

1. Check service status:
   ```bash
   sudo systemctl status nginx
   sudo systemctl status eplatform-django
   sudo systemctl status eplatform-daphne
   sudo systemctl status redis
   ```

2. Check logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/eplatform_error.log
   sudo tail -f /var/log/eplatform/gunicorn-error.log
   sudo tail -f /var/log/eplatform/daphne-access.log
   ```

3. Test Nginx configuration:
   ```bash
   sudo nginx -t
   ```

4. Verify ports are open:
   ```bash
   sudo netstat -tulpn | grep -E ':(80|8000|8001|6379)'
   ```

## Moving to Production

When you're ready to move to production:

1. Set up SSL certificates (Let's Encrypt recommended)
2. Use the production configuration (`eplatform_enhanced.conf`)
3. Set Django's `DEBUG = False` in settings
4. Secure database credentials
5. Set up regular backups

For detailed production setup instructions, see `README_ENHANCED.md`.
