#!/bin/bash
# E_Platform Unified Deployment Script
# This script sets up Nginx as a reverse proxy for both Django and Daphne servers
# and configures it to work on your local network

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

print_header() {
    echo -e "\n\e[1;36m=== $1 ===\e[0m"
}

# Display help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --ip IP_ADDRESS    Specify the IP address manually"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --ip 192.168.1.100  Use 192.168.1.100 as the IP address"
    echo ""
}

# Parse command line arguments
MANUAL_IP=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--ip)
            MANUAL_IP="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

print_header "E_PLATFORM UNIFIED DEPLOYMENT"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Variables - adjust these to match your setup
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
NGINX_MAIN_CONF="/etc/nginx/nginx.conf"
LOG_DIR="/var/log/eplatform"
STATIC_DIR="$PROJECT_DIR/staticfiles"
VENV_DIR="$PROJECT_DIR/.venv"

print_header "DETECTING LOCAL IP ADDRESS"

# Get local IP address
get_ip() {
    # Method 1: hostname -I (most common)
    local ip1=$(hostname -I 2>/dev/null | awk '{print $1}')

    # Method 2: ip command
    local ip2=$(ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1)

    # Method 3: ifconfig command
    local ip3=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1)

    # Method 4: Using a specific interface (try common ones)
    for interface in eth0 wlan0 enp0s3 enp0s8 ens33 wlp2s0; do
        local ip4=$(ip -4 addr show $interface 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        if [ -n "$ip4" ]; then
            break
        fi
    done

    # Return the first non-empty IP
    if [ -n "$ip1" ]; then
        echo "$ip1"
    elif [ -n "$ip2" ]; then
        echo "$ip2"
    elif [ -n "$ip3" ]; then
        echo "$ip3"
    elif [ -n "$ip4" ]; then
        echo "$ip4"
    else
        echo "127.0.0.1"  # Fallback to localhost if no IP is found
    fi
}

