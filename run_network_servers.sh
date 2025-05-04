#!/bin/bash

# Environment variables for WebSocket security configuration
export WEBSOCKET_CSRF_EXEMPT=true
export DJANGO_ALLOW_ASYNC_UNSAFE=true
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

# Check for necessary commands and packages
if ! command -v daphne &> /dev/null; then
    echo "Daphne command not found. Checking if package is installed in virtual environment..."
    
    # Check if we can import daphne in Python
    if ! python -c "import daphne" 2>/dev/null; then
        echo "Daphne package not found. Installing it now..."
        pip install daphne
        
        # Check if installation succeeded
        if ! python -c "import daphne" 2>/dev/null; then
            echo "Error: Failed to install daphne. Please install it manually with:"
            echo "pip install daphne"
            exit 1
        fi
        
        echo "Daphne package installed successfully."
    else
        echo "Daphne package is installed but command is not in path."
        echo "Will use Python module directly."
    fi
fi

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

# Check if ports are already in use
check_port() {
    if command -v lsof &> /dev/null; then
        lsof -i:"$1" &> /dev/null
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -tuln | grep -q ":$1 "
        return $?
    elif command -v ss &> /dev/null; then
        ss -tuln | grep -q ":$1 "
        return $?
    else
        # If no tool is available, assume port is free
        return 1
    fi
}

if check_port 8000; then
    echo "Warning: Port 8000 is already in use. Django server may fail to start."
fi

if check_port 8001; then
    echo "Warning: Port 8001 is already in use. WebSocket server may fail to start."
fi

# Try to use KDE Konsole or GNOME Terminal
if command -v konsole &> /dev/null; then
    # KDE Konsole
    echo "Using KDE Konsole to run both servers..."

    # Create dedicated scripts in a more reliable location
    mkdir -p "${HOME}/.e_platform_scripts"
    DJANGO_SCRIPT="${HOME}/.e_platform_scripts/django_server.sh"
    WS_SCRIPT="${HOME}/.e_platform_scripts/websocket_server.sh"
    
    # Create Django server script
    echo "#!/bin/bash" > $DJANGO_SCRIPT
    echo "cd \"$(pwd)\"" >> $DJANGO_SCRIPT
    echo "source .venv/bin/activate" >> $DJANGO_SCRIPT
    echo "echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\"" >> $DJANGO_SCRIPT
    echo "echo \"This server handles HTTP requests and static files.\"" >> $DJANGO_SCRIPT
    echo "echo \"Keep this terminal window open while using the application.\"" >> $DJANGO_SCRIPT
    echo "echo \"------------------------------------------------------------\"" >> $DJANGO_SCRIPT
    echo "python manage.py runserver 0.0.0.0:8000" >> $DJANGO_SCRIPT
    chmod +x $DJANGO_SCRIPT

    # Create WebSocket server script
    echo "#!/bin/bash" > $WS_SCRIPT
    echo "cd \"$(pwd)\"" >> $WS_SCRIPT
    echo "source .venv/bin/activate" >> $WS_SCRIPT
    echo "echo \"Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...\"" >> $WS_SCRIPT
    echo "echo \"This server handles WebSocket connections only.\"" >> $WS_SCRIPT
    echo "echo \"Keep this terminal window open while using the application.\"" >> $WS_SCRIPT
    echo "echo \"------------------------------------------------------------\"" >> $WS_SCRIPT
    echo "export WEBSOCKET_CSRF_EXEMPT=true" >> $WS_SCRIPT
    echo "export DJANGO_ALLOW_ASYNC_UNSAFE=true" >> $WS_SCRIPT
    echo "if [ -f E_Platform/asgi.py ]; then" >> $WS_SCRIPT
    echo "  if command -v daphne &>/dev/null; then" >> $WS_SCRIPT
    echo "    daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application" >> $WS_SCRIPT
    echo "  else" >> $WS_SCRIPT
    echo "    echo \"Daphne command not found. Using Python module directly...\"" >> $WS_SCRIPT
    echo "    python -m daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application" >> $WS_SCRIPT
    echo "  fi" >> $WS_SCRIPT
    echo "else" >> $WS_SCRIPT
    echo "  echo \"Error: WebSocket server configuration not found!\"" >> $WS_SCRIPT
    echo "  echo \"Could not locate E_Platform/asgi.py\"" >> $WS_SCRIPT
    echo "  echo \"Press Enter to exit...\"" >> $WS_SCRIPT
    echo "  read" >> $WS_SCRIPT
    echo "  exit 1" >> $WS_SCRIPT
    echo "fi" >> $WS_SCRIPT
    chmod +x $WS_SCRIPT
    
    # Launch directly with command rather than script file
    DJANGO_CMD="cd \"$(pwd)\" && source .venv/bin/activate && echo 'Starting Django development server on all interfaces (0.0.0.0:8000)...' && echo 'This server handles HTTP requests and static files.' && echo 'Keep this terminal window open while using the application.' && echo '------------------------------------------------------------' && python manage.py runserver 0.0.0.0:8000"
    
    WS_CMD="cd \"$(pwd)\" && source .venv/bin/activate && echo 'Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...' && echo 'This server handles WebSocket connections only.' && echo 'Keep this terminal window open while using the application.' && echo '------------------------------------------------------------' && export WEBSOCKET_CSRF_EXEMPT=true && export DJANGO_ALLOW_ASYNC_UNSAFE=true && if [ -f E_Platform/asgi.py ]; then if command -v daphne &>/dev/null; then daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; else echo 'Daphne command not found. Using Python module directly...'; python -m daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; fi; else echo 'Error: WebSocket server configuration not found!'; echo 'Press Enter to exit...'; read; fi"

    # Launch both servers in Konsole tabs using direct command execution
    konsole --new-tab --title="Django Server" -e bash -c "$DJANGO_CMD" &
    sleep 1
    konsole --new-tab --title="WebSocket Server" -e bash -c "$WS_CMD" &

    echo "Started servers in KDE Konsole tabs"

    # Open browser on host device
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

