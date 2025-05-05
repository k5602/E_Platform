#!/bin/bash

# E_Platform Unified Run Script with Nginx
# This script runs the E_Platform application with Nginx as a reverse proxy

# Exit on error
set -e

echo "E_Platform Unified Run Script with Nginx"
echo "========================================"

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Nginx is not installed. Please install it with:"
    echo "sudo pacman -S nginx"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root or with sudo"
    exit 1
fi

# Variables
PROJECT_DIR="$(pwd)"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
LOG_DIR="/var/log/eplatform"

# Create directories if they don't exist
echo "Creating necessary directories..."
mkdir -p "$NGINX_CONF_DIR"
mkdir -p "$NGINX_ENABLED_DIR"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"
chown http:http "$LOG_DIR"

# Copy Nginx configuration for development
echo "Setting up Nginx configuration for development..."
cat > "$NGINX_CONF_DIR/eplatform_dev.conf" << EOF
server {
    listen 80;
    server_name localhost;
    
    # Access and error logs
    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
    
    # Maximum upload size
    client_max_body_size 20M;
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
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
        proxy_read_timeout 86400;
    }
    
    # All other requests - route to Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Create symbolic link to enable the site
echo "Enabling site..."
ln -sf "$NGINX_CONF_DIR/eplatform_dev.conf" "$NGINX_ENABLED_DIR/eplatform_dev.conf"

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl restart nginx

# Create temporary scripts for Django and Daphne
DJANGO_SCRIPT=$(mktemp)
DAPHNE_SCRIPT=$(mktemp)

# Create Django server script
echo "#!/bin/bash" > $DJANGO_SCRIPT
echo "cd \"$PROJECT_DIR\"" >> $DJANGO_SCRIPT
echo "source .venv/bin/activate" >> $DJANGO_SCRIPT
echo "echo \"Starting Django development server on 127.0.0.1:8000...\"" >> $DJANGO_SCRIPT
echo "echo \"This server handles HTTP requests.\"" >> $DJANGO_SCRIPT
echo "echo \"Keep this terminal window open while using the application.\"" >> $DJANGO_SCRIPT
echo "echo \"------------------------------------------------------------\"" >> $DJANGO_SCRIPT
echo "python manage.py runserver 127.0.0.1:8000" >> $DJANGO_SCRIPT
chmod +x $DJANGO_SCRIPT

# Create WebSocket server script
echo "#!/bin/bash" > $DAPHNE_SCRIPT
echo "cd \"$PROJECT_DIR\"" >> $DAPHNE_SCRIPT
echo "source .venv/bin/activate" >> $DAPHNE_SCRIPT
echo "echo \"Starting Daphne WebSocket server on 127.0.0.1:8001...\"" >> $DAPHNE_SCRIPT
echo "echo \"This server handles WebSocket connections only.\"" >> $DAPHNE_SCRIPT
echo "echo \"Keep this terminal window open while using the application.\"" >> $DAPHNE_SCRIPT
echo "echo \"------------------------------------------------------------\"" >> $DAPHNE_SCRIPT
echo "export WEBSOCKET_CSRF_EXEMPT=true" >> $DAPHNE_SCRIPT
echo "export DJANGO_ALLOW_ASYNC_UNSAFE=true" >> $DAPHNE_SCRIPT
echo "daphne -b 127.0.0.1 -p 8001 E_Platform.asgi:application" >> $DAPHNE_SCRIPT
chmod +x $DAPHNE_SCRIPT

# Function to clean up on exit
cleanup() {
    echo "Cleaning up..."
    kill $DJANGO_PID 2>/dev/null || true
    kill $DAPHNE_PID 2>/dev/null || true
    rm -f $DJANGO_SCRIPT $DAPHNE_SCRIPT
    echo "Servers stopped."
}

# Set up trap to clean up on exit
trap cleanup EXIT INT TERM

# Run Django server in the background
$DJANGO_SCRIPT > $LOG_DIR/django_dev.log 2>&1 &
DJANGO_PID=$!
echo "Django server started in background (PID: $DJANGO_PID)"
echo "Log file: $LOG_DIR/django_dev.log"

# Run Daphne server in the background
$DAPHNE_SCRIPT > $LOG_DIR/daphne_dev.log 2>&1 &
DAPHNE_PID=$!
echo "Daphne server started in background (PID: $DAPHNE_PID)"
echo "Log file: $LOG_DIR/daphne_dev.log"

echo ""
echo "All services started!"
echo "Your E_Platform should now be accessible at http://localhost"
echo ""
echo "Press Ctrl+C to stop all servers"

# Keep the script running
while true; do
    sleep 1
    # Check if both servers are still running
    if ! kill -0 $DJANGO_PID 2>/dev/null; then
        echo "Django server stopped unexpectedly. Check logs for details."
        exit 1
    fi
    if ! kill -0 $DAPHNE_PID 2>/dev/null; then
        echo "Daphne server stopped unexpectedly. Check logs for details."
        exit 1
    fi
done
