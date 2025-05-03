#!/bin/bash

# Check if konsole is installed
if ! command -v konsole &> /dev/null; then
    echo "KDE Konsole is not installed. Please install it or use the separate scripts:"
    echo "./run_django_server.sh in one terminal"
    echo "./run_websocket_server.sh in another terminal"
    exit 1
fi

# Get the current directory
CURRENT_DIR=$(pwd)

# Start Django server in one tab
konsole --new-tab --workdir "$CURRENT_DIR" -e ./run_django_server.sh &

# Wait a moment to ensure the first tab is created
sleep 1

# Start WebSocket server in another tab
konsole --new-tab --workdir "$CURRENT_DIR" -e ./run_websocket_server.sh &

echo "Both servers are now running in separate Konsole tabs."
echo "Keep both tabs open while using the application."
echo "Close the tabs to stop the servers."
