#!/bin/bash

# Get the current directory
CURRENT_DIR=$(pwd)

# Detect the terminal emulator
if command -v konsole &> /dev/null; then
    # KDE Konsole
    konsole --new-tab --workdir "$CURRENT_DIR" -e ./run_django_server.sh &
    sleep 1
    konsole --new-tab --workdir "$CURRENT_DIR" -e ./run_websocket_server.sh &
    echo "Started servers in KDE Konsole tabs"
elif command -v gnome-terminal &> /dev/null; then
    # GNOME Terminal
    gnome-terminal --tab --working-directory="$CURRENT_DIR" -- ./run_django_server.sh
    gnome-terminal --tab --working-directory="$CURRENT_DIR" -- ./run_websocket_server.sh
    echo "Started servers in GNOME Terminal tabs"
elif command -v xfce4-terminal &> /dev/null; then
    # XFCE Terminal
    xfce4-terminal --tab --working-directory="$CURRENT_DIR" -e "./run_django_server.sh" &
    xfce4-terminal --tab --working-directory="$CURRENT_DIR" -e "./run_websocket_server.sh" &
    echo "Started servers in XFCE Terminal tabs"
elif command -v xterm &> /dev/null; then
    # XTerm
    xterm -e "cd $CURRENT_DIR && ./run_django_server.sh" &
    xterm -e "cd $CURRENT_DIR && ./run_websocket_server.sh" &
    echo "Started servers in XTerm windows"
elif command -v tmux &> /dev/null; then
    # Tmux as fallback
    echo "Using tmux to run both servers..."
    tmux new-session -d -s e_platform
    tmux split-window -h -t e_platform
    tmux send-keys -t e_platform:0.0 "cd $CURRENT_DIR && ./run_django_server.sh" C-m
    tmux send-keys -t e_platform:0.1 "cd $CURRENT_DIR && ./run_websocket_server.sh" C-m
    tmux attach-session -t e_platform
else
    # No supported terminal found
    echo "No supported terminal emulator found."
    echo "Please run the servers manually in separate terminal windows:"
    echo ""
    echo "Terminal 1: ./run_django_server.sh"
    echo "Terminal 2: ./run_websocket_server.sh"
    exit 1
fi

echo "Both servers are now running."
echo "Keep both terminal windows/tabs open while using the application."
