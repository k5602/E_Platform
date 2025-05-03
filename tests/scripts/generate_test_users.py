#!/usr/bin/env python
"""
Script to generate test users for the E-Platform project.

This script provides functions to create test users with various attributes
for testing purposes. It can be run directly or imported and used in other tests.

Usage:
    python tests/scripts/generate_test_users.py [num_users] [--student] [--instructor] [--admin]

Examples:
    # Generate 5 users of random types
    python tests/scripts/generate_test_users.py 5
    
    # Generate 3 student users
    python tests/scripts/generate_test_users.py 3 --student
    
    # Generate 2 instructor users and 1 admin user
    python tests/scripts/generate_test_users.py 3 --instructor --admin
"""

import argparse
import os
import random
import sys
from datetime import datetime, timedelta

import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

# Now we can import Django models
from django.contrib.auth import get_user_model

User = get_user_model()

# Sample data for generating users
FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
    'Matthew', 'Margaret', 'Anthony', 'Betty', 'Mark', 'Sandra', 'Donald', 'Ashley',
    'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
    'Kenneth', 'Dorothy', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa',
    'Edward', 'Deborah', 'Ronald', 'Stephanie', 'Timothy', 'Rebecca', 'Jason', 'Sharon'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson',
    'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin',
    'Thompson', 'Garcia', 'Martinez', 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee',
    'Walker', 'Hall', 'Allen', 'Young', 'Hernandez', 'King', 'Wright', 'Lopez',
    'Hill', 'Scott', 'Green', 'Adams', 'Baker', 'Gonzalez', 'Nelson', 'Carter',
    'Mitchell', 'Perez', 'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans',
    'Edwards', 'Collins', 'Stewart', 'Sanchez', 'Morris', 'Rogers', 'Reed', 'Cook'
]

DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'example.com', 'test.com']


def generate_random_date(start_year=1970, end_year=2000):
    """Generate a random date between start_year and end_year."""
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)


def create_test_user(
        username=None,
        email=None,
        password='testpassword123',
        first_name=None,
        last_name=None,
        user_type=None,
        birthdate=None,
        profile_picture=None,
        is_staff=False,
        is_superuser=False
):
    """
    Create a test user with the given parameters.
    
    Args:
        username (str, optional): Username for the user. If None, a random username will be generated.
        email (str, optional): Email for the user. If None, a random email will be generated.
        password (str, optional): Password for the user. Defaults to 'testpassword123'.
        first_name (str, optional): First name for the user. If None, a random first name will be generated.
        last_name (str, optional): Last name for the user. If None, a random last name will be generated.
        user_type (str, optional): Type of user ('student', 'instructor', or 'admin'). 
                                  If None, a random type will be assigned.
        birthdate (datetime, optional): Birthdate for the user. If None, a random date will be generated.
        profile_picture (File, optional): Profile picture for the user. If None, no picture will be assigned.
        is_staff (bool, optional): Whether the user is staff. Defaults to False.
        is_superuser (bool, optional): Whether the user is a superuser. Defaults to False.
        
    Returns:
        User: The created user object.
    """
    # Generate random values for any parameters that weren't provided
    if first_name is None:
        first_name = random.choice(FIRST_NAMES)

    if last_name is None:
        last_name = random.choice(LAST_NAMES)

    if username is None:
        # Create a username based on first and last name with a random number
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        random_number = random.randint(1, 9999)
        username = f"{base_username}{random_number}"

        # Make sure the username is unique
        while User.objects.filter(username=username).exists():
            random_number = random.randint(1, 9999)
            username = f"{base_username}{random_number}"

    if email is None:
        # Create an email based on the username
        domain = random.choice(DOMAINS)
        email = f"{username}@{domain}"

    if user_type is None:
        user_type = random.choice(['student', 'instructor', 'admin'])

    if birthdate is None:
        # Generate a random birthdate for an adult (18-60 years old)
        current_year = datetime.now().year
        birthdate = generate_random_date(current_year - 60, current_year - 18)

    # Create the user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        user_type=user_type,
        birthdate=birthdate,
        is_staff=is_staff or user_type == 'admin',
        is_superuser=is_superuser or user_type == 'admin'
    )

    # Add profile picture if provided
    if profile_picture:
        user.profile_picture = profile_picture
        user.save()

    return user


def generate_test_users(num_users=10, user_types=None):
    """
    Generate multiple test users.
    
    Args:
        num_users (int, optional): Number of users to generate. Defaults to 10.
        user_types (list, optional): List of user types to generate. If None, random types will be assigned.
                                    Example: ['student', 'instructor', 'admin']
        
    Returns:
        list: List of created user objects.
    """
    users = []

    for i in range(num_users):
        # Determine user type
        user_type = None
        if user_types:
            user_type = random.choice(user_types)

        # Create a user
        user = create_test_user(user_type=user_type)
        users.append(user)

        print(f"Created user: {user.username} ({user.user_type})")

    return users


def main():
    """Main function to run when script is executed directly."""
    parser = argparse.ArgumentParser(description='Generate test users for the E-Platform project.')
    parser.add_argument('num_users', type=int, nargs='?', default=10,
                        help='Number of users to generate (default: 10)')
    parser.add_argument('--student', action='store_true', help='Generate student users')
    parser.add_argument('--instructor', action='store_true', help='Generate instructor users')
    parser.add_argument('--admin', action='store_true', help='Generate admin users')

    args = parser.parse_args()

    # Determine which user types to generate
    user_types = []
    if args.student:
        user_types.append('student')
    if args.instructor:
        user_types.append('instructor')
    if args.admin:
        user_types.append('admin')

    # If no specific types were requested, use all types
    if not user_types:
        user_types = ['student', 'instructor', 'admin']

    print(f"Generating {args.num_users} users with types: {', '.join(user_types)}")

    # Generate the users
    users = generate_test_users(args.num_users, user_types)

    print(f"\nSuccessfully created {len(users)} test users.")
    print("User details:")
    for user in users:
        print(f"  - {user.username}: {user.first_name} {user.last_name} ({user.user_type})")


if __name__ == '__main__':
    main()
