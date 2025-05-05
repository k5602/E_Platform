#!/bin/bash
# E_Platform Test and Fix Script
# This script tests the Nginx setup and fixes common issues

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
    echo "  -t, --test-only       Only run tests, don't fix anything"
    echo "  -f, --fix-only        Skip tests and go straight to fixing"
    echo "  -h, --help            Show this help message"
    echo ""
}

# Parse command line arguments
TEST_ONLY=false
FIX_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test-only)
            TEST_ONLY=true
            shift
            ;;
        -f|--fix-only)
            FIX_ONLY=true
            shift
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

print_header "E_PLATFORM TEST AND FIX SCRIPT"

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

# Get local IP address
get_ip() {
    # Try multiple methods to get the IP
    local ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    
    if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
        ip=$(ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1)
    fi
    
    if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
        ip=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1)
    fi
    
    echo "${ip:-127.0.0.1}"
}

LOCAL_IP=$(get_ip)

# Function to test services
run_tests() {
    print_header "TESTING SERVICES"
    
    # Test HTTP connection
    print_info "Testing HTTP connection..."
    if curl -s -I "http://localhost" | grep -q "200 OK\|302 Found"; then
        print_success "HTTP connection successful"
    else
        print_error "HTTP connection failed"
        issues_found=true
    fi
    
    # Test static files
    print_info "Testing static file access..."
    if curl -s -I "http://localhost/static/css/responsive-utils.css" | grep -q "200 OK"; then
        print_success "Static file access successful"
    else
        print_error "Static file access failed"
        issues_found=true
    fi
    
    # Test WebSocket endpoint (basic check)
    print_info "Testing WebSocket endpoint (basic check)..."
    if curl -s -I "http://localhost/ws/chat/" | grep -q "400 Bad Request\|101 Switching Protocols"; then
        print_success "WebSocket endpoint check successful"
    else
        print_error "WebSocket endpoint check failed"
        issues_found=true
    fi
    
    # Check service status
    print_info "Checking service status..."
    services_ok=true
    
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
        services_ok=false
        issues_found=true
    fi
    
    if systemctl is-active --quiet eplatform-django; then
        print_success "Django service is running"
    else
        print_error "Django service is not running"
        services_ok=false
        issues_found=true
    fi
    
    if systemctl is-active --quiet eplatform-daphne; then
        print_success "Daphne service is running"
    else
        print_error "Daphne service is not running"
        services_ok=false
        issues_found=true
    fi
    
    if systemctl is-active --quiet redis; then
        print_success "Redis is running"
    else
        print_error "Redis is not running"
        services_ok=false
        issues_found=true
    fi
    
    # Check logs for errors
    print_header "CHECKING LOGS FOR ERRORS"
    
    print_info "Nginx error log:"
    if [ -f /var/log/nginx/eplatform_error.log ]; then
        if grep -q "error\|critical" /var/log/nginx/eplatform_error.log; then
            print_warning "Errors found in Nginx error log:"
            grep -i "error\|critical" /var/log/nginx/eplatform_error.log | tail -n 5
            issues_found=true
        else
            print_success "No errors found in Nginx error log"
        fi
    else
        print_warning "Nginx error log file not found"
        issues_found=true
    fi
    
    print_info "Django (Gunicorn) error log:"
    if [ -f "$LOG_DIR/gunicorn-error.log" ]; then
        if grep -q "Error\|Exception\|Critical" "$LOG_DIR/gunicorn-error.log"; then
            print_warning "Errors found in Django error log:"
            grep -i "Error\|Exception\|Critical" "$LOG_DIR/gunicorn-error.log" | tail -n 5
            issues_found=true
        else
            print_success "No errors found in Django error log"
        fi
    else
        print_warning "Django error log file not found"
        issues_found=true
    fi
    
    print_info "Daphne access log:"
    if [ -f "$LOG_DIR/daphne-access.log" ]; then
        if grep -q "Error\|Exception\|Critical" "$LOG_DIR/daphne-access.log"; then
            print_warning "Errors found in Daphne log:"
            grep -i "Error\|Exception\|Critical" "$LOG_DIR/daphne-access.log" | tail -n 5
            issues_found=true
        else
            print_success "No errors found in Daphne log"
        fi
    else
        print_warning "Daphne log file not found"
        issues_found=true
    fi
    
    # Check port availability
    print_header "CHECKING PORT AVAILABILITY"
    
    print_info "Checking if port 80 is in use by Nginx..."
    if netstat -tuln | grep -q ":80 "; then
        print_success "Port 80 is in use (expected by Nginx)"
    else
        print_error "Port 80 is not in use. Nginx may not be running correctly."
        issues_found=true
    fi
    
    print_info "Checking if port 8000 is in use by Django..."
    if netstat -tuln | grep -q ":8000 "; then
        print_success "Port 8000 is in use (expected by Django)"
    else
        print_error "Port 8000 is not in use. Django may not be running correctly."
        issues_found=true
    fi
    
    print_info "Checking if port 8001 is in use by Daphne..."
    if netstat -tuln | grep -q ":8001 "; then
        print_success "Port 8001 is in use (expected by Daphne)"
    else
        print_error "Port 8001 is not in use. Daphne may not be running correctly."
        issues_found=true
    fi
    
    # Test WebSocket connection with wscat if available
    if command -v wscat &> /dev/null; then
        print_header "TESTING WEBSOCKET CONNECTION"
        print_info "Testing WebSocket connection with wscat..."
        print_info "This will attempt to connect to the WebSocket server for 5 seconds."
        print_info "Press Ctrl+C if it hangs or after you see connection messages."
        
        # Run wscat with a timeout
        timeout 5s wscat -c "ws://localhost/ws/chat/?csrf_token=test" || true
    fi
    
    # Summary
    print_header "TEST SUMMARY"
    
    if [ "$issues_found" = true ]; then
        print_warning "Issues were found during testing."
        if [ "$TEST_ONLY" = true ]; then
            print_info "Run this script without --test-only to attempt to fix these issues."
        else
            print_info "Proceeding to fix these issues..."
        fi
    else
        print_success "All tests passed successfully!"
    fi
}

