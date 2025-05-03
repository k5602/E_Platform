#!/usr/bin/env python
"""
Test script for PostgreSQL connection.
This script tests the connection to PostgreSQL and demonstrates the fallback to SQLite.
"""

import os
import sys
import django

# Set environment variables for PostgreSQL
os.environ['DB_ENGINE'] = 'postgresql'
os.environ['DB_NAME'] = 'e_platform_db'
os.environ['DB_USER'] = 'zero'
os.environ['DB_PASSWORD'] = '82821931003'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

# Import models after Django setup
from authentication.models import CustomUser
from home.models import Post, Notification
from django.conf import settings

# Print database configuration
print("=== Database Configuration ===")
print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Name: {settings.DATABASES['default']['NAME']}")

# Check if tables exist by counting records
print("\n=== Database Tables Check ===")
print(f"CustomUser: {CustomUser.objects.count()} records")
print(f"Post: {Post.objects.count()} records")
print(f"Notification: {Notification.objects.count()} records")

# Get the first user (if any)
user = CustomUser.objects.first()
if user:
    print(f"\nFound user: {user.username}")
    
    # Create a test notification
    notification = Notification.objects.create(
        recipient=user,
        sender=user,
        notification_type='test',
        text='Test notification from PostgreSQL connection test'
    )
    print(f"Created Notification with ID: {notification.id}")
else:
    print("\nNo users found in the database. Please create a user first.")

print("\n=== Test completed ===")