#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the Daphne server on port 8001
echo "Starting Daphne WebSocket server on port 8001..."
echo "This server handles WebSocket connections only."
echo "Keep this terminal window open while using the application."
echo "------------------------------------------------------------"
daphne -p 8001 E_Platform.asgi:application
