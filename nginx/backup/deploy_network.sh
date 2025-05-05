#!/bin/bash
# Script to deploy Nginx configuration for local network access

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

# Define paths
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"

print_header "DETECTING LOCAL IP ADDRESS"

# Get local IP address
local_ip=$(ip addr | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n 1)

if [ -z "$local_ip" ]; then
    print_error "Could not detect local IP address"
    exit 1
fi

print_success "Detected local IP address: $local_ip"

print_header "UPDATING NGINX CONFIGURATION"

# Update the configuration file with the correct IP address
print_info "Updating configuration file with IP address: $local_ip"
sed "s/server_name 192.168.1.104;/server_name $local_ip;/" "$PROJECT_DIR/nginx/eplatform_network.conf" > "$PROJECT_DIR/nginx/eplatform_network_updated.conf"

# Copy the configuration file to Nginx
print_info "Copying configuration file to Nginx..."
cp "$PROJECT_DIR/nginx/eplatform_network_updated.conf" "$NGINX_CONF_DIR/eplatform_network.conf"

# Create symbolic link to enable the site
print_info "Enabling site..."
ln -sf "$NGINX_CONF_DIR/eplatform_network.conf" "$NGINX_ENABLED_DIR/eplatform_network.conf"

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

print_header "UPDATING WEBSOCKET TEST PAGE"

# Update WebSocket test page with the correct IP address
print_info "Updating WebSocket test page with IP address: $local_ip"
sed "s|value=\"ws://localhost/ws/notifications/1/\"|value=\"ws://$local_ip/ws/notifications/1/\"|" "$PROJECT_DIR/nginx/websocket_test.html" > "$PROJECT_DIR/staticfiles/websocket_test.html"

print_header "SUMMARY"

print_success "Network configuration deployed successfully!"
print_info "Your E_Platform is now accessible on your local network at:"
print_info "http://$local_ip"
print_info "WebSocket test page: http://$local_ip/static/websocket_test.html"

print_info "To test from another device on your network, open a browser and navigate to:"
print_info "http://$local_ip"

exit 0
