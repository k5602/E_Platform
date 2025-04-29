from django.db import models
from authentication.models import CustomUser
from django.utils import timezone
import re

class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video = models.FileField(upload_to='posts/videos/', null=True, blank=True)
    document = models.FileField(upload_to='posts/documents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Process mentions only if this is a new post
        if is_new and self.content:
            from home.utils import extract_mentions
            mentioned_users = extract_mentions(self.content)

            print(f"Post save: Found {len(mentioned_users)} mentioned users in post {self.id}")

            # Create notifications for mentioned users
            for mentioned_user in mentioned_users:
                if mentioned_user != self.user:  # Don't notify yourself
                    print(f"Creating mention notification for {mentioned_user.username} from {self.user.username}")
                    notification = Notification.objects.create(
                        recipient=mentioned_user,
                        sender=self.user,
                        post=self,
                        notification_type='mention',
                        text=f"{self.user.username} mentioned you in a post"
                    )
                    print(f"Created notification with ID: {notification.id}")

class Like(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.post}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create notification for post owner (if not self)
        if is_new and self.post.user != self.user:
            Notification.objects.create(
                recipient=self.post.user,
                sender=self.user,
                post=self.post,
                notification_type='like',
                text=f"{self.user.username} liked your post"
            )

class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Create notification for post owner (if not self)
            if self.post.user != self.user:
                print(f"Creating comment notification for post owner {self.post.user.username}")
                notification = Notification.objects.create(
                    recipient=self.post.user,
                    sender=self.user,
                    post=self.post,
                    comment=self,
                    notification_type='comment',
                    text=f"{self.user.username} commented on your post"
                )
                print(f"Created comment notification with ID: {notification.id}")

            # Process mentions
            if self.content:
                from home.utils import extract_mentions
                mentioned_users = extract_mentions(self.content)

                print(f"Comment save: Found {len(mentioned_users)} mentioned users in comment {self.id}")

                # Create notifications for mentioned users
                for mentioned_user in mentioned_users:
                    if mentioned_user != self.user:  # Don't notify yourself
                        print(f"Creating mention notification for {mentioned_user.username} from {self.user.username} in comment")
                        notification = Notification.objects.create(
                            recipient=mentioned_user,
                            sender=self.user,
                            post=self.post,
                            comment=self,
                            notification_type='mention',
                            text=f"{self.user.username} mentioned you in a comment"
                        )
                        print(f"Created mention notification with ID: {notification.id}")

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

class Appointment(models.Model):
    APPOINTMENT_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    APPOINTMENT_TYPE = (
        ('office_hours', 'Office Hours'),
        ('project_discussion', 'Project Discussion'),
        ('academic_advice', 'Academic Advice'),
        ('course_related', 'Course Related'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=50, choices=APPOINTMENT_TYPE, default='office_hours')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='pending')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='appointments')
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='instructor_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"Appointment for {self.name} on {self.appointment_date} at {self.appointment_time} ({self.get_status_display()})"

    def is_upcoming(self):
        """Check if the appointment is in the future."""
        current_date = timezone.now().date()
        return self.appointment_date >= current_date

    def is_past(self):
        """Check if the appointment has passed."""
        current_date = timezone.now().date()
        return self.appointment_date < current_date


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('mention', 'Mention'),
        ('comment', 'Comment'),
        ('like', 'Like'),
    )

    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    text = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.username} from {self.sender.username}"
