#!/bin/bash

# E_Platform Unified Nginx Test Script
# This script helps verify that your Nginx reverse proxy is working correctly

echo "E_Platform Unified Nginx Test Script"
echo "==================================="

# Test HTTP connection
echo "Testing HTTP connection..."
curl -I "http://localhost"
echo ""

# Test static files
echo "Testing static file access..."
curl -I "http://localhost/static/css/responsive-utils.css"
echo ""

# Test WebSocket endpoint (basic check)
echo "Testing WebSocket endpoint (basic check)..."
curl -I "http://localhost/ws/chat/"
echo ""

# Check service status
echo "Checking service status..."
echo "Django service:"
systemctl status eplatform-django.service | head -n 5
echo ""
echo "Daphne service:"
systemctl status eplatform-daphne.service | head -n 5
echo ""
echo "Nginx service:"
systemctl status nginx | head -n 5
echo ""

# Check logs for errors
echo "Checking logs for errors..."
echo "Nginx error log:"
tail -n 10 /var/log/nginx/eplatform_error.log
echo ""
echo "Django (Gunicorn) error log:"
tail -n 10 /var/log/eplatform/gunicorn-error.log
echo ""
echo "Daphne access log:"
tail -n 10 /var/log/eplatform/daphne-access.log
echo ""

# Test WebSocket connection with wscat if available
if command -v wscat &> /dev/null; then
    echo "Testing WebSocket connection with wscat..."
    echo "Press Ctrl+C after a few seconds to exit"
    wscat -c "ws://localhost/ws/chat/?csrf_token=test"
else
    echo "wscat not found. Install it with 'npm install -g wscat' to test WebSocket connections."
fi

echo ""
echo "Test complete!"
echo "For a more thorough WebSocket test, please use the browser console and check WebSocket connections."
