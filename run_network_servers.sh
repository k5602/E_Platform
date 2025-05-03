#!/bin/bash

# Display help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --ip IP_ADDRESS    Specify the IP address manually"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --ip 192.168.1.100  Use 192.168.1.100 as the IP address"
    echo ""
}

# Parse command line arguments
MANUAL_IP=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--ip)
            MANUAL_IP="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to print clickable links
print_links() {
    local ip=$1

    # Check if we're in a terminal that supports ANSI escape sequences
    if [ -t 1 ] && [ -n "$TERM" ] && [ "$TERM" != "dumb" ]; then
        # ANSI escape codes for colors and formatting
        local BLUE='\033[0;34m'
        local GREEN='\033[0;32m'
        local YELLOW='\033[1;33m'
        local BOLD='\033[1m'
        local UNDERLINE='\033[4m'
        local NC='\033[0m' # No Color

        echo -e "\n${BOLD}=== CLICKABLE LINKS ===${NC}"
        echo -e "\n${BOLD}For this device (host):${NC}"
        echo -e "${BLUE}${UNDERLINE}http://localhost:8000${NC}"

        echo -e "\n${BOLD}For other devices on the network:${NC}"
        echo -e "${GREEN}${UNDERLINE}http://$ip:8000${NC}"

        echo -e "\n${YELLOW}Copy and send this link to other devices to test chat functionality${NC}\n"
    else
        # Plain text version for terminals that don't support ANSI
        echo ""
        echo "=== LINKS ==="
        echo ""
        echo "For this device (host):"
        echo "http://localhost:8000"

        echo ""
        echo "For other devices on the network:"
        echo "http://$ip:8000"

        echo ""
        echo "Copy and send this link to other devices to test chat functionality"
        echo ""
    fi
}

# Activate the virtual environment for the main script
source .venv/bin/activate

# Get the local IP address using multiple methods
get_ip() {
    # Method 1: hostname -I (most common)
    local ip1=$(hostname -I 2>/dev/null | awk '{print $1}')

    # Method 2: ip command
    local ip2=$(ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1)

    # Method 3: ifconfig command
    local ip3=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1)

    # Method 4: Using a specific interface (try common ones)
    for interface in eth0 wlan0 enp0s3 enp0s8 ens33 wlp2s0; do
        local ip4=$(ip -4 addr show $interface 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        if [ -n "$ip4" ]; then
            break
        fi
    done

    # Return the first non-empty IP
    if [ -n "$ip1" ]; then
        echo "$ip1"
    elif [ -n "$ip2" ]; then
        echo "$ip2"
    elif [ -n "$ip3" ]; then
        echo "$ip3"
    elif [ -n "$ip4" ]; then
        echo "$ip4"
    else
        echo "127.0.0.1"  # Fallback to localhost if no IP is found
        echo "Warning: Could not detect your network IP. Other devices may not be able to connect." >&2
        echo "Please check your network connection and try again." >&2
    fi
}

