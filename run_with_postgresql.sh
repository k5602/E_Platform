#!/bin/bash

# Script to run the E-Platform application with PostgreSQL and WebSockets
# This script sets the necessary environment variables to use PostgreSQL
# and then runs both the Django server and the Daphne WebSocket server

# Set environment variables for PostgreSQL
export DB_ENGINE=postgresql
export DB_NAME=e_platform_db
export DB_USER=zero
export DB_PASSWORD=82821931003
export DB_HOST=localhost
export DB_PORT=5432

# Check if PostgreSQL is running
echo "Checking if PostgreSQL is running..."
if pg_isready -h $DB_HOST -p $DB_PORT > /dev/null 2>&1; then
    echo "PostgreSQL is running."
else
    echo "PostgreSQL is not running. Please start the PostgreSQL service."
    echo "You can start PostgreSQL with: sudo systemctl start postgresql"
    exit 1
fi

# Create the database and user if they don't exist
echo "Creating database and user if they don't exist..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database $DB_NAME already exists."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User $DB_USER already exists."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || echo "Privileges already granted."

# Create logs directory if it doesn't exist
mkdir -p logs

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Create a temporary script for the Django server
DJANGO_SCRIPT=$(mktemp)
echo "#!/bin/bash" > $DJANGO_SCRIPT
echo "cd $(pwd)" >> $DJANGO_SCRIPT
echo "export DB_ENGINE=postgresql" >> $DJANGO_SCRIPT
echo "export DB_NAME=e_platform_db" >> $DJANGO_SCRIPT
echo "export DB_USER=zero" >> $DJANGO_SCRIPT
echo "export DB_PASSWORD=82821931003" >> $DJANGO_SCRIPT
echo "export DB_HOST=localhost" >> $DJANGO_SCRIPT
echo "export DB_PORT=5432" >> $DJANGO_SCRIPT
echo "echo \"Starting Django development server on all interfaces (0.0.0.0:8000)...\"" >> $DJANGO_SCRIPT
echo "echo \"This server handles HTTP requests and static files.\"" >> $DJANGO_SCRIPT
echo "echo \"Keep this terminal window open while using the application.\"" >> $DJANGO_SCRIPT
echo "echo \"------------------------------------------------------------\"" >> $DJANGO_SCRIPT
echo "python manage.py runserver 0.0.0.0:8000" >> $DJANGO_SCRIPT
chmod +x $DJANGO_SCRIPT

# Run Django server in the background
$DJANGO_SCRIPT > logs/django_server.log 2>&1 &
DJANGO_PID=$!
echo "Django server started in background (PID: $DJANGO_PID)"
echo "Log file: $(pwd)/logs/django_server.log"
echo ""

# Set up trap to kill Django server when the script exits
trap "kill $DJANGO_PID 2>/dev/null; echo 'Servers stopped.'; exit" INT TERM EXIT

# Run WebSocket server in the foreground
echo "Starting Daphne WebSocket server on all interfaces (0.0.0.0:8001)..."
echo "This server handles WebSocket connections only."
echo "Keep this terminal window open while using the application."
echo "------------------------------------------------------------"
daphne -b 0.0.0.0 -p 8001 E_Platform.asgi:application
