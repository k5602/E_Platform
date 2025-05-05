#!/bin/bash

# Test script for E_Platform Nginx setup
# This script helps verify that your Nginx reverse proxy is working correctly

# Variables - adjust these to match your setup
DOMAIN="your_domain.com"  # Replace with your domain or IP

echo "E_Platform Nginx Test Script"
echo "==========================="

# Test HTTP connection
echo "Testing HTTP connection..."
curl -I "http://$DOMAIN"
echo ""

# Test static files
echo "Testing static file access..."
curl -I "http://$DOMAIN/static/css/responsive-utils.css"
echo ""

# Test WebSocket connection (this is a basic check, not a full test)
echo "Testing WebSocket endpoint (basic check)..."
curl -I "http://$DOMAIN/ws/chat/"
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

echo "Test complete!"
echo "For a more thorough WebSocket test, please use the browser console and check WebSocket connections."
