#!/bin/bash
# Script to check Django WebSocket configuration

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

# Define paths
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
VENV_DIR="$PROJECT_DIR/.venv"

print_header "CHECKING DJANGO CHANNELS SETUP"

# Check if Channels is installed
print_info "Checking if Channels is installed..."
if [ -d "$VENV_DIR" ]; then
    if source "$VENV_DIR/bin/activate" && pip freeze | grep -q "channels"; then
        print_success "Channels is installed"
        pip freeze | grep "channels"
    else
        print_warning "Channels is not installed"
    fi
else
    print_error "Virtual environment not found at $VENV_DIR"
fi

print_header "CHECKING ASGI CONFIGURATION"

# Check ASGI configuration
print_info "Checking ASGI configuration..."
if [ -f "$PROJECT_DIR/E_Platform/asgi.py" ]; then
    print_success "ASGI configuration file exists"
    print_info "Content of ASGI configuration:"
    cat "$PROJECT_DIR/E_Platform/asgi.py"
else
    print_error "ASGI configuration file does not exist"
fi

print_header "CHECKING ROUTING CONFIGURATION"

# Check for routing.py files
print_info "Checking for routing.py files..."
routing_files=$(find "$PROJECT_DIR" -name "routing.py")

if [ -n "$routing_files" ]; then
    print_success "Found routing.py files:"
    echo "$routing_files"
    
    # Display content of routing files
    for file in $routing_files; do
        print_info "Content of $file:"
        cat "$file"
        echo ""
    done
else
    print_warning "No routing.py files found"
fi

print_header "CHECKING CONSUMER FILES"

# Check for consumer.py or consumers.py files
print_info "Checking for consumer files..."
consumer_files=$(find "$PROJECT_DIR" -name "consumer*.py")

if [ -n "$consumer_files" ]; then
    print_success "Found consumer files:"
    echo "$consumer_files"
    
    # Display content of consumer files
    for file in $consumer_files; do
        print_info "Content of $file:"
        cat "$file"
        echo ""
    done
else
    print_warning "No consumer files found"
fi

print_header "CHECKING SETTINGS CONFIGURATION"

# Check settings.py for Channels configuration
print_info "Checking settings.py for Channels configuration..."
if [ -f "$PROJECT_DIR/E_Platform/settings.py" ]; then
    # Check if Channels is in INSTALLED_APPS
    if grep -q "'channels'" "$PROJECT_DIR/E_Platform/settings.py" || grep -q '"channels"' "$PROJECT_DIR/E_Platform/settings.py"; then
        print_success "Channels is in INSTALLED_APPS"
    else
        print_warning "Channels is not in INSTALLED_APPS"
    fi
    
    # Check for ASGI_APPLICATION setting
    if grep -q "ASGI_APPLICATION" "$PROJECT_DIR/E_Platform/settings.py"; then
        print_success "ASGI_APPLICATION is configured"
        grep -n "ASGI_APPLICATION" "$PROJECT_DIR/E_Platform/settings.py"
    else
        print_warning "ASGI_APPLICATION is not configured"
    fi
    
    # Check for CHANNEL_LAYERS setting
    if grep -q "CHANNEL_LAYERS" "$PROJECT_DIR/E_Platform/settings.py"; then
        print_success "CHANNEL_LAYERS is configured"
        grep -A 10 "CHANNEL_LAYERS" "$PROJECT_DIR/E_Platform/settings.py"
    else
        print_warning "CHANNEL_LAYERS is not configured"
    fi
else
    print_error "settings.py file not found"
fi

print_header "CHECKING REDIS CONNECTION"

# Check Redis connection
print_info "Checking Redis connection..."
if command -v redis-cli > /dev/null; then
    if redis-cli ping | grep -q "PONG"; then
        print_success "Redis connection successful"
    else
        print_error "Redis connection failed"
    fi
else
    print_warning "redis-cli not found"
fi

print_header "SUMMARY"

print_info "This script has checked your Django WebSocket configuration."
print_info "If you're experiencing WebSocket connection issues, make sure:"
print_info "1. Channels is properly installed and configured in settings.py"
print_info "2. ASGI application is properly configured"
print_info "3. Routing is correctly set up"
print_info "4. Consumer classes are implemented correctly"
print_info "5. Redis is running and accessible"

exit 0
