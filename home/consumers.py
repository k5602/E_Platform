import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications."""

    async def connect(self):
        """Connect to the WebSocket."""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.notification_group_name = f'notifications_{self.user_id}'

        # Check if the user is authenticated and authorized
        if not await self.is_user_authorized():
            await self.close()
            return

        # Join the notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial unread count
        unread_count = await self.get_unread_notification_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        """Disconnect from the WebSocket."""
        # Leave the notification group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Receive message from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'mark_read':
            notification_id = data.get('notification_id')
            if notification_id:
                # Mark a specific notification as read
                success = await self.mark_notification_read(notification_id)
                if success:
                    # Send updated unread count
                    unread_count = await self.get_unread_notification_count()
                    await self.send(text_data=json.dumps({
                        'type': 'unread_count',
                        'count': unread_count
                    }))

        elif message_type == 'mark_all_read':
            # Mark all notifications as read
            await self.mark_all_notifications_read()
            # Send updated unread count (should be 0)
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': 0
            }))

    async def notification_message(self, event):
        """Send notification to WebSocket."""
        # Send the notification data to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

        # Also send the updated unread count
        unread_count = await self.get_unread_notification_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    @database_sync_to_async
    def is_user_authorized(self):
        """Check if the user is authorized to receive notifications."""
        try:
            # Get the user from the database
            user = User.objects.get(id=self.user_id)

            # For development, allow all connections
            # In production, this should be more restrictive
            return True

        except User.DoesNotExist:
            print(f"User with ID {self.user_id} does not exist")
            return False

    @database_sync_to_async
    def get_unread_notification_count(self):
        """Get the count of unread notifications for the user."""
        try:
            user = User.objects.get(id=self.user_id)
            return Notification.objects.filter(recipient=user, is_read=False).count()
        except User.DoesNotExist:
            return 0

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(id=notification_id, recipient_id=self.user_id)
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications for the user as read."""
        Notification.objects.filter(recipient_id=self.user_id, is_read=False).update(is_read=True)
