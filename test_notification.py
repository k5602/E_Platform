import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

from home.models import Notification
from authentication.models import CustomUser

# Get the first user
user = CustomUser.objects.first()

if user:
    # Create a test notification
    notification = Notification.objects.create(
        recipient=user,
        sender=user,
        notification_type='mention',
        text='Test notification'
    )
    print(f'Test notification created with ID: {notification.id}')
    
    # Count unread notifications
    count = Notification.objects.filter(recipient=user, is_read=False).count()
    print(f'Unread notifications count: {count}')
else:
    print('No users found in the database')
