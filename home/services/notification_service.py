from home.models import Notification
from home.utils import get_time_ago
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class for notification-related business logic."""

    @staticmethod
    def get_user_notifications(user, limit=20):
        """Get optimized notifications for a user."""
        notifications = (
            Notification.objects.filter(recipient=user)
            .select_related("sender", "post", "comment")
            .only(
                "id",
                "notification_type",
                "text",
                "is_read",
                "created_at",
                "sender__username",
                "sender__first_name",
                "sender__last_name",
                "post__id",
                "post__content",
                "comment__id",
                "comment__content",
            )
            .order_by("-created_at")[:limit]
        )

        notifications_data = []
        for notification in notifications:
            data = {
                "id": notification.id,
                "type": notification.notification_type,
                "text": notification.text,
                "sender": {
                    "username": notification.sender.username,
                    "first_name": notification.sender.first_name,
                    "last_name": notification.sender.last_name,
                },
                "is_read": notification.is_read,
                "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
                "time_ago": get_time_ago(notification.created_at),
            }

            # Add post info if available
            if notification.post:
                data["post"] = {
                    "id": notification.post.id,
                    "content_preview": (
                        notification.post.content[:50] + "..."
                        if len(notification.post.content) > 50
                        else notification.post.content
                    ),
                }

            # Add comment info if available
            if notification.comment:
                data["comment"] = {
                    "id": notification.comment.id,
                    "content_preview": (
                        notification.comment.content[:50] + "..."
                        if len(notification.comment.content) > 50
                        else notification.comment.content
                    ),
                }

            notifications_data.append(data)

        return notifications_data

    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for a user."""
        return (
            Notification.objects.filter(recipient=user, is_read=False)
            .values("id")
            .count()
        )

    @staticmethod
    def mark_notification_read(user, notification_id=None):
        """Mark notifications as read."""
        if notification_id:
            # Mark a specific notification as read
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.is_read = True
            notification.save()
            message = "Notification marked as read"
        else:
            # Mark all notifications as read
            Notification.objects.filter(recipient=user, is_read=False).update(
                is_read=True
            )
            message = "All notifications marked as read"

        unread_count = NotificationService.get_unread_count(user)

        return {"message": message, "unread_count": unread_count}
