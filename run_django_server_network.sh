#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Add the local IP to ALLOWED_HOSTS temporarily
echo "Your local IP address is: $LOCAL_IP"
echo "Make sure this IP is added to ALLOWED_HOSTS in E_Platform/settings.py"
echo "------------------------------------------------------------"

# Run Django development server on all interfaces
echo "Starting Django development server on all interfaces (0.0.0.0:8000)..."
echo "This server handles HTTP requests and static files."
echo "Keep this terminal window open while using the application."
echo "------------------------------------------------------------"
python manage.py runserver 0.0.0.0:8000
