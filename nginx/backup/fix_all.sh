#!/bin/bash
# Comprehensive fix script for E_Platform Nginx setup

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
STATIC_DIR="$PROJECT_DIR/staticfiles"
VENV_DIR="$PROJECT_DIR/.venv"

print_header "INSTALLING DEPENDENCIES"

# Install netcat if missing
if ! command -v nc &> /dev/null; then
    print_info "Installing netcat..."
    if command -v pacman &> /dev/null; then
        pacman -Sy --noconfirm openbsd-netcat
    elif command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y netcat-openbsd
    elif command -v dnf &> /dev/null; then
        dnf install -y nc
    else
        print_warning "Could not determine package manager. Please install netcat manually."
    fi
else
    print_success "Netcat is already installed"
fi

print_header "FIXING LOG DIRECTORY"

# Create log directory with proper permissions
print_info "Creating log directory with proper permissions..."
mkdir -p "$LOG_DIR"
chown -R zero:zero "$LOG_DIR"
chmod 755 "$LOG_DIR"

print_header "FIXING DAPHNE SERVICE"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Install or upgrade Daphne in the virtual environment
print_info "Installing/upgrading Daphne in the virtual environment..."
su - zero -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && pip install --upgrade daphne channels channels-redis"

# Update the service file to use a simpler configuration
print_info "Updating Daphne service file with simpler configuration..."

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
    E_Platform.asgi:application

Environment=DJANGO_SETTINGS_MODULE=E_Platform.settings
Environment=DJANGO_ALLOW_ASYNC_UNSAFE=true
Environment=WEBSOCKET_CSRF_EXEMPT=true

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

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

print_header "RESTARTING SERVICES"

# Make sure Redis is running
print_info "Ensuring Redis is running..."
systemctl enable redis
systemctl restart redis

# Reload systemd
print_info "Reloading systemd..."
systemctl daemon-reload

# Restart services
print_info "Restarting Django service..."
systemctl restart eplatform-django

print_info "Restarting Daphne service..."
systemctl restart eplatform-daphne

print_info "Restarting Nginx..."
systemctl restart nginx

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
    
    # Show Daphne logs if it's not running
    print_info "Daphne service logs:"
    journalctl -u eplatform-daphne -n 20
fi

if systemctl is-active --quiet redis; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
    services_ok=false
fi

print_header "SUMMARY"

if [ "$services_ok" = true ]; then
    print_success "All services are running! The fix was successful."
    print_info "You can now access your application at http://localhost"
else
    print_warning "Some services are still not running. Please check the logs for more details."
fi

print_info "To run the test script: sudo bash nginx/test_enhanced.sh"

exit 0
