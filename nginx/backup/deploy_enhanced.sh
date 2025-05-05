#!/bin/bash
# E_Platform Enhanced Nginx Deployment Script
# This script sets up Nginx as a reverse proxy for E_Platform

# Exit on error
set -e

# Print colored messages
print_info() {
    echo -e "\e[1;34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1"
}

print_warning() {
    echo -e "\e[1;33m[WARNING]\e[0m $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Define paths
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
LOG_DIR="/var/log/eplatform"

# Create directories if they don't exist
print_info "Creating required directories..."
mkdir -p "$NGINX_CONF_DIR"
mkdir -p "$NGINX_ENABLED_DIR"
mkdir -p "$LOG_DIR"

# Set permissions for log directory
chown -R zero:zero "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Install required packages
print_info "Checking and installing required packages..."
if command -v pacman &> /dev/null; then
    # Arch Linux
    pacman -Sy --noconfirm nginx redis
elif command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    apt-get update
    apt-get install -y nginx redis-server
elif command -v dnf &> /dev/null; then
    # Fedora/RHEL
    dnf install -y nginx redis
else
    print_warning "Could not determine package manager. Please install Nginx and Redis manually."
fi

# Copy Nginx configuration files
print_info "Copying Nginx configuration files..."
cp "$PROJECT_DIR/nginx/nginx.conf" /etc/nginx/nginx.conf
cp "$PROJECT_DIR/nginx/eplatform_enhanced.conf" "$NGINX_CONF_DIR/eplatform.conf"

# Create symbolic link to enable the site
print_info "Enabling site..."
ln -sf "$NGINX_CONF_DIR/eplatform.conf" "$NGINX_ENABLED_DIR/eplatform.conf"

# Copy systemd service files
print_info "Copying systemd service files..."
cp "$PROJECT_DIR/nginx/eplatform-django-enhanced.service" /etc/systemd/system/eplatform-django.service
cp "$PROJECT_DIR/nginx/eplatform-daphne-enhanced.service" /etc/systemd/system/eplatform-daphne.service

# Reload systemd
print_info "Reloading systemd..."
systemctl daemon-reload

# Enable and start Redis (required for Django Channels)
print_info "Enabling and starting Redis..."
systemctl enable redis
systemctl restart redis

# Enable and start services
print_info "Enabling and starting services..."
systemctl enable eplatform-django.service
systemctl enable eplatform-daphne.service
systemctl restart eplatform-django.service
systemctl restart eplatform-daphne.service

# Test Nginx configuration
print_info "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    # Enable and start Nginx
    print_info "Enabling and starting Nginx..."
    systemctl enable nginx
    systemctl restart nginx

    print_success "Deployment completed successfully!"
    print_info "Your E_Platform should now be accessible at http://your_domain.com"
    print_info "To test the setup, run: bash $PROJECT_DIR/nginx/test_enhanced.sh"
else
    print_error "Nginx configuration test failed. Please check the error messages above."
    exit 1
fi

# Final instructions
print_info "Next steps:"
print_info "1. Update the server_name directive in /etc/nginx/sites-available/eplatform.conf with your domain"
print_info "2. For HTTPS, uncomment the SSL section in the configuration file"
print_info "3. Consider setting up Let's Encrypt for free SSL certificates"
print_info "4. Check the logs if you encounter any issues: $LOG_DIR/"

exit 0
