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

# Display banner
echo "========================================================"
echo "  E-Platform PostgreSQL Setup and Launch Script"
echo "========================================================"

# Check if PostgreSQL is running
echo "Checking if PostgreSQL is running..."
if pg_isready -h $DB_HOST -p $DB_PORT > /dev/null 2>&1; then
    echo "✓ PostgreSQL is running."
else
    echo "✗ PostgreSQL is not running. Please start the PostgreSQL service."
    echo "  You can start PostgreSQL with: sudo systemctl start postgresql"
    exit 1
fi

# Create the database and user if they don't exist
echo -e "\nSetting up database and permissions..."
echo "- Creating database and user if they don't exist"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "  → Database $DB_NAME already exists."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "  → User $DB_USER already exists."

# Make user the database owner
echo "- Setting database ownership"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;" 2>/dev/null

# Set up proper schema permissions to avoid "permission denied for schema public" errors
echo "- Setting up schema permissions"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null

# Grant privileges on all tables, sequences, and functions
echo "- Granting privileges on database objects"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;" 2>/dev/null

# Set default privileges for future objects
echo "- Setting default privileges for future objects"
sudo -u postgres psql -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;" 2>/dev/null

echo "✓ Database setup complete!"

# Test database connection
echo -e "\nTesting database connection..."
python tests/test_postgresql_connection.py
if [ $? -eq 0 ]; then
    echo "✓ Database connection successful!"
else
    echo "✗ Database connection failed. Please check your database settings."
    exit 1
fi

# Initialize migrations
echo -e "\nInitializing migrations..."
python initialize_migrations.py

# Create migrations
echo -e "\nCreating migrations..."
python manage.py makemigrations

# Apply migrations
echo -e "\nApplying migrations..."
python manage.py migrate

# Run the server
echo -e "\nStarting the server..."
python manage.py runserver
