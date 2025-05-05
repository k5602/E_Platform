#!/bin/bash

# Deploy Nginx configuration for E_Platform
# This script helps set up the Nginx reverse proxy for your Django-Daphne application

# Exit on error
set -e

echo "E_Platform Nginx Deployment Script"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo"
  exit 1
fi

# Variables - adjust these to match your setup
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
DOMAIN="your_domain.com"  # Replace with your domain or IP

# Create directories if they don't exist
mkdir -p "$NGINX_CONF_DIR"
mkdir -p "$NGINX_ENABLED_DIR"

# Copy Nginx configuration
echo "Copying Nginx configuration..."
cp "$PROJECT_DIR/nginx/eplatform.conf" "$NGINX_CONF_DIR/eplatform.conf"

# Update domain in configuration
echo "Updating domain in configuration..."
sed -i "s/your_domain.com/$DOMAIN/g" "$NGINX_CONF_DIR/eplatform.conf"

# Create symbolic link to enable the site
echo "Enabling site..."
ln -sf "$NGINX_CONF_DIR/eplatform.conf" "$NGINX_ENABLED_DIR/eplatform.conf"

# Copy systemd service files
echo "Copying systemd service files..."
cp "$PROJECT_DIR/nginx/eplatform-django.service" /etc/systemd/system/
cp "$PROJECT_DIR/nginx/eplatform-daphne.service" /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start services
echo "Enabling and starting services..."
systemctl enable eplatform-django.service
systemctl enable eplatform-daphne.service
systemctl start eplatform-django.service
systemctl start eplatform-daphne.service

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

echo "Deployment complete!"
echo "Your E_Platform should now be accessible at http://$DOMAIN"
echo ""
echo "Next steps:"
echo "1. Configure SSL/TLS for secure connections"
echo "2. Test your WebSocket connections"
echo "3. Monitor logs for any issues"
echo ""
echo "Logs can be found at:"
echo "- Nginx: /var/log/nginx/eplatform_*.log"
echo "- Django: Check your Django logging configuration"
echo "- Daphne: Check your Daphne logging configuration"
