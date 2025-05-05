#!/bin/bash
# Script to fix the remaining issues with the Nginx setup

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

print_header() {
    echo -e "\n\e[1;36m=== $1 ===\e[0m"
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

print_header "CHECKING NGINX CONFIGURATION"

# Check if there are multiple configurations enabled
print_info "Checking for multiple enabled configurations..."
enabled_configs=$(ls -1 "$NGINX_ENABLED_DIR" | wc -l)

if [ "$enabled_configs" -gt 1 ]; then
    print_warning "Multiple configurations found in $NGINX_ENABLED_DIR"
    print_info "Removing all configurations except eplatform.conf..."
    
    for config in "$NGINX_ENABLED_DIR"/*; do
        if [ "$(basename "$config")" != "eplatform.conf" ]; then
            print_info "Removing $config"
            rm -f "$config"
        fi
    done
fi

print_header "UPDATING NGINX CONFIGURATION"

# Create conf.d directory if it doesn't exist
print_info "Creating conf.d directory if it doesn't exist..."
mkdir -p /etc/nginx/conf.d

# Update the main configuration file
print_info "Updating main Nginx configuration..."

cat > /etc/nginx/nginx.conf << 'EOF'
# Nginx Configuration for E_Platform
# This configuration file replaces the dual server system with Nginx as a reverse proxy

# User and worker processes
user zero;
worker_processes auto;  # Automatically determine based on CPU cores
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

# Events configuration
events {
    worker_connections 1024;  # Maximum number of simultaneous connections per worker
    multi_accept on;          # Accept as many connections as possible
}

# HTTP configuration
http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 4096;
    types_hash_bucket_size 128;
    server_tokens off;  # Don't show Nginx version in error pages and headers

    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging settings
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;  # API rate limiting
    limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/s;  # Admin rate limiting

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";

    # Include server configurations
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Update the site configuration
print_info "Updating site configuration..."

cat > "$NGINX_CONF_DIR/eplatform.conf" << 'EOF'
# E_Platform Development Nginx Server Configuration
# This configuration serves as a reverse proxy for the Django and Daphne servers

# HTTP Server Block
server {
    # Basic server configuration
    listen 80 default_server;          # Listen on port 80 for HTTP as default server
    server_name localhost;             # Using localhost for local development
    
    # Access and error logs
    access_log /var/log/nginx/eplatform_access.log;
    error_log /var/log/nginx/eplatform_error.log warn;
    
    # Maximum upload size
    client_max_body_size 20M;
    
    # Security headers for HTTP
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Static files - served directly by Nginx for better performance
    location /static/ {
        alias /mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        access_log off;
        
        # Protect against directory listing
        autoindex off;
        
        # Optimize file serving
        sendfile on;
        tcp_nopush on;
    }
    
    # Media files - served directly by Nginx
    location /media/ {
        alias /mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        access_log off;
        
        # Protect against directory listing
        autoindex off;
        
        # Optimize file serving
        sendfile on;
        tcp_nopush on;
    }
    
    # WebSocket connections - route to Daphne
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;  # Timeout for WebSocket connections (24h)
        
        # WebSocket specific optimizations
        proxy_buffers 8 32k;
        proxy_buffer_size 64k;
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
    }
    
    # API endpoints - route to Django with specific optimizations
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API specific optimizations
        proxy_buffers 8 32k;
        proxy_buffer_size 64k;
        proxy_read_timeout 90s;
        
        # Rate limiting for API
        limit_req zone=api burst=20 nodelay;
    }
    
    # Admin area - route to Django with specific security
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Additional security for admin
        client_max_body_size 10M;
        proxy_read_timeout 90s;
        
        # Basic rate limiting for admin login
        limit_req zone=admin burst=5 nodelay;
    }
    
    # All other requests - route to Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
    
    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "OK";
    }
    
    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

print_header "RESTARTING SERVICES"

# Restart Nginx
print_info "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    print_success "Nginx configuration is valid"
    print_info "Restarting Nginx..."
    systemctl restart nginx
else
    print_error "Nginx configuration is invalid. Please check the errors above."
    exit 1
fi

# Restart Django and Daphne
print_info "Restarting Django and Daphne services..."
systemctl restart eplatform-django
systemctl restart eplatform-daphne

print_header "CLEARING OLD LOGS"

# Clear old error logs
print_info "Clearing old error logs..."
echo "" > /var/log/nginx/eplatform_error.log
echo "" > /var/log/eplatform/gunicorn-error.log

print_header "TESTING CONFIGURATION"

# Test the configuration
print_info "Testing the configuration..."
curl -I http://localhost/

print_success "Fix complete! Your E_Platform should now be accessible at http://localhost"
print_info "Run the test script to verify: sudo bash nginx/test_enhanced.sh"

exit 0
