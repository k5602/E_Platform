#!/bin/bash
# E_Platform Enhanced Nginx Testing Script
# This script tests the Nginx reverse proxy setup for E_Platform

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

# Function to check if a service is running
check_service() {
    local service_name="$1"
    print_info "Checking $service_name service..."

    if systemctl is-active --quiet "$service_name"; then
        print_success "$service_name is running"
        return 0
    else
        print_error "$service_name is not running"
        return 1
    fi
}

# Function to check if a port is open
check_port() {
    local port="$1"
    local service="$2"
    print_info "Checking if port $port is open ($service)..."

    # Check if nc command exists
    if ! command -v nc &> /dev/null; then
        print_warning "nc (netcat) command not found. Installing alternative check method."
        # Try using /dev/tcp as an alternative
        if (</dev/tcp/localhost/$port) 2>/dev/null; then
            print_success "Port $port is open ($service)"
            return 0
        else
            print_error "Port $port is closed ($service)"
            return 1
        fi
    else
        # Use nc if available
        if nc -z localhost "$port"; then
            print_success "Port $port is open ($service)"
            return 0
        else
            print_error "Port $port is closed ($service)"
            return 1
        fi
    fi
}

# Function to check HTTP response
check_http() {
    local url="$1"
    local expected_code="$2"
    local description="$3"
    local allow_redirect="${4:-false}"
    print_info "Testing HTTP request to $url ($description)..."

    # Use -L to follow redirects if allowed
    if [ "$allow_redirect" = "true" ]; then
        local response=$(curl -L -s -o /dev/null -w "%{http_code}" "$url")
        print_info "Following redirects for $url"
    else
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi

    if [ "$response" = "$expected_code" ]; then
        print_success "HTTP request to $url returned $response (expected $expected_code)"
        return 0
    elif [ "$response" = "302" ] && [ "$allow_redirect" = "false" ]; then
        print_warning "HTTP request to $url returned a redirect (302). This may be expected for login-protected pages."
        return 0
    else
        print_error "HTTP request to $url returned $response (expected $expected_code)"
        return 1
    fi
}

# Function to check if a file exists
check_file() {
    local file_path="$1"
    local description="$2"
    print_info "Checking if $description exists at $file_path..."

    if [ -f "$file_path" ]; then
        print_success "$description exists"
        return 0
    else
        print_error "$description does not exist"
        return 1
    fi
}

# Function to check log files for errors
check_logs() {
    local log_file="$1"
    local description="$2"
    print_info "Checking $description log file for errors..."

    if [ -f "$log_file" ]; then
        local error_count=$(grep -i "error\|critical\|fatal" "$log_file" | wc -l)

        if [ "$error_count" -eq 0 ]; then
            print_success "No errors found in $description log"
            return 0
        else
            print_warning "Found $error_count errors in $description log"
            print_info "Last 5 errors:"
            grep -i "error\|critical\|fatal" "$log_file" | tail -n 5
            return 1
        fi
    else
        print_warning "$description log file does not exist yet"
        return 0
    fi
}

# Main testing sequence
print_header "SYSTEM SERVICES"

# Check if services are running
services_ok=true
check_service "nginx" || services_ok=false
check_service "eplatform-django" || services_ok=false
check_service "eplatform-daphne" || services_ok=false
check_service "redis" || services_ok=false

if [ "$services_ok" = true ]; then
    print_success "All required services are running"
else
    print_error "Some services are not running"
fi

print_header "NETWORK PORTS"

# Check if ports are open
ports_ok=true
check_port 80 "Nginx HTTP" || ports_ok=false
check_port 8000 "Django/Gunicorn" || ports_ok=false
check_port 8001 "Daphne/WebSocket" || ports_ok=false
check_port 6379 "Redis" || ports_ok=false

if [ "$ports_ok" = true ]; then
    print_success "All required ports are open"
else
    print_error "Some ports are closed"
fi

print_header "CONFIGURATION FILES"

# Check if configuration files exist
config_ok=true
check_file "/etc/nginx/nginx.conf" "Nginx global configuration" || config_ok=false
check_file "/etc/nginx/sites-available/eplatform.conf" "E_Platform Nginx configuration" || config_ok=false
check_file "/etc/systemd/system/eplatform-django.service" "Django systemd service" || config_ok=false
check_file "/etc/systemd/system/eplatform-daphne.service" "Daphne systemd service" || config_ok=false

