import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

from authentication.models import CustomUser

# List all users
print('Total users:', CustomUser.objects.count())
print('Users:')
for user in CustomUser.objects.all():
    print(f'- {user.username} ({user.user_type})')