# Check if IP was provided as command-line argument
if [ -n "$MANUAL_IP" ]; then
    # Validate the provided IP
    if [[ $MANUAL_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        LOCAL_IP=$MANUAL_IP
        print_success "Using provided IP address: $LOCAL_IP"
    else
        print_error "Invalid IP format provided. Will try to detect automatically."
        MANUAL_IP=""
    fi
else
    # Get the local IP address automatically
    LOCAL_IP=$(get_ip)

    # Check if the IP is localhost, which indicates detection failure
    if [ "$LOCAL_IP" = "127.0.0.1" ]; then
        print_warning "Could not automatically detect your network IP address."
        print_info "Please enter your network IP address manually."
        print_info "You can find it by running 'ip addr' or 'ifconfig' in another terminal."
        print_info "It should look like 192.168.x.x or 10.0.x.x"
        
        # Prompt for manual IP entry
        read -p "Enter your network IP address: " MANUAL_IP

        # Validate the entered IP
        if [[ $MANUAL_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            LOCAL_IP=$MANUAL_IP
            print_success "Using manually entered IP: $LOCAL_IP"
        else
            print_warning "Invalid IP format. Using localhost (127.0.0.1) as fallback."
            print_info "Note: Other devices will not be able to connect using this IP."
            LOCAL_IP="127.0.0.1"
        fi
    else
        print_success "Detected local IP address: $LOCAL_IP"
    fi
fi

print_header "CREATING DIRECTORIES"

# Create directories if they don't exist
print_info "Creating necessary directories..."
mkdir -p "$NGINX_CONF_DIR"
mkdir -p "$NGINX_ENABLED_DIR"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"
chown http:http "$LOG_DIR"

print_header "COLLECTING STATIC FILES"

# Create staticfiles directory if it doesn't exist
print_info "Creating staticfiles directory..."
mkdir -p "$STATIC_DIR"
chown -R zero:zero "$STATIC_DIR"

# Collect static files
print_info "Collecting static files..."
su - zero -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py collectstatic --noinput"

if [ $? -eq 0 ]; then
    print_success "Static files collected successfully!"
    
    # Set permissions
    chmod -R 755 "$STATIC_DIR"
    
    # Count collected files
    file_count=$(find "$STATIC_DIR" -type f | wc -l)
    print_info "Collected $file_count static files in $STATIC_DIR"
else
    print_error "Failed to collect static files."
fi

print_header "CONFIGURING NGINX"

# Update the configuration file with the correct IP address
print_info "Creating Nginx configuration with IP address: $LOCAL_IP"

# Create a new configuration file based on eplatform_unified.conf but with the correct IP
cat > "$NGINX_CONF_DIR/eplatform.conf" << EOF
server {
    listen 80;
    server_name localhost $LOCAL_IP;  # Listen on both localhost and the local IP
    
    # Access and error logs
    access_log /var/log/nginx/eplatform_access.log;
    error_log /var/log/nginx/eplatform_error.log;
    
    # Maximum upload size
    client_max_body_size 20M;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files - served directly by Nginx for better performance
    location /static/ {
        alias $STATIC_DIR/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        access_log off;
    }
    
    # Media files - served directly by Nginx
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        access_log off;
    }
    
    # WebSocket connections - route to Daphne
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # API specific optimizations
        proxy_buffers 8 32k;
        proxy_buffer_size 64k;
        proxy_read_timeout 90s;
    }
    
    # Admin area - route to Django with specific security
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Additional security for admin
        client_max_body_size 10M;
        proxy_read_timeout 90s;
    }
    
    # All other requests - route to Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }
}
EOF

# Copy main Nginx configuration
print_info "Copying main Nginx configuration..."
cp "$PROJECT_DIR/nginx/nginx.conf" "$NGINX_MAIN_CONF"

# Create symbolic link to enable the site
print_info "Enabling site..."
ln -sf "$NGINX_CONF_DIR/eplatform.conf" "$NGINX_ENABLED_DIR/eplatform.conf"

print_header "CONFIGURING SYSTEMD SERVICES"

# Create Django service file
print_info "Creating Django service file..."
cat > /etc/systemd/system/eplatform-django.service << EOF
[Unit]
Description=E_Platform Django Service
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
User=zero
Group=zero
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    --timeout 120 \\
    --access-logfile $LOG_DIR/gunicorn-access.log \\
    --error-logfile $LOG_DIR/gunicorn-error.log \\
    E_Platform.wsgi:application

# Environment variables
Environment=DB_ENGINE=postgresql
Environment=DB_NAME=e_platform_db
Environment=DB_USER=zero
Environment=DB_PASSWORD=82821931003
Environment=DB_HOST=localhost
Environment=DB_PORT=5432

# Restart on failure
Restart=on-failure
RestartSec=5s

# Limit resources
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF

# Create Daphne service file
print_info "Creating Daphne service file..."
cat > /etc/systemd/system/eplatform-daphne.service << EOF
[Unit]
Description=E_Platform Daphne Service (WebSocket Server)
After=network.target redis.service
Wants=redis.service

[Service]
User=zero
Group=zero
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/daphne \\
    -b 127.0.0.1 \\
    -p 8001 \\
    --access-log $LOG_DIR/daphne-access.log \\
    E_Platform.asgi:application

# Environment variables
Environment=DJANGO_SETTINGS_MODULE=E_Platform.settings
Environment=DJANGO_ALLOW_ASYNC_UNSAFE=true
Environment=WEBSOCKET_CSRF_EXEMPT=true
Environment=DB_ENGINE=postgresql
Environment=DB_NAME=e_platform_db
Environment=DB_USER=zero
Environment=DB_PASSWORD=82821931003
Environment=DB_HOST=localhost
Environment=DB_PORT=5432

# Restart on failure
Restart=on-failure
RestartSec=5s

# Limit resources
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF

print_header "UPDATING WEBSOCKET TEST PAGE"

# Update WebSocket test page with the correct IP address
print_info "Updating WebSocket test page with IP address: $LOCAL_IP"
sed "s|value=\"ws://localhost/ws/notifications/1/\"|value=\"ws://$LOCAL_IP/ws/notifications/1/\"|" "$PROJECT_DIR/nginx/websocket_test.html" > "$PROJECT_DIR/staticfiles/websocket_test.html"

print_header "UPDATING FIREWALL"

# Check if firewall is enabled
print_info "Checking firewall status..."

if command -v ufw &> /dev/null; then
    # Using UFW
    print_info "UFW detected"
    
    if ufw status | grep -q "Status: active"; then
        print_info "UFW is active, allowing port 80..."
        ufw allow 80/tcp
        print_success "Port 80 allowed in UFW"
    else
        print_info "UFW is not active"
    fi
elif command -v firewall-cmd &> /dev/null; then
    # Using firewalld
    print_info "firewalld detected"
    
    if systemctl is-active --quiet firewalld; then
        print_info "firewalld is active, allowing port 80..."
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --reload
        print_success "Port 80 allowed in firewalld"
    else
        print_info "firewalld is not active"
    fi
else
    print_info "No firewall detected or not using ufw/firewalld"
fi

print_header "STARTING SERVICES"

# Reload systemd
print_info "Reloading systemd..."
systemctl daemon-reload

# Make sure Redis is running
print_info "Ensuring Redis is running..."
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
    print_success "Nginx configuration is valid"
    print_info "Restarting Nginx..."
    systemctl restart nginx
else
    print_error "Nginx configuration is invalid. Please check the errors above."
    exit 1
fi

print_header "CHECKING SERVICE STATUS"

# Check if services are running
print_info "Checking service status..."
services_ok=true

if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running"
    services_ok=false
fi

if systemctl is-active --quiet eplatform-django; then
    print_success "Django service is running"
else
    print_error "Django service is not running"
    services_ok=false
fi

if systemctl is-active --quiet eplatform-daphne; then
    print_success "Daphne service is running"
else
    print_error "Daphne service is not running"
    services_ok=false
fi

if systemctl is-active --quiet redis; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
    services_ok=false
fi

print_header "DEPLOYMENT SUMMARY"

if [ "$services_ok" = true ]; then
    print_success "Deployment completed successfully!"
    print_info "Your E_Platform is now accessible at:"
    print_info "- Local access: http://localhost"
    print_info "- Network access: http://$LOCAL_IP"
    print_info "WebSocket test page: http://$LOCAL_IP/static/websocket_test.html"
    
    print_info "To test from another device on your network, open a browser and navigate to:"
    print_info "http://$LOCAL_IP"
    
    print_info "To test and troubleshoot your setup, run:"
    print_info "sudo bash nginx/test_fix.sh"
else
    print_warning "Deployment completed with some issues. Some services are not running."
    print_info "Please run the test and fix script to troubleshoot:"
    print_info "sudo bash nginx/test_fix.sh"
fi

exit 0
