"""
Script to initialize migration directories for all Django apps in the project.
This script should be run after cloning the repository and before running migrations.
It ensures that all necessary migration directories exist and creates empty __init__.py files
to make them proper Python packages.
"""

import os
from pathlib import Path


def create_migration_directory(app_path):
    """Create a migrations directory for the given app if it doesn't exist."""
    migrations_dir = os.path.join(app_path, 'migrations')

    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
        print(f"Created migrations directory for {os.path.basename(app_path)}")

    # Create __init__.py file to make it a proper Python package
    init_file = os.path.join(migrations_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass  # Create an empty file
        print(f"Created __init__.py in migrations directory for {os.path.basename(app_path)}")


def main():
    """Main function to initialize migration directories for all apps."""
    # Get the base directory of the project
    base_dir = Path(__file__).resolve().parent

    # List of app directories to check
    app_dirs = [
        os.path.join(base_dir, 'authentication'),
        os.path.join(base_dir, 'home'),
        os.path.join(base_dir, 'chatting'),
        os.path.join(base_dir, 'Ai_prototype')
    ]

    # Create migration directories for each app
    for app_dir in app_dirs:
        if os.path.isdir(app_dir):
            create_migration_directory(app_dir)

    print("\nMigration directories have been initialized.")
    print("You can now run 'python manage.py makemigrations' followed by 'python manage.py migrate'")


if __name__ == "__main__":
    main()
