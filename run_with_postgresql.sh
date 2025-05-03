#!/bin/bash

# Script to run the E-Platform application with PostgreSQL
# This script sets the necessary environment variables to use PostgreSQL
# and then runs the application

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

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Run the server
echo "Starting the server..."
python manage.py runserver