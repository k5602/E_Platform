"""
Test file demonstrating how to use the generate_test_users.py script.

This file serves as both documentation and a test of the script's functionality.
"""

import os
import sys
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the user generation functions
from tests.scripts.generate_test_users import create_test_user, generate_test_users

User = get_user_model()


class TestUserGeneration(TestCase):
    """Test the user generation functions."""

    def test_create_single_user(self):
        """Test creating a single user with specific attributes."""
        # Create a user with specific attributes
        user = create_test_user(
            username='testuser123',
            email='testuser123@example.com',
            password='securepassword456',
            first_name='Test',
            last_name='User',
            user_type='student'
        )

        # Verify the user was created with the correct attributes
        self.assertEqual(user.username, 'testuser123')
        self.assertEqual(user.email, 'testuser123@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.user_type, 'student')

        # Verify the user can authenticate
        self.assertTrue(user.check_password('securepassword456'))

        # Clean up
        user.delete()

    def test_create_user_with_defaults(self):
        """Test creating a user with default random attributes."""
        # Create a user with default random attributes
        user = create_test_user()

        # Verify the user was created
        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.email)
        self.assertIsNotNone(user.first_name)
        self.assertIsNotNone(user.last_name)
        self.assertIsNotNone(user.user_type)
        self.assertIsNotNone(user.birthdate)

        # Verify the user can authenticate with the default password
        self.assertTrue(user.check_password('testpassword123'))

        # Clean up
        user.delete()

    def test_generate_multiple_users(self):
        """Test generating multiple users."""
        # Generate 5 users
        num_users = 5
        users = generate_test_users(num_users=num_users)

        # Verify the correct number of users was created
        self.assertEqual(len(users), num_users)

        # Verify each user has the required attributes
        for user in users:
            self.assertIsNotNone(user.id)
            self.assertIsNotNone(user.username)
            self.assertIsNotNone(user.email)
            self.assertIsNotNone(user.first_name)
            self.assertIsNotNone(user.last_name)
            self.assertIsNotNone(user.user_type)
            self.assertIsNotNone(user.birthdate)

        # Clean up
        for user in users:
            user.delete()

    def test_generate_users_with_specific_type(self):
        """Test generating users with a specific type."""
        # Generate 3 student users
        num_users = 3
        user_type = 'student'
        users = generate_test_users(num_users=num_users, user_types=[user_type])

        # Verify the correct number of users was created
        self.assertEqual(len(users), num_users)

        # Verify each user has the correct type
        for user in users:
            self.assertEqual(user.user_type, user_type)

        # Clean up
        for user in users:
            user.delete()


if __name__ == '__main__':
    unittest.main()
