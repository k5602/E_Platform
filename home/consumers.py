import json
import logging
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import Notification

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications with optimized caching."""

    async def connect(self):
        """Connect to the WebSocket with optimized caching."""
        try:
            self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
            self.notification_group_name = f"notifications_{self.user_id}"
            self.cache_key_unread = f"notification_unread_{self.user_id}"

            logger.info(f"WebSocket connection attempt for user_id: {self.user_id}")

            # Check if the user is authenticated and authorized
            if not await self.is_user_authorized():
                logger.warning(
                    f"Unauthorized WebSocket connection attempt for user_id: {self.user_id}"
                )
                await self.close(code=4003)  # 4003: Unauthorized
                return

            # Join the notification group
            await self.channel_layer.group_add(
                self.notification_group_name, self.channel_name
            )

            logger.info(
                f"User {self.user_id} joined notification group: {self.notification_group_name}"
            )
            await self.accept()

            # Send initial unread count with caching
            unread_count = await self.get_unread_notification_count_cached()
            await self.send(
                text_data=json.dumps(
                    {"type": "unread_count", "count": unread_count, "status": "success"}
                )
            )

        except Exception as e:
            logger.error(
                f"Error in WebSocket connect for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            await self.close(code=4000)  # 4000: Generic error

    async def disconnect(self, close_code):
        """Disconnect from the WebSocket."""
        try:
            # Leave the notification group
            await self.channel_layer.group_discard(
                self.notification_group_name, self.channel_name
            )
            logger.info(
                f"User {self.user_id} disconnected from notification group with code: {close_code}"
            )
        except Exception as e:
            logger.error(
                f"Error in WebSocket disconnect for user_id {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())

    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            # Validate JSON format
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid JSON received from user {self.user_id}: {text_data}"
                )
                await self.send_error("Invalid JSON format")
                return

            # Validate message structure
            message_type = data.get("type")
            if not message_type:
                logger.warning(
                    f"Message missing 'type' field from user {self.user_id}: {data}"
                )
                await self.send_error("Message type is required")
                return

            logger.info(
                f"Received message of type '{message_type}' from user {self.user_id}"
            )

            if message_type == "mark_read":
                notification_id = data.get("notification_id")
                if not notification_id:
                    logger.warning(
                        f"'mark_read' message missing notification_id from user {self.user_id}"
                    )
                    await self.send_error("notification_id is required for mark_read")
                    return

                # Mark a specific notification as read
                success = await self.mark_notification_read(notification_id)
                if success:
                    # Send updated unread count
                    unread_count = await self.get_unread_notification_count()
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "unread_count",
                                "count": unread_count,
                                "status": "success",
                                "message": f"Notification {notification_id} marked as read",
                            }
                        )
                    )
                else:
                    await self.send_error(
                        f"Notification {notification_id} not found or not authorized"
                    )

            elif message_type == "mark_all_read":
                # Mark all notifications as read
                count = await self.mark_all_notifications_read()
                # Send updated unread count (should be 0)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "unread_count",
                            "count": 0,
                            "status": "success",
                            "message": f"{count} notifications marked as read",
                        }
                    )
                )

            else:
                logger.warning(
                    f"Unknown message type '{message_type}' from user {self.user_id}"
                )
                await self.send_error(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error processing message from user {self.user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            await self.send_error("Internal server error")

    async def notification_message(self, event):
        """Send notification to WebSocket and update cached unread count."""
        try:
            # Send the notification data to the WebSocket
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "notification",
                        "notification": event["notification"],
                        "status": "success",
                    }
                )
            )

            # Update cached unread count (invalidate cache to force refresh)
            cache.delete(self.cache_key_unread)

            # Send the updated unread count
            unread_count = await self.get_unread_notification_count_cached()
            await self.send(
                text_data=json.dumps(
                    {"type": "unread_count", "count": unread_count, "status": "success"}
                )
            )

            logger.info(
                f"Notification sent to user {self.user_id}: {event['notification'].get('id')}"
            )

        except Exception as e:
            logger.error(f"Error sending notification to user {self.user_id}: {str(e)}")
            logger.error(traceback.format_exc())
            await self.send_error("Error delivering notification")

    async def send_error(self, message):
        """Send an error message to the client."""
        try:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": message, "status": "error"}
                )
            )
        except Exception as e:
            logger.error(
                f"Error sending error message to user {self.user_id}: {str(e)}"
            )

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
            logger.warning(f"User with ID {self.user_id} does not exist")
            return False
        except Exception as e:
            logger.error(
                f"Error checking authorization for user {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False

    @database_sync_to_async
    def get_unread_notification_count(self):
        """Get the count of unread notifications for the user."""
        try:
            user = User.objects.get(id=self.user_id)
            count = Notification.objects.filter(recipient=user, is_read=False).count()
            logger.debug(f"Unread notification count for user {self.user_id}: {count}")
            return count
        except User.DoesNotExist:
            logger.warning(
                f"User with ID {self.user_id} does not exist when getting unread count"
            )
            return 0
        except Exception as e:
            logger.error(
                f"Error getting unread count for user {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return 0

    async def get_unread_notification_count_cached(self):
        """Get unread notification count with caching for better performance."""
        # Try to get from cache first
        cached_count = cache.get(self.cache_key_unread)
        if cached_count is not None:
            return cached_count

        # Cache miss - get from database
        count = await self.get_unread_notification_count()

        # Cache for 30 seconds
        cache.set(self.cache_key_unread, count, 30)
        return count

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(
                id=notification_id, recipient_id=self.user_id
            )
            notification.is_read = True
            notification.save()

            # Invalidate cache
            cache.delete(self.cache_key_unread)

            logger.info(
                f"Notification {notification_id} marked as read for user {self.user_id}"
            )
            return True
        except Notification.DoesNotExist:
            logger.warning(
                f"Notification {notification_id} not found for user {self.user_id}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Error marking notification {notification_id} as read for user {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read."""
        try:
            count = Notification.objects.filter(
                recipient_id=self.user_id, is_read=False
            ).count()
            Notification.objects.filter(
                recipient_id=self.user_id, is_read=False
            ).update(is_read=True)

            # Invalidate cache
            cache.delete(self.cache_key_unread)

            logger.info(
                f"All {count} notifications marked as read for user {self.user_id}"
            )
            return count
        except Exception as e:
            logger.error(
                f"Error marking all notifications as read for user {self.user_id}: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return 0
