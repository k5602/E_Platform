#!/bin/bash

# E_Platform Nginx Deployment Script
# This script sets up Nginx as a reverse proxy for E_Platform

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (sudo bash deploy_complete.sh)"
    exit 1
fi

# Variables - adjust these to match your setup
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
NGINX_MAIN_CONF="/etc/nginx/nginx.conf"
LOG_DIR="/var/log/eplatform"
DOMAIN="localhost"  # Change this to your domain or IP

echo "E_Platform Nginx Deployment Script"
echo "=================================="
echo ""
echo "This script will set up Nginx as a reverse proxy for E_Platform."
echo "It will configure Nginx to route HTTP and WebSocket traffic to the appropriate services."
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Domain: $DOMAIN"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Install required packages
echo "Installing required packages..."
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    apt-get update
    apt-get install -y nginx redis-server
elif command -v pacman &> /dev/null; then
    # Arch Linux
    pacman -Sy --noconfirm nginx redis
elif command -v dnf &> /dev/null; then
    # Fedora/RHEL
    dnf install -y nginx redis
else
    echo "Unsupported package manager. Please install Nginx and Redis manually."
    exit 1
fi

# Create directories if they don't exist
echo "Creating necessary directories..."
mkdir -p "$NGINX_CONF_DIR"
mkdir -p "$NGINX_ENABLED_DIR"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"
chown http:http "$LOG_DIR"

# Copy Nginx configuration
echo "Copying Nginx configuration..."
cp "$PROJECT_DIR/nginx/nginx.conf" "$NGINX_MAIN_CONF"
cp "$PROJECT_DIR/nginx/eplatform_complete.conf" "$NGINX_CONF_DIR/eplatform.conf"

# Update domain in configuration
echo "Updating domain in configuration..."
sed -i "s/server_name localhost;/server_name $DOMAIN;/g" "$NGINX_CONF_DIR/eplatform.conf"

# Create symbolic link to enable the site
echo "Enabling site..."
ln -sf "$NGINX_CONF_DIR/eplatform.conf" "$NGINX_ENABLED_DIR/eplatform.conf"

# Copy systemd service files
echo "Copying systemd service files..."
cp "$PROJECT_DIR/nginx/eplatform-django-service.conf" /etc/systemd/system/eplatform-django.service
cp "$PROJECT_DIR/nginx/eplatform-daphne-service.conf" /etc/systemd/system/eplatform-daphne.service

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start Redis (required for Django Channels)
echo "Enabling and starting Redis..."
systemctl enable redis
systemctl restart redis

# Enable and start services
echo "Enabling and starting services..."
systemctl enable eplatform-django.service
systemctl enable eplatform-daphne.service
systemctl restart eplatform-django.service
systemctl restart eplatform-daphne.service

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Restart Nginx
echo "Restarting Nginx..."
systemctl restart nginx

echo ""
echo "Deployment complete!"
echo "Your E_Platform should now be accessible at http://$DOMAIN"
echo ""
echo "To test the setup, run: bash $PROJECT_DIR/nginx/test_complete.sh"
echo ""
echo "If you encounter any issues, check the troubleshooting guide in the README."
