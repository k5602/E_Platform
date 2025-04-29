#!/usr/bin/env python
"""
Test script for the E-Platform REST API.
This script tests the main API endpoints to ensure they are working correctly.
"""

import requests
import json
import sys

# Base URL for the API
BASE_URL = 'http://localhost:8000'

# Headers for API requests
headers = {
    'Content-Type': 'application/json',
}

# Authentication token
auth_token = None


def print_response(response, label=None):
    """Print the response from an API request."""
    if label:
        print(f"\n=== {label} ===")

    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")


def test_register():
    """Test user registration."""
    print("\n=== Testing User Registration ===")

    # Test data for registration
    register_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123",
        "password2": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "user_type": "student",
        "birthdate": "2000-01-01"
    }

    # Send registration request
    response = requests.post(
        f"{BASE_URL}/api/auth/register/",
        headers=headers,
        data=json.dumps(register_data)
    )

    print_response(response)

    if response.status_code == 201:
        print("Registration successful!")
        return response.json().get('access')
    else:
        print("Registration failed!")
        return None


def test_login():
    """Test user login."""
    print("\n=== Testing User Login ===")

    # Test data for login
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }

    # Send login request
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        headers=headers,
        data=json.dumps(login_data)
    )

    print_response(response)

    if response.status_code == 200:
        print("Login successful!")
        return response.json().get('access')
    else:
        print("Login failed!")
        return None


def test_profile(token):
    """Test retrieving user profile."""
    print("\n=== Testing User Profile ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Send profile request
    response = requests.get(
        f"{BASE_URL}/api/auth/profile/",
        headers=auth_headers
    )

    print_response(response)

    if response.status_code == 200:
        print("Profile retrieval successful!")
    else:
        print("Profile retrieval failed!")


def test_create_post(token):
    """Test creating a post."""
    print("\n=== Testing Post Creation ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Test data for post creation
    post_data = {
        "content": "This is a test post with @testuser mention."
    }

    # Send post creation request
    response = requests.post(
        f"{BASE_URL}/api/posts/",
        headers=auth_headers,
        data=json.dumps(post_data)
    )

    print_response(response)

    if response.status_code == 201:
        print("Post creation successful!")
        return response.json().get('id')
    else:
        print("Post creation failed!")
        return None


def test_get_posts(token):
    """Test retrieving posts."""
    print("\n=== Testing Post Retrieval ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Send post retrieval request
    response = requests.get(
        f"{BASE_URL}/api/posts/",
        headers=auth_headers
    )

    print_response(response)

    if response.status_code == 200:
        print("Post retrieval successful!")
    else:
        print("Post retrieval failed!")


def test_add_comment(token, post_id):
    """Test adding a comment to a post."""
    print("\n=== Testing Comment Creation ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Test data for comment creation
    comment_data = {
        "content": "This is a test comment with @testuser mention.",
        "post": post_id
    }

    # Send comment creation request
    response = requests.post(
        f"{BASE_URL}/api/comments/",
        headers=auth_headers,
        data=json.dumps(comment_data)
    )

    print_response(response)

    if response.status_code == 201:
        print("Comment creation successful!")
        return response.json().get('id')
    else:
        print("Comment creation failed!")
        return None


def test_like_post(token, post_id):
    """Test liking a post."""
    print("\n=== Testing Post Like ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Send like request
    response = requests.post(
        f"{BASE_URL}/api/posts/{post_id}/like/",
        headers=auth_headers
    )

    print_response(response)

    if response.status_code == 200:
        print("Post like successful!")
    else:
        print("Post like failed!")


def test_get_notifications(token):
    """Test retrieving notifications."""
    print("\n=== Testing Notification Retrieval ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Send notification retrieval request
    response = requests.get(
        f"{BASE_URL}/api/notifications/",
        headers=auth_headers
    )

    print_response(response)

    if response.status_code == 200:
        print("Notification retrieval successful!")
    else:
        print("Notification retrieval failed!")


def test_mark_notification_read(token):
    """Test marking all notifications as read."""
    print("\n=== Testing Mark All Notifications as Read ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Send mark all read request
    response = requests.post(
        f"{BASE_URL}/api/notifications/mark_all_read/",
        headers=auth_headers
    )

    print_response(response)

    if response.status_code == 200:
        print("Mark all notifications as read successful!")
    else:
        print("Mark all notifications as read failed!")


def test_search_users(token):
    """Test searching for users."""
    print("\n=== Testing User Search ===")

    # Update headers with authentication token
    auth_headers = headers.copy()
    auth_headers['Authorization'] = f"Bearer {token}"

    # Send user search request
    response = requests.get(
        f"{BASE_URL}/api/users/search/?q=test",
        headers=auth_headers
    )

    print_response(response)

    if response.status_code == 200:
        print("User search successful!")
    else:
        print("User search failed!")


def main():
    """Main function to run all tests."""
    print("=== E-Platform API Test Script ===")

    # Test registration
    token = test_register()

    if not token:
        # If registration fails or user already exists, try login
        print("Registration failed or user already exists. Trying login...")
        token = test_login()

    if not token:
        print("Authentication failed. Cannot proceed with tests.")
        sys.exit(1)

    # Test profile
    test_profile(token)

    # Test post creation
    post_id = test_create_post(token)

    if not post_id:
        print("Post creation failed. Cannot proceed with post-related tests.")
    else:
        # Test post retrieval
        test_get_posts(token)

        # Test comment creation
        test_add_comment(token, post_id)

        # Test post like
        test_like_post(token, post_id)

    # Test notification retrieval
    test_get_notifications(token)

    # Test mark all notifications as read
    test_mark_notification_read(token)

    # Test user search
    test_search_users(token)

    print("\n=== All tests completed ===")


if __name__ == "__main__":
    main()
