#!/usr/bin/env python
"""
Example script demonstrating how to use the generate_test_users.py script.

This script generates a set of example users for testing purposes:
- 5 students
- 3 instructors
- 2 admin users

Usage:
    python tests/scripts/examples/generate_example_users.py
"""

import os
import sys

import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

# Import the user generation functions
from tests.scripts.generate_test_users import create_test_user, generate_test_users


def main():
    """Generate example users for testing."""
    print("Generating example users for testing...")

    # Generate 5 student users
    print("\nGenerating 5 student users:")
    students = generate_test_users(num_users=5, user_types=['student'])

    # Generate 3 instructor users
    print("\nGenerating 3 instructor users:")
    instructors = generate_test_users(num_users=3, user_types=['instructor'])

    # Generate 2 admin users
    print("\nGenerating 2 admin users:")
    admins = generate_test_users(num_users=2, user_types=['admin'])

    # Create a specific user for testing
    print("\nCreating a specific user for testing:")
    test_user = create_test_user(
        username='testadmin',
        email='testadmin@example.com',
        password='admin123',
        first_name='Test',
        last_name='Admin',
        user_type='admin',
        is_staff=True,
        is_superuser=True
    )
    print(f"Created user: {test_user.username} ({test_user.user_type})")

    # Print summary
    all_users = students + instructors + admins + [test_user]
    print(f"\nSuccessfully created {len(all_users)} test users.")
    print("User details:")
    for user in all_users:
        print(f"  - {user.username}: {user.first_name} {user.last_name} ({user.user_type})")

    print("\nYou can now log in with any of these users.")
    print("For the specific test admin user:")
    print("  Username: testadmin")
    print("  Password: admin123")
    print("\nFor all other users, the default password is: testpassword123")


if __name__ == '__main__':
    main()
