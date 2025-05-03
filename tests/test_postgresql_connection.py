"""
Script to test the PostgreSQL connection.
This script attempts to connect to the PostgreSQL database using the
environment variables set in the run_with_postgresql.sh script.
It exits with status code 0 if the connection is successful, and 1 otherwise.
"""

import os
import sys

import psycopg2


def test_postgresql_connection():
    """Test the PostgreSQL connection using environment variables."""
    try:
        # Get database connection parameters from environment variables
        db_name = os.environ.get('DB_NAME', 'e_platform_db')
        db_user = os.environ.get('DB_USER', 'zero')
        db_password = os.environ.get('DB_PASSWORD', '82821931003')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')

        # Attempt to connect to the database
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )

        # If we get here, the connection was successful
        print(f"Successfully connected to PostgreSQL database '{db_name}' as user '{db_user}'")

        # Close the connection
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"Failed to connect to PostgreSQL database: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


if __name__ == "__main__":
    # Run the test and exit with appropriate status code
    if test_postgresql_connection():
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