elif command -v gnome-terminal &> /dev/null; then
    # GNOME Terminal
    echo "Using GNOME Terminal to run both servers..."

    # Launch Django server in a GNOME Terminal window
    gnome-terminal --title="Django Server" -- bash -c "cd \"$(pwd)\" && source .venv/bin/activate && echo 'Starting Django development server on all interfaces (0.0.0.0:8000)...' && echo 'This server handles HTTP requests and static files.' && echo 'Keep this terminal window open while using the application.' && echo '------------------------------------------------------------' && python manage.py runserver 0.0.0.0:8000; exec bash"
    
    # Launch WebSocket server in another GNOME Terminal window
    gnome-terminal --title="WebSocket Server" -- bash -c "cd \"$(pwd)\" && source .venv/bin/activate && echo 'Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)...' && echo 'This server handles WebSocket connections only.' && echo 'Keep this terminal window open while using the application.' && echo '------------------------------------------------------------' && export WEBSOCKET_CSRF_EXEMPT=true && export DJANGO_ALLOW_ASYNC_UNSAFE=true && if [ -f E_Platform/asgi.py ]; then if command -v daphne &>/dev/null; then daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; else echo 'Daphne command not found. Using Python module directly...'; python -m daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; fi; else echo 'Error: WebSocket server configuration not found!'; fi; exec bash"

    echo "Started servers in GNOME Terminal windows"

    # Open browser on host device
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser on host device..."
        xdg-open "http://localhost:8000" &
    fi

else
    # Fallback mode - no supported terminal found
    echo "Neither KDE Konsole nor GNOME Terminal found."
    echo "Running Django server in the background and WebSocket server in the foreground..."
    echo ""

    # Run Django server directly in the background with error handling
    (cd "$(pwd)" && source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000) > django_server.log 2>&1 &
    DJANGO_PID=$!
    
    # Give Django server a moment to start and check if it's running
    sleep 2
    if ! ps -p $DJANGO_PID > /dev/null; then
        echo "Error: Django server failed to start. Check django_server.log for details."
        cat django_server.log
        exit 1
    fi
    
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
    
    # Check if asgi.py exists before running daphne
    if [ ! -f "E_Platform/asgi.py" ]; then
        echo "Error: WebSocket server configuration (E_Platform/asgi.py) not found!"
        echo "Stopping Django server..."
        kill $DJANGO_PID 2>/dev/null
        exit 1
    fi
    
    # Export environment variables again to ensure they're set in this context
    export WEBSOCKET_CSRF_EXEMPT=true
    export DJANGO_ALLOW_ASYNC_UNSAFE=true
    
    # Run WebSocket server with error handling
    echo "Starting WebSocket server..."
    if command -v daphne &>/dev/null; then
        if ! daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; then
            echo "Error: WebSocket server failed to start with daphne command."
            echo "Trying to run via Python module directly..."
            if ! python -m daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; then
                echo "Error: WebSocket server failed to start."
                echo "Stopping Django server..."
                kill $DJANGO_PID 2>/dev/null
                exit 1
            fi
        fi
    else
        echo "Daphne command not found. Using Python module directly..."
        if ! python -m daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application; then
            echo "Error: WebSocket server failed to start."
            echo "Stopping Django server..."
            kill $DJANGO_PID 2>/dev/null
            exit 1
        fi
    fi
fi

# This part will only be reached if the servers are started in the background
echo ""
echo "Both servers are now running for network testing."
echo "Keep both terminal windows/tabs open while testing."
echo ""

# Print the links again for convenience
print_links "$LOCAL_IP"
