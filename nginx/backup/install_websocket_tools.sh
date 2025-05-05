#!/bin/bash
# Script to install WebSocket testing tools

# Print colored messages
print_info() {
    echo -e "\e[1;34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1"
}

print_warning() {
    echo -e "\e[1;33m[WARNING]\e[0m $1"
}

print_header() {
    echo -e "\n\e[1;36m=== $1 ===\e[0m"
}

# Define paths
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
VENV_DIR="$PROJECT_DIR/.venv"

print_header "INSTALLING WEBSOCKET TOOLS"

# Check if running as root for system-wide tools
if [ "$EUID" -eq 0 ]; then
    print_info "Installing system-wide WebSocket tools..."
    
    # Detect package manager
    if command -v pacman &> /dev/null; then
        # Arch Linux
        print_info "Detected Arch Linux, using pacman..."
        pacman -Sy --noconfirm websocat
    elif command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        print_info "Detected Debian/Ubuntu, using apt..."
        apt-get update
        apt-get install -y websocat
    elif command -v dnf &> /dev/null; then
        # Fedora/RHEL
        print_info "Detected Fedora/RHEL, using dnf..."
        dnf install -y websocat
    else
        print_warning "Could not determine package manager. Installing websocat from cargo..."
        if ! command -v cargo &> /dev/null; then
            print_info "Installing Rust and Cargo..."
            curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            source $HOME/.cargo/env
        fi
        cargo install websocat
    fi
else
    print_warning "Not running as root. Skipping system-wide tool installation."
    print_info "To install system-wide tools, run this script with sudo."
fi

print_header "INSTALLING PYTHON WEBSOCKET CLIENT"

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    print_info "Installing websockets package in virtual environment..."
    source "$VENV_DIR/bin/activate"
    pip install websockets
    deactivate
    print_success "Installed websockets package in virtual environment"
else
    print_warning "Virtual environment not found at $VENV_DIR"
    print_info "Installing websockets package for current user..."
    pip install --user websockets
fi

print_header "SETTING UP TEST FILES"

# Make Python client executable
chmod +x "$PROJECT_DIR/nginx/websocket_client.py"

# Copy WebSocket test HTML to static files
mkdir -p "$PROJECT_DIR/staticfiles"
cp "$PROJECT_DIR/nginx/websocket_test.html" "$PROJECT_DIR/staticfiles/"

print_success "WebSocket test HTML copied to staticfiles directory"
print_info "You can access it at: http://localhost/static/websocket_test.html"

print_header "USAGE INSTRUCTIONS"

echo "1. Test WebSocket connection with Python client:"
echo "   python nginx/websocket_client.py ws://localhost/ws/notifications/1/"
echo
echo "2. Test WebSocket connection with websocat (if installed):"
echo "   websocat ws://localhost/ws/notifications/1/"
echo
echo "3. Test WebSocket connection with browser:"
echo "   Open http://localhost/static/websocket_test.html in your browser"
echo
echo "4. If you need to modify the WebSocket URL, edit it in the browser interface"

exit 0