# Function to fix common issues
fix_issues() {
    print_header "FIXING COMMON ISSUES"
    
    # Install dependencies
    print_info "Checking for required tools..."
    
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
    
    # Fix log directory
    print_info "Fixing log directory permissions..."
    mkdir -p "$LOG_DIR"
    chown -R zero:zero "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    
    # Fix static files
    print_info "Fixing static files..."
    mkdir -p "$STATIC_DIR"
    chown -R zero:zero "$STATIC_DIR"
    
    # Collect static files
    print_info "Collecting static files..."
    su - zero -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py collectstatic --noinput"
    
    if [ $? -eq 0 ]; then
        print_success "Static files collected successfully!"
        chmod -R 755 "$STATIC_DIR"
    else
        print_error "Failed to collect static files."
    fi
    
    # Fix Daphne installation
    print_info "Checking Daphne installation..."
    su - zero -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && pip install --upgrade daphne channels channels-redis"
    
    # Fix Redis
    print_info "Ensuring Redis is running..."
    systemctl enable redis
    systemctl restart redis
    
    # Restart services
    print_info "Restarting all services..."
    systemctl daemon-reload
    systemctl restart eplatform-django
    systemctl restart eplatform-daphne
    systemctl restart nginx
    
    # Check if services are running after fixes
    print_header "CHECKING SERVICES AFTER FIXES"
    
    services_fixed=true
    
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is still not running"
        print_info "Nginx error logs:"
        journalctl -u nginx -n 10
        services_fixed=false
    fi
    
    if systemctl is-active --quiet eplatform-django; then
        print_success "Django service is running"
    else
        print_error "Django service is still not running"
        print_info "Django service logs:"
        journalctl -u eplatform-django -n 10
        services_fixed=false
    fi
    
    if systemctl is-active --quiet eplatform-daphne; then
        print_success "Daphne service is running"
    else
        print_error "Daphne service is still not running"
        print_info "Daphne service logs:"
        journalctl -u eplatform-daphne -n 10
        services_fixed=false
    fi
    
    if systemctl is-active --quiet redis; then
        print_success "Redis is running"
    else
        print_error "Redis is still not running"
        services_fixed=false
    fi
    
    # Summary
    print_header "FIX SUMMARY"
    
    if [ "$services_fixed" = true ]; then
        print_success "All services are now running!"
        print_info "Your E_Platform should be accessible at:"
        print_info "- Local access: http://localhost"
        print_info "- Network access: http://$LOCAL_IP"
    else
        print_warning "Some services are still not running."
        print_info "Please check the logs for more details:"
        print_info "- Nginx: journalctl -u nginx"
        print_info "- Django: journalctl -u eplatform-django"
        print_info "- Daphne: journalctl -u eplatform-daphne"
        print_info "- Redis: journalctl -u redis"
    fi
}

# Main execution
issues_found=false

if [ "$FIX_ONLY" = false ]; then
    run_tests
fi

if [ "$TEST_ONLY" = false ] && ([ "$issues_found" = true ] || [ "$FIX_ONLY" = true ]); then
    fix_issues
fi

print_header "COMPLETED"
print_info "Test and fix script completed."
print_info "If you're still experiencing issues, please check the documentation or seek help."

exit 0
