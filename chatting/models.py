from django.db import models
from django.utils import timezone

from authentication.models import CustomUser


class Conversation(models.Model):
    """Model representing a conversation between two users."""
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        participant_names = ", ".join([user.username for user in self.participants.all()])
        return f"Conversation between {participant_names}"

    def get_other_participant(self, user):
        """Get the other participant in a conversation."""
        return self.participants.exclude(id=user.id).first()

    def update_timestamp(self):
        """Update the timestamp when a new message is added."""
        self.updated_at = timezone.now()
        self.save()


def message_file_path(instance, filename):
    """
    Generate a unique file path for message attachments.
    Format: chat_files/conversation_{id}/{timestamp}_{filename}
    """
    import os
    from django.utils import timezone

    # Get the file extension
    ext = filename.split('.')[-1]

    # Create a timestamp-based filename to avoid collisions
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f"{timestamp}_{instance.sender.id}_{filename}"

    # Return the complete path
    return os.path.join('chat_files', f'conversation_{instance.conversation.id}', new_filename)


class Message(models.Model):
    """Model representing a message in a conversation."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    )

    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('other', 'Other'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', db_index=True)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages', db_index=True)
    content = models.TextField(blank=True)  # Allow empty content for file-only messages
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    delivery_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    delivery_attempts = models.IntegerField(default=0)
    last_delivery_attempt = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False, db_index=True)
    edited_timestamp = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_timestamp = models.DateTimeField(null=True, blank=True)

    # File attachment fields
    file_attachment = models.FileField(upload_to=message_file_path, null=True, blank=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)  # Size in bytes

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

    def mark_as_read(self):
        """Mark the message as read."""
        self.is_read = True
        self.delivery_status = 'read'
        self.save()

    def mark_as_delivered(self):
        """Mark the message as delivered."""
        self.delivery_status = 'delivered'
        self.save()

    def increment_delivery_attempt(self):
        """Increment the delivery attempt counter."""
        self.delivery_attempts += 1
        self.last_delivery_attempt = timezone.now()
        self.save()

    def mark_as_failed(self):
        """Mark the message as failed after multiple delivery attempts."""
        self.delivery_status = 'failed'
        self.save()

    def edit_message(self, new_content):
        """
        Edit the message content and mark it as edited.

        Args:
            new_content: The new content for the message

        Returns:
            The updated message
        """
        self.content = new_content
        self.is_edited = True
        self.edited_timestamp = timezone.now()
        self.save()
        return self

    def delete_message(self):
        """
        Soft delete the message by marking it as deleted.

        Returns:
            The updated message
        """
        self.is_deleted = True
        self.deleted_timestamp = timezone.now()
        # We keep the content but mark it as deleted
        self.save()
        return self

class UserStatus(models.Model):
    """Model to track user online status."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='chat_status', db_index=True)
    is_online = models.BooleanField(default=False, db_index=True)
    last_active = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.user.username} - {status}"

    def update_status(self, status):
        """Update the user's online status."""
        self.is_online = status
        if not status:
            self.last_active = timezone.now()
        self.save()