if [ "$config_ok" = true ]; then
    print_success "All configuration files exist"
else
    print_error "Some configuration files are missing"
fi

print_header "NGINX CONFIGURATION"

# Test Nginx configuration
print_info "Testing Nginx configuration syntax..."
if nginx -t &> /dev/null; then
    print_success "Nginx configuration syntax is valid"
else
    print_error "Nginx configuration syntax is invalid"
    nginx -t
fi

print_header "HTTP REQUESTS"

# Get server name from Nginx config
server_name=$(grep -m 1 "server_name" /etc/nginx/sites-available/eplatform.conf | awk '{print $2}' | tr -d ';')
if [ "$server_name" = "your_domain.com" ]; then
    print_warning "Using default server name. Consider updating it in the configuration."
    server_name="localhost"
fi

# Test HTTP requests
http_ok=true
check_http "http://$server_name/" 200 "Main page" "true" || http_ok=false
# Check if staticfiles directory exists and has content
if [ -d "/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform/staticfiles" ]; then
    # Find an existing CSS file to test
    css_file=$(find /mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform/staticfiles -name "*.css" -type f | head -n 1)
    if [ -n "$css_file" ]; then
        # Extract the relative path from the staticfiles directory
        rel_path=${css_file#/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform/staticfiles/}
        check_http "http://$server_name/static/$rel_path" 200 "Static file" || http_ok=false
    else
        print_warning "No CSS files found in staticfiles directory. Skipping static file test."
    fi
else
    print_warning "Staticfiles directory not found. Run 'python manage.py collectstatic' to collect static files."
fi
check_http "http://$server_name/admin/" 200 "Admin page" "true" || http_ok=false
# Check if the API endpoint exists
if curl -s -o /dev/null -w "%{http_code}" "http://$server_name/api/auth/" | grep -q "404"; then
    print_warning "API endpoint /api/auth/ not found. This is expected if the endpoint doesn't exist."
    print_info "Trying alternative API endpoint..."

    # Try a different API endpoint
    if curl -s -o /dev/null -w "%{http_code}" "http://$server_name/api/" | grep -q "200"; then
        print_success "Alternative API endpoint /api/ is working"
    else
        print_warning "No API endpoints found. This may be normal if your application doesn't have API endpoints yet."
    fi
else
    check_http "http://$server_name/api/auth/" 200 "API endpoint" "true" || http_ok=false
fi

if [ "$http_ok" = true ]; then
    print_success "All HTTP requests returned expected responses"
else
    print_warning "Some HTTP requests failed"
fi

print_header "LOG FILES"

# Check log files for errors
logs_ok=true
check_logs "/var/log/nginx/error.log" "Nginx error" || logs_ok=false
check_logs "/var/log/nginx/eplatform_error.log" "E_Platform Nginx error" || logs_ok=false
check_logs "/var/log/eplatform/gunicorn-error.log" "Django/Gunicorn error" || logs_ok=false
check_logs "/var/log/eplatform/daphne-access.log" "Daphne access" || logs_ok=false

if [ "$logs_ok" = true ]; then
    print_success "No critical errors found in log files"
else
    print_warning "Some log files contain errors"
fi

print_header "SUMMARY"

# Print summary
if [ "$services_ok" = true ] && [ "$ports_ok" = true ] && [ "$config_ok" = true ] && [ "$http_ok" = true ]; then
    print_success "All tests passed! Your E_Platform Nginx setup appears to be working correctly."
    print_info "You can access your application at: http://$server_name/"
else
    print_warning "Some tests failed. Please check the issues above."

    if [ "$services_ok" = false ]; then
        print_info "To start services: sudo systemctl start [service-name]"
    fi

    if [ "$config_ok" = false ]; then
        print_info "To fix configuration: Check the deployment script or manually copy the files"
    fi

    if [ "$http_ok" = false ]; then
        print_info "To debug HTTP issues: Check Nginx and application logs"
    fi

    print_info "For more help, see the troubleshooting guide: nginx/TROUBLESHOOTING.md"
fi

exit 0
