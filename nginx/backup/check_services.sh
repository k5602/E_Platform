#!/bin/bash
# Script to check if all services are running properly

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

print_header "CHECKING SERVICES"

# Check if services are running
services_ok=true

print_info "Checking Nginx service..."
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running"
    services_ok=false
fi

print_info "Checking Django service..."
if systemctl is-active --quiet eplatform-django; then
    print_success "Django service is running"
else
    print_error "Django service is not running"
    services_ok=false
fi

print_info "Checking Daphne service..."
if systemctl is-active --quiet eplatform-daphne; then
    print_success "Daphne service is running"
else
    print_error "Daphne service is not running"
    services_ok=false
fi

print_info "Checking Redis service..."
if systemctl is-active --quiet redis; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
    services_ok=false
fi

print_header "CHECKING PORTS"

# Check if ports are open
ports_ok=true

print_info "Checking if port 80 is open (Nginx)..."
if netstat -tuln | grep -q ":80"; then
    print_success "Port 80 is open (Nginx)"
else
    print_error "Port 80 is not open (Nginx)"
    ports_ok=false
fi

print_info "Checking if port 8000 is open (Django)..."
if netstat -tuln | grep -q ":8000"; then
    print_success "Port 8000 is open (Django)"
else
    print_error "Port 8000 is not open (Django)"
    ports_ok=false
fi

print_info "Checking if port 8001 is open (Daphne)..."
if netstat -tuln | grep -q ":8001"; then
    print_success "Port 8001 is open (Daphne)"
else
    print_error "Port 8001 is not open (Daphne)"
    ports_ok=false
fi

print_info "Checking if port 6379 is open (Redis)..."
if netstat -tuln | grep -q ":6379"; then
    print_success "Port 6379 is open (Redis)"
else
    print_error "Port 6379 is not open (Redis)"
    ports_ok=false
fi

print_header "CHECKING CONNECTIONS"

# Check if Nginx can connect to Django
print_info "Checking if Nginx can connect to Django..."
if curl -s http://127.0.0.1:8000 > /dev/null; then
    print_success "Nginx can connect to Django"
else
    print_error "Nginx cannot connect to Django"
fi

# Check if Nginx can connect to Daphne
print_info "Checking if Nginx can connect to Daphne..."
response=$(curl -s -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: localhost" -H "Origin: http://localhost" http://127.0.0.1:8001)
if echo "$response" | grep -q "400 WebSocket connection denied" || echo "$response" | grep -q "Bad Request" || echo "$response" | grep -q "101 Switching Protocols"; then
    print_success "Nginx can connect to Daphne (received expected WebSocket response)"
    print_info "Response excerpt: $(echo "$response" | head -1)"
else
    print_error "Nginx cannot connect to Daphne"
    print_info "Response: $(echo "$response" | head -3)"
fi

print_header "SUMMARY"

if [ "$services_ok" = true ] && [ "$ports_ok" = true ]; then
    print_success "All services are running and listening on the correct ports"
    print_info "Your Nginx reverse proxy setup should be working correctly"
else
    print_warning "Some services are not running or not listening on the correct ports"
    print_info "Please run the fix scripts to resolve the issues"
fi

exit 0
