#!/bin/bash
# Script to fix WebSocket connection issues with Daphne

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
LOG_DIR="/var/log/eplatform"
VENV_DIR="$PROJECT_DIR/.venv"

print_header "CHECKING DAPHNE SERVICE"

# Check Daphne service status
print_info "Checking Daphne service status..."
if systemctl is-active --quiet eplatform-daphne; then
    print_success "Daphne service is active"
else
    print_warning "Daphne service is not active"
    
    # Check logs
    print_info "Checking Daphne service logs..."
    journalctl -u eplatform-daphne -n 20
fi

print_header "CHECKING PORT 8001"

# Check if port 8001 is in use
print_info "Checking if port 8001 is in use..."
if netstat -tuln | grep -q ":8001"; then
    print_success "Port 8001 is in use"
    print_info "Process using port 8001:"
    netstat -tulnp | grep ":8001"
else
    print_warning "Port 8001 is not in use"
fi

print_header "CHECKING FIREWALL"

# Check if firewall is blocking port 8001
print_info "Checking if firewall is blocking port 8001..."
if command -v ufw &> /dev/null; then
    ufw status | grep 8001
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --list-ports | grep 8001
else
    print_info "No firewall detected or not using ufw/firewalld"
fi

print_header "UPDATING DAPHNE SERVICE"

# Update Daphne service file
print_info "Updating Daphne service file..."

cat > /etc/systemd/system/eplatform-daphne.service << EOF
[Unit]
Description=E_Platform Daphne Service (WebSocket Server)
After=network.target redis.service
Wants=redis.service

[Service]
User=zero
Group=zero
WorkingDirectory=/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform
ExecStart=/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform/.venv/bin/daphne \\
    -b 127.0.0.1 \\
    -p 8001 \\
    --access-log /var/log/eplatform/daphne-access.log \\
    --verbosity 2 \\
    E_Platform.asgi:application

Environment=DJANGO_SETTINGS_MODULE=E_Platform.settings
Environment=DJANGO_ALLOW_ASYNC_UNSAFE=true
Environment=WEBSOCKET_CSRF_EXEMPT=true

Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

print_info "Reloading systemd..."
systemctl daemon-reload

print_header "CHECKING ASGI CONFIGURATION"

# Check if ASGI configuration exists
print_info "Checking if ASGI configuration exists..."
if [ -f "$PROJECT_DIR/E_Platform/asgi.py" ]; then
    print_success "ASGI configuration exists"
    print_info "Content of ASGI configuration:"
    cat "$PROJECT_DIR/E_Platform/asgi.py"
else
    print_error "ASGI configuration does not exist"
    exit 1
fi

print_header "CHECKING CHANNELS CONFIGURATION"

# Check if Channels is installed
print_info "Checking if Channels is installed..."
su - zero -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && pip freeze | grep channels"

# Check if Channels is configured in settings.py
print_info "Checking if Channels is configured in settings.py..."
if grep -q "CHANNEL_LAYERS" "$PROJECT_DIR/E_Platform/settings.py"; then
    print_success "Channels is configured in settings.py"
    print_info "Channels configuration:"
    grep -A 10 "CHANNEL_LAYERS" "$PROJECT_DIR/E_Platform/settings.py"
else
    print_warning "Channels configuration not found in settings.py"
    
    print_info "Adding Channels configuration to settings.py..."
    cat >> "$PROJECT_DIR/E_Platform/settings.py" << EOF

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
EOF
    
    print_success "Added Channels configuration to settings.py"
fi

print_header "CHECKING INSTALLED APPS"

# Check if Channels is in INSTALLED_APPS
print_info "Checking if Channels is in INSTALLED_APPS..."
if grep -q "'channels'" "$PROJECT_DIR/E_Platform/settings.py"; then
    print_success "Channels is in INSTALLED_APPS"
else
    print_warning "Channels not found in INSTALLED_APPS"
    
    print_info "Adding Channels to INSTALLED_APPS..."
    sed -i "/INSTALLED_APPS = \[/a \    'channels'," "$PROJECT_DIR/E_Platform/settings.py"
    
    print_success "Added Channels to INSTALLED_APPS"
fi

print_header "CHECKING REDIS"

# Check if Redis is running
print_info "Checking if Redis is running..."
if systemctl is-active --quiet redis; then
    print_success "Redis is running"
else
    print_warning "Redis is not running"
    print_info "Starting Redis..."
    systemctl start redis
fi

# Test Redis connection
print_info "Testing Redis connection..."
if redis-cli ping | grep -q "PONG"; then
    print_success "Redis connection successful"
else
    print_error "Redis connection failed"
fi

print_header "RESTARTING SERVICES"

# Restart Daphne
print_info "Restarting Daphne service..."
systemctl restart eplatform-daphne

# Wait for Daphne to start
print_info "Waiting for Daphne to start..."
sleep 5

# Check if Daphne is running
print_info "Checking if Daphne is running..."
if systemctl is-active --quiet eplatform-daphne; then
    print_success "Daphne service is running"
    
    # Check if port 8001 is in use
    print_info "Checking if port 8001 is in use..."
    if netstat -tuln | grep -q ":8001"; then
        print_success "Port 8001 is in use"
        print_info "Process using port 8001:"
        netstat -tulnp | grep ":8001"
    else
        print_error "Port 8001 is still not in use"
        print_info "Checking Daphne logs..."
        journalctl -u eplatform-daphne -n 20
    fi
else
    print_error "Daphne service is not running"
    print_info "Checking Daphne logs..."
    journalctl -u eplatform-daphne -n 20
fi

print_header "TESTING WEBSOCKET CONNECTION"

# Test WebSocket connection
print_info "Testing WebSocket connection..."
if command -v websocat &> /dev/null; then
    print_info "Using websocat to test WebSocket connection..."
    timeout 5 websocat ws://localhost/ws/notifications/1/ || print_warning "WebSocket connection timed out or failed"
else
    print_info "Testing WebSocket connection with curl..."
    curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: localhost" -H "Origin: http://localhost" http://localhost/ws/notifications/1/
fi

print_header "SUMMARY"

# Check if Daphne is running
if systemctl is-active --quiet eplatform-daphne && netstat -tuln | grep -q ":8001"; then
    print_success "WebSocket server is running and listening on port 8001"
    print_info "Your WebSocket connections should now work properly"
else
    print_warning "WebSocket server is still not running correctly"
    print_info "Please check the logs and try again"
fi

print_info "If you continue to have issues, try restarting all services:"
print_info "sudo systemctl restart redis eplatform-django eplatform-daphne nginx"

exit 0