# Check if IP was provided as command-line argument
if [ -n "$MANUAL_IP" ]; then
    # Validate the provided IP
    if [[ $MANUAL_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        LOCAL_IP=$MANUAL_IP
        echo "Using provided IP address: $LOCAL_IP"
    else
        echo "Invalid IP format provided. Will try to detect automatically."
        MANUAL_IP=""
    fi
else
    # Get the local IP address automatically
    LOCAL_IP=$(get_ip)

    # Check if the IP is localhost, which indicates detection failure
    if [ "$LOCAL_IP" = "127.0.0.1" ]; then
        echo "=========================================================="
        echo "IP ADDRESS DETECTION FAILED"
        echo "=========================================================="
        echo "Could not automatically detect your network IP address."
        echo "Please enter your network IP address manually."
        echo "You can find it by running 'ip addr' or 'ifconfig' in another terminal."
        echo "It should look like 192.168.x.x or 10.0.x.x"
        echo ""
        echo "Tip: Next time, you can specify the IP directly when running the script:"
        echo "     ./run_network_servers.sh --ip YOUR_IP_ADDRESS"
        echo "=========================================================="

        # Prompt for manual IP entry
        read -p "Enter your network IP address: " MANUAL_IP

        # Validate the entered IP
        if [[ $MANUAL_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            LOCAL_IP=$MANUAL_IP
            echo "Using manually entered IP: $LOCAL_IP"
        else
            echo "Invalid IP format. Using localhost (127.0.0.1) as fallback."
            echo "Note: Other devices will not be able to connect using this IP."
            LOCAL_IP="127.0.0.1"
        fi
    fi
fi

# Display network information
echo "=========================================================="
echo "NETWORK TESTING SETUP"
echo "=========================================================="
echo "Your local IP address is: $LOCAL_IP"
echo "Other devices should connect to: http://$LOCAL_IP:8000"
echo "Make sure all devices are on the same network"
echo "=========================================================="

# Print clickable links
print_links "$LOCAL_IP"

# Prioritize KDE Konsole and GNOME Terminal
if command -v konsole &> /dev/null; then
    # KDE Konsole
    echo "Using KDE Konsole to run both servers..."

    # Create a temporary script for Django server
    DJANGO_SCRIPT=$(mktemp)
    echo "#!/bin/bash" > $DJANGO_SCRIPT
    echo "cd $(pwd)" >> $DJANGO_SCRIPT
    echo "source .venv/bin/activate" >> $DJANGO_SCRIPT
    echo "echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\"" >> $DJANGO_SCRIPT
    echo "echo \"This server handles HTTP requests and static files.\"" >> $DJANGO_SCRIPT
    echo "echo \"Keep this terminal window open while using the application.\"" >> $DJANGO_SCRIPT
    echo "echo \"------------------------------------------------------------\"" >> $DJANGO_SCRIPT
    echo "python manage.py runserver 0.0.0.0:8000" >> $DJANGO_SCRIPT
    chmod +x $DJANGO_SCRIPT

    # Create a temporary script for WebSocket server
    WS_SCRIPT=$(mktemp)
    echo "#!/bin/bash" > $WS_SCRIPT
    echo "cd $(pwd)" >> $WS_SCRIPT
    echo "source .venv/bin/activate" >> $WS_SCRIPT
    echo "echo \"Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...\"" >> $WS_SCRIPT
    echo "echo \"This server handles WebSocket connections only.\"" >> $WS_SCRIPT
    echo "echo \"Keep this terminal window open while using the application.\"" >> $WS_SCRIPT
    echo "echo \"------------------------------------------------------------\"" >> $WS_SCRIPT
    echo "daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application" >> $WS_SCRIPT
    chmod +x $WS_SCRIPT

    # Launch both servers in Konsole tabs
    konsole --new-tab --title="Django Server" --workdir "$(pwd)" -e $DJANGO_SCRIPT &
    sleep 1
    konsole --new-tab --title="WebSocket Server" --workdir "$(pwd)" -e $WS_SCRIPT &

    echo "Started servers in KDE Konsole tabs"

    # Open browser on host device
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

elif command -v gnome-terminal &> /dev/null; then
    # GNOME Terminal
    echo "Using GNOME Terminal to run both servers..."

    # Create command strings with echo statements
    DJANGO_CMD="cd $(pwd) && source .venv/bin/activate && echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\" && echo \"This server handles HTTP requests and static files.\" && echo \"Keep this terminal window open while using the application.\" && echo \"------------------------------------------------------------\" && python manage.py runserver 0.0.0.0:8000"
    WS_CMD="cd $(pwd) && source .venv/bin/activate && echo \"Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...\" && echo \"This server handles WebSocket connections only.\" && echo \"Keep this terminal window open while using the application.\" && echo \"------------------------------------------------------------\" && daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application"

    # Launch both servers in GNOME Terminal tabs
    gnome-terminal --tab --title="Django Server" -- bash -c "$DJANGO_CMD"
    gnome-terminal --tab --title="WebSocket Server" -- bash -c "$WS_CMD"

    echo "Started servers in GNOME Terminal tabs"

    # Open browser on host device
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

elif command -v tmux &> /dev/null; then
    # Tmux as third option
    echo "Using tmux to run both servers..."

    # Create a new tmux session
    tmux new-session -d -s e_platform_network

    # Split the window horizontally
    tmux split-window -h -t e_platform_network

    # Send commands to run the Django server in the left pane
    tmux send-keys -t e_platform_network:0.0 "cd $(pwd)" C-m
    tmux send-keys -t e_platform_network:0.0 "source .venv/bin/activate" C-m
    tmux send-keys -t e_platform_network:0.0 "echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\"" C-m
    tmux send-keys -t e_platform_network:0.0 "echo \"This server handles HTTP requests and static files.\"" C-m
    tmux send-keys -t e_platform_network:0.0 "echo \"Keep this terminal window open while using the application.\"" C-m
    tmux send-keys -t e_platform_network:0.0 "echo \"------------------------------------------------------------\"" C-m
    tmux send-keys -t e_platform_network:0.0 "python manage.py runserver 0.0.0.0:8000" C-m

    # Send commands to run the WebSocket server in the right pane
    tmux send-keys -t e_platform_network:0.1 "cd $(pwd)" C-m
    tmux send-keys -t e_platform_network:0.1 "source .venv/bin/activate" C-m
    tmux send-keys -t e_platform_network:0.1 "echo \"Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...\"" C-m
    tmux send-keys -t e_platform_network:0.1 "echo \"This server handles WebSocket connections only.\"" C-m
    tmux send-keys -t e_platform_network:0.1 "echo \"Keep this terminal window open while using the application.\"" C-m
    tmux send-keys -t e_platform_network:0.1 "echo \"------------------------------------------------------------\"" C-m
    tmux send-keys -t e_platform_network:0.1 "daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application" C-m

    # Open browser in background if possible
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

    # Attach to the tmux session
    tmux attach-session -t e_platform_network

elif command -v xfce4-terminal &> /dev/null; then
    # XFCE Terminal
    echo "Using XFCE Terminal to run both servers..."

    # Create temporary scripts
    DJANGO_SCRIPT=$(mktemp)
    echo "#!/bin/bash" > $DJANGO_SCRIPT
    echo "cd $(pwd)" >> $DJANGO_SCRIPT
    echo "source .venv/bin/activate" >> $DJANGO_SCRIPT
    echo "echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\"" >> $DJANGO_SCRIPT
    echo "echo \"This server handles HTTP requests and static files.\"" >> $DJANGO_SCRIPT
    echo "echo \"Keep this terminal window open while using the application.\"" >> $DJANGO_SCRIPT
    echo "echo \"------------------------------------------------------------\"" >> $DJANGO_SCRIPT
    echo "python manage.py runserver 0.0.0.0:8000" >> $DJANGO_SCRIPT
    chmod +x $DJANGO_SCRIPT

    WS_SCRIPT=$(mktemp)
    echo "#!/bin/bash" > $WS_SCRIPT
    echo "cd $(pwd)" >> $WS_SCRIPT
    echo "source .venv/bin/activate" >> $WS_SCRIPT
    echo "echo \"Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...\"" >> $WS_SCRIPT
    echo "echo \"This server handles WebSocket connections only.\"" >> $WS_SCRIPT
    echo "echo \"Keep this terminal window open while using the application.\"" >> $WS_SCRIPT
    echo "echo \"------------------------------------------------------------\"" >> $WS_SCRIPT
    echo "daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application" >> $WS_SCRIPT
    chmod +x $WS_SCRIPT

    # Launch both servers in XFCE Terminal tabs
    xfce4-terminal --tab --title="Django Server" -e "$DJANGO_SCRIPT" &
    xfce4-terminal --tab --title="WebSocket Server" -e "$WS_SCRIPT" &

    echo "Started servers in XFCE Terminal tabs"

    # Open browser on host device
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

elif command -v xterm &> /dev/null; then
    # XTerm
    echo "Using XTerm to run both servers..."

    # Create command strings
    DJANGO_CMD="cd $(pwd) && source .venv/bin/activate && echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\" && echo \"This server handles HTTP requests and static files.\" && echo \"Keep this terminal window open while using the application.\" && echo \"------------------------------------------------------------\" && python manage.py runserver 0.0.0.0:8000"
    WS_CMD="cd $(pwd) && source .venv/bin/activate && echo \"Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...\" && echo \"This server handles WebSocket connections only.\" && echo \"Keep this terminal window open while using the application.\" && echo \"------------------------------------------------------------\" && daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application"

    # Launch both servers in XTerm windows
    xterm -title "Django Server" -e "bash -c '$DJANGO_CMD'" &
    xterm -title "WebSocket Server" -e "bash -c '$WS_CMD'" &

    echo "Started servers in XTerm windows"

    # Open browser on host device
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

else
    # No supported terminal found, run in foreground/background
    echo "No supported terminal emulator found."
    echo "Running Django server in the background and WebSocket server in the foreground..."
    echo ""

    # Create a temporary script for the Django server
    DJANGO_SCRIPT=$(mktemp)
    echo "#!/bin/bash" > $DJANGO_SCRIPT
    echo "cd $(pwd)" >> $DJANGO_SCRIPT
    echo "source .venv/bin/activate" >> $DJANGO_SCRIPT
    echo "python manage.py runserver 0.0.0.0:8000" >> $DJANGO_SCRIPT
    chmod +x $DJANGO_SCRIPT

    # Run Django server in the background
    $DJANGO_SCRIPT > django_server.log 2>&1 &
    DJANGO_PID=$!
    echo "Django server started in background (PID: $DJANGO_PID)"
    echo "Log file: $(pwd)/django_server.log"
    echo ""
    echo "Press Ctrl+C to stop both servers when done"
    echo ""

    # Open browser on host device if possible
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

    # Set up trap to kill Django server when the script exits
    trap "kill $DJANGO_PID 2>/dev/null; echo 'Servers stopped.'; exit" INT TERM EXIT

    # Run WebSocket server in the foreground
    source .venv/bin/activate
    echo "Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)..."
    echo "This server handles WebSocket connections only."
    echo "Keep this terminal window open while using the application."
    echo "------------------------------------------------------------"
    daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application
fi

# This part will only be reached if the servers are started in the background
echo ""
echo "Both servers are now running for network testing."
echo "Keep both terminal windows/tabs open while testing."
echo ""

# Print the links again for convenience
print_links "$LOCAL_IP"
