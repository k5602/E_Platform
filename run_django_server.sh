#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run Django development server on port 8000
echo "Starting Django development server on port 8000..."
echo "This server handles HTTP requests and static files."
echo "Keep this terminal window open while using the application."
echo "------------------------------------------------------------"
python manage.py runserver
