#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Display network information
echo "=========================================================="
echo "NETWORK TESTING SETUP"
echo "=========================================================="
echo "Your local IP address is: $LOCAL_IP"
echo "Other devices should connect to: http://$LOCAL_IP:8000"
echo "Make sure all devices are on the same network"
echo "=========================================================="

# Detect the terminal emulator
if command -v konsole &> /dev/null; then
    # KDE Konsole
    echo "Using KDE Konsole to run both servers..."
    konsole --new-tab --workdir "$(pwd)" -e ./run_django_server_network.sh &
    sleep 1
    konsole --new-tab --workdir "$(pwd)" -e ./run_websocket_server_network.sh &
    echo "Started servers in KDE Konsole tabs"
elif command -v gnome-terminal &> /dev/null; then
    # GNOME Terminal
    echo "Using GNOME Terminal to run both servers..."
    gnome-terminal --tab --working-directory="$(pwd)" -- ./run_django_server_network.sh
    gnome-terminal --tab --working-directory="$(pwd)" -- ./run_websocket_server_network.sh
    echo "Started servers in GNOME Terminal tabs"
elif command -v xfce4-terminal &> /dev/null; then
    # XFCE Terminal
    echo "Using XFCE Terminal to run both servers..."
    xfce4-terminal --tab --working-directory="$(pwd)" -e "./run_django_server_network.sh" &
    xfce4-terminal --tab --working-directory="$(pwd)" -e "./run_websocket_server_network.sh" &
    echo "Started servers in XFCE Terminal tabs"
elif command -v xterm &> /dev/null; then
    # XTerm
    echo "Using XTerm to run both servers..."
    xterm -e "cd $(pwd) && ./run_django_server_network.sh" &
    xterm -e "cd $(pwd) && ./run_websocket_server_network.sh" &
    echo "Started servers in XTerm windows"
elif command -v tmux &> /dev/null; then
    # Tmux as fallback
    echo "Using tmux to run both servers..."
    tmux new-session -d -s e_platform_network
    tmux split-window -h -t e_platform_network
    tmux send-keys -t e_platform_network:0.0 "./run_django_server_network.sh" C-m
    tmux send-keys -t e_platform_network:0.1 "./run_websocket_server_network.sh" C-m
    tmux attach-session -t e_platform_network
else
    # No supported terminal found, provide manual instructions
    echo "No supported terminal emulator found."
    echo "Please run the servers manually in separate terminal windows:"
    echo ""
    echo "Terminal 1: ./run_django_server_network.sh"
    echo "Terminal 2: ./run_websocket_server_network.sh"
    exit 1
fi

echo ""
echo "Both servers are now running for network testing."
echo "Keep both terminal windows/tabs open while testing."
echo ""
echo "On other devices, open a web browser and go to:"
echo "http://$LOCAL_IP:8000"
echo ""
echo "Log in with different user accounts on each device to test the chat."
