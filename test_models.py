import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

from authentication.models import CustomUser
from home.models import Post, Comment, Like, Notification
from chatting.models import Conversation, Message, UserStatus
from Ai_prototype.models import MockAIFeedback

# Check if tables exist by counting records
print("=== Database Tables Check ===")
print(f"CustomUser: {CustomUser.objects.count()} records")
print(f"Post: {Post.objects.count()} records")
print(f"Comment: {Comment.objects.count()} records")
print(f"Like: {Like.objects.count()} records")
print(f"Notification: {Notification.objects.count()} records")
print(f"Conversation: {Conversation.objects.count()} records")
print(f"Message: {Message.objects.count()} records")
print(f"UserStatus: {UserStatus.objects.count()} records")
print(f"MockAIFeedback: {MockAIFeedback.objects.count()} records")

# Get the first user (if any)
user = CustomUser.objects.first()
if user:
    print(f"\nFound user: {user.username}")
    
    # Create test records for each model
    print("\n=== Creating Test Records ===")
    
    # Create a test post
    post = Post.objects.create(
        user=user,
        content="This is a test post"
    )
    print(f"Created Post with ID: {post.id}")
    
    # Create a test notification
    notification = Notification.objects.create(
        recipient=user,
        sender=user,
        notification_type='mention',
        text='Test notification'
    )
    print(f"Created Notification with ID: {notification.id}")
    
    # Create a test conversation (with the same user as both participants for simplicity)
    conversation = Conversation.objects.create()
    conversation.participants.add(user)
    print(f"Created Conversation with ID: {conversation.id}")
    
    # Create a test message
    message = Message.objects.create(
        conversation=conversation,
        sender=user,
        content="This is a test message"
    )
    print(f"Created Message with ID: {message.id}")
    
    # Create or update user status
    user_status, created = UserStatus.objects.get_or_create(user=user)
    user_status.is_online = True
    user_status.save()
    print(f"{'Created' if created else 'Updated'} UserStatus for {user.username}")
    
    # Create a test AI feedback
    ai_feedback = MockAIFeedback.objects.create(
        user=user,
        feedback_type='general',
        submission_id='test-submission',
        feedback_text='This is a test AI feedback'
    )
    print(f"Created MockAIFeedback with ID: {ai_feedback.id}")
else:
    print("\nNo users found in the database. Please create a user first.")
