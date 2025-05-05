#!/bin/bash
# Script to fix the connection between Nginx and Daphne

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

print_header "CHECKING DAPHNE PROCESS"

# Check if Daphne is running and listening on port 8001
print_info "Checking Daphne process..."
daphne_pid=$(pgrep -f "daphne.*-p 8001")

if [ -n "$daphne_pid" ]; then
    print_success "Daphne is running with PID $daphne_pid"
    print_info "Daphne process details:"
    ps -p $daphne_pid -o pid,ppid,cmd,etime
else
    print_warning "Daphne process not found"
fi

print_header "TESTING DIRECT CONNECTION TO DAPHNE"

# Test direct connection to Daphne
print_info "Testing direct connection to Daphne on port 8001..."
if curl -s -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: localhost" -H "Origin: http://localhost" http://127.0.0.1:8001 > /tmp/daphne_response.txt; then
    print_success "Connection to Daphne successful"
    print_info "Response from Daphne:"
    cat /tmp/daphne_response.txt
else
    print_error "Connection to Daphne failed"
fi

print_header "UPDATING DAPHNE SERVICE"

# Update Daphne service to ensure it's binding to the correct address
print_info "Updating Daphne service configuration..."

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
    --proxy-headers \\
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

print_header "UPDATING NGINX CONFIGURATION"

# Update Nginx configuration for WebSocket
print_info "Updating Nginx configuration for WebSocket..."

# Backup current configuration
cp /etc/nginx/sites-available/eplatform.conf /etc/nginx/sites-available/eplatform.conf.bak

# Update WebSocket location block
sed -i '/location \/ws\/ {/,/}/c\
    # WebSocket connections - route to Daphne\
    location /ws/ {\
        proxy_pass http://127.0.0.1:8001;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 86400;  # Timeout for WebSocket connections (24h)\
        \
        # WebSocket specific optimizations\
        proxy_buffers 8 32k;\
        proxy_buffer_size 64k;\
        proxy_connect_timeout 90s;\
        proxy_send_timeout 90s;\
    }' /etc/nginx/sites-available/eplatform.conf

print_info "Testing Nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
    print_error "Nginx configuration test failed"
    print_info "Restoring backup configuration..."
    cp /etc/nginx/sites-available/eplatform.conf.bak /etc/nginx/sites-available/eplatform.conf
    exit 1
fi

print_header "RESTARTING SERVICES"

# Restart services
print_info "Restarting Daphne..."
systemctl restart eplatform-daphne

print_info "Restarting Nginx..."
systemctl restart nginx

# Wait for services to start
print_info "Waiting for services to start..."
sleep 5

print_header "VERIFYING CONNECTION"

# Verify Daphne is running
print_info "Verifying Daphne is running..."
if systemctl is-active --quiet eplatform-daphne; then
    print_success "Daphne service is running"
    
    # Check if port 8001 is in use
    print_info "Checking if port 8001 is in use..."
    if netstat -tuln | grep -q ":8001"; then
        print_success "Port 8001 is in use"
        print_info "Process using port 8001:"
        netstat -tulnp | grep ":8001"
    else
        print_error "Port 8001 is not in use"
    fi
else
    print_error "Daphne service is not running"
fi

# Test WebSocket connection through Nginx
print_info "Testing WebSocket connection through Nginx..."
curl -s -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: localhost" -H "Origin: http://localhost" http://localhost/ws/ > /tmp/nginx_ws_response.txt

print_info "Response from Nginx WebSocket request:"
cat /tmp/nginx_ws_response.txt

print_header "CHECKING LOGS"

# Check Nginx error log for WebSocket errors
print_info "Checking Nginx error log for WebSocket errors..."
if grep -q "connect() failed.*while connecting to upstream.*ws" /var/log/nginx/eplatform_error.log; then
    print_warning "Found WebSocket connection errors in Nginx log"
    grep "connect() failed.*while connecting to upstream.*ws" /var/log/nginx/eplatform_error.log | tail -5
else
    print_success "No recent WebSocket connection errors in Nginx log"
fi

# Check Daphne access log
print_info "Checking Daphne access log..."
if [ -f "$LOG_DIR/daphne-access.log" ]; then
    if [ -s "$LOG_DIR/daphne-access.log" ]; then
        print_success "Daphne is logging access"
        tail -5 "$LOG_DIR/daphne-access.log"
    else
        print_warning "Daphne access log is empty"
    fi
else
    print_warning "Daphne access log file does not exist"
fi

print_header "SUMMARY"

print_info "The connection between Nginx and Daphne should now be fixed."
print_info "If you're still experiencing issues, please check:"
print_info "1. Your Django Channels routing configuration"
print_info "2. The ASGI application setup"
print_info "3. Redis connection for Channels"
print_info "4. WebSocket consumer implementation"

print_info "You can run the check_services.sh script again to verify the connection:"
print_info "sudo bash nginx/check_services.sh"

exit 0
