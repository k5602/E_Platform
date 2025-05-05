#!/bin/bash
# Script to collect static files for E_Platform

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

# Define paths
PROJECT_DIR="/mnt/4BC9EBFC28ECC8F5/Others/Projects/E_Platform"
STATIC_DIR="$PROJECT_DIR/staticfiles"

# Create staticfiles directory if it doesn't exist
print_info "Creating staticfiles directory if it doesn't exist..."
mkdir -p "$STATIC_DIR"

# Activate virtual environment and collect static files
print_info "Activating virtual environment and collecting static files..."
cd "$PROJECT_DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    print_error "Virtual environment not found. Please create it first."
    exit 1
fi

# Check if Django is installed
if ! python -c "import django" &> /dev/null; then
    print_error "Django is not installed in the virtual environment."
    exit 1
fi

# Collect static files
print_info "Running collectstatic command..."
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    print_success "Static files collected successfully!"
    
    # Set permissions
    print_info "Setting permissions..."
    chmod -R 755 "$STATIC_DIR"
    
    # Count collected files
    file_count=$(find "$STATIC_DIR" -type f | wc -l)
    print_info "Collected $file_count static files in $STATIC_DIR"
    
    # List some CSS files for verification
    css_files=$(find "$STATIC_DIR" -name "*.css" -type f | head -n 5)
    if [ -n "$css_files" ]; then
        print_info "Found CSS files:"
        echo "$css_files"
    else
        print_info "No CSS files found. This might be an issue."
    fi
else
    print_error "Failed to collect static files."
    exit 1
fi

print_success "Static files setup complete!"
exit 0
