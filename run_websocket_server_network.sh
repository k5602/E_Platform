#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Add the local IP to ALLOWED_HOSTS temporarily
echo "Your local IP address is: $LOCAL_IP"
echo "Make sure this IP is added to ALLOWED_HOSTS in E_Platform/settings.py"
echo "------------------------------------------------------------"

# Run the Daphne server on all interfaces
echo "Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)..."
echo "This server handles WebSocket connections only."
echo "Keep this terminal window open while using the application."
echo "------------------------------------------------------------"
daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application
