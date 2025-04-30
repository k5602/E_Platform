from django.db import models
from authentication.models import CustomUser
from django.utils import timezone

class Conversation(models.Model):
    """Model representing a conversation between two users."""
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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

class Message(models.Model):
    """Model representing a message in a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"
        
    def mark_as_read(self):
        """Mark the message as read."""
        self.is_read = True
        self.save()

class UserStatus(models.Model):
    """Model to track user online status."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='chat_status')
    is_online = models.BooleanField(default=False)
    last_active = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.user.username} - {status}"
        
    def update_status(self, status):
        """Update the user's online status."""
        self.is_online = status
        if not status:
            self.last_active = timezone.now()
        self.save()
