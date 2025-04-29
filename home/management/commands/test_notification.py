from django.core.management.base import BaseCommand
from home.models import Notification
from authentication.models import CustomUser

class Command(BaseCommand):
    help = 'Create a test notification'

    def handle(self, *args, **options):
        user = CustomUser.objects.first()
        if user:
            notification = Notification.objects.create(
                recipient=user,
                sender=user,
                notification_type='mention',
                text='Test notification'
            )
            self.stdout.write(self.style.SUCCESS(f'Test notification created with ID: {notification.id}'))
        else:
            self.stdout.write(self.style.ERROR('No users found in the database'))
