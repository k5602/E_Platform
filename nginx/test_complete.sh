#!/bin/bash

# E_Platform Nginx Test Script
# This script helps verify that your Nginx reverse proxy is working correctly

# Variables
DOMAIN="localhost"  # Change this to your domain or IP

echo "E_Platform Nginx Test Script"
echo "==========================="
echo ""

# Check if Nginx is running
echo "Checking if Nginx is running..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is not running"
    echo "Try starting it with: sudo systemctl start nginx"
    exit 1
fi

# Check if Django service is running
echo "Checking if Django service is running..."
if systemctl is-active --quiet eplatform-django; then
    echo "✅ Django service is running"
else
    echo "❌ Django service is not running"
    echo "Try starting it with: sudo systemctl start eplatform-django"
    exit 1
fi

# Check if Daphne service is running
echo "Checking if Daphne service is running..."
if systemctl is-active --quiet eplatform-daphne; then
    echo "✅ Daphne service is running"
else
    echo "❌ Daphne service is not running"
    echo "Try starting it with: sudo systemctl start eplatform-daphne"
    exit 1
fi

# Check if Redis is running
echo "Checking if Redis is running..."
if systemctl is-active --quiet redis; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running"
    echo "Try starting it with: sudo systemctl start redis"
    exit 1
fi

echo ""
echo "Testing HTTP connection..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN")
if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 302 ]; then
    echo "✅ HTTP connection successful (Status: $HTTP_STATUS)"
else
    echo "❌ HTTP connection failed (Status: $HTTP_STATUS)"
    echo "Check Nginx error logs: sudo tail -f /var/log/nginx/error.log"
fi

echo ""
echo "Testing static file access..."
STATIC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/static/css/responsive-utils.css")
if [ "$STATIC_STATUS" -eq 200 ]; then
    echo "✅ Static file access successful"
else
    echo "❌ Static file access failed (Status: $STATIC_STATUS)"
    echo "Check if static files are collected and paths are correct in Nginx config"
fi

echo ""
echo "Testing WebSocket endpoint (basic check)..."
WS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/ws/chat/")
if [ "$WS_STATUS" -eq 400 ] || [ "$WS_STATUS" -eq 426 ] || [ "$WS_STATUS" -eq 101 ]; then
    echo "✅ WebSocket endpoint accessible (Status: $WS_STATUS)"
    echo "   Note: 400/426 is expected for a GET request to a WebSocket endpoint"
else
    echo "❌ WebSocket endpoint check failed (Status: $WS_STATUS)"
    echo "Check Daphne logs: sudo journalctl -u eplatform-daphne"
fi

echo ""
echo "Testing API endpoint..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/api/")
if [ "$API_STATUS" -eq 200 ] || [ "$API_STATUS" -eq 404 ] || [ "$API_STATUS" -eq 403 ]; then
    echo "✅ API endpoint accessible (Status: $API_STATUS)"
    echo "   Note: 404/403 might be expected depending on your API configuration"
else
    echo "❌ API endpoint check failed (Status: $API_STATUS)"
    echo "Check Django logs: sudo journalctl -u eplatform-django"
fi

echo ""
echo "Testing admin interface..."
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/admin/")
if [ "$ADMIN_STATUS" -eq 200 ] || [ "$ADMIN_STATUS" -eq 302 ]; then
    echo "✅ Admin interface accessible (Status: $ADMIN_STATUS)"
else
    echo "❌ Admin interface check failed (Status: $ADMIN_STATUS)"
    echo "Check Django logs: sudo journalctl -u eplatform-django"
fi

echo ""
echo "All tests completed!"
echo ""
echo "For a more comprehensive test, try accessing the application in your browser"
echo "and test the WebSocket functionality (chat, notifications)."
