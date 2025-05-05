#!/bin/bash
# Script to fix the Daphne service for E_Platform

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
LOG_DIR="/var/log/eplatform"
VENV_DIR="$PROJECT_DIR/.venv"

# Create log directory with proper permissions
print_info "Creating log directory with proper permissions..."
mkdir -p "$LOG_DIR"
chown -R zero:zero "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Install or upgrade Daphne in the virtual environment
print_info "Installing/upgrading Daphne in the virtual environment..."
su - zero -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && pip install --upgrade daphne channels channels-redis"

# Check if installation was successful
if [ $? -ne 0 ]; then
    print_error "Failed to install Daphne and dependencies"
    exit 1
fi

print_success "Daphne and dependencies installed/upgraded successfully"

# Create a test script to verify Daphne works
print_info "Creating a test script to verify Daphne..."
TEST_SCRIPT="$PROJECT_DIR/test_daphne.sh"

cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "Testing Daphne installation..."
daphne --version
echo "Testing Daphne with ASGI application..."
daphne -b 127.0.0.1 -p 8001 --verbosity 2 E_Platform.asgi:application
EOF

chmod +x "$TEST_SCRIPT"
chown zero:zero "$TEST_SCRIPT"

# Run the test script as the zero user
print_info "Running Daphne test script..."
su - zero -c "$TEST_SCRIPT" &
TEST_PID=$!

# Wait a few seconds to see if Daphne starts
sleep 5

# Check if Daphne is running
if kill -0 $TEST_PID 2>/dev/null; then
    print_success "Daphne test successful! Killing test process..."
    kill $TEST_PID
else
    print_warning "Daphne test failed. Check for errors above."
fi

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

# Reload systemd
print_info "Reloading systemd..."
systemctl daemon-reload

# Restart the Daphne service
print_info "Restarting Daphne service..."
systemctl restart eplatform-daphne

# Check if service started successfully
sleep 2
if systemctl is-active --quiet eplatform-daphne; then
    print_success "Daphne service started successfully!"
else
    print_error "Failed to start Daphne service. Checking logs..."
    journalctl -u eplatform-daphne -n 20
fi

print_info "Fix complete. Please check the status with: systemctl status eplatform-daphne"
