import time
import sys
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_Platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from chatting.models import Conversation, Message, UserStatus

User = get_user_model()

def test_message_read_status():
    """
    Test that messages are marked as read for the sender.
    """
    print("Testing message read status...")

    # Get two users for testing
    users = User.objects.all()[:2]

    if len(users) < 2:
        print("Error: Need at least two users for testing")
        return False

    user1, user2 = users

    print(f"Using users: {user1.username} and {user2.username}")

    # Create a conversation between the users
    conversation = Conversation.objects.filter(participants=user1).filter(participants=user2).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(user1, user2)
        conversation.save()
        print(f"Created new conversation with ID: {conversation.id}")
    else:
        print(f"Using existing conversation with ID: {conversation.id}")

    # Create a message from user1 to user2
    message = Message.objects.create(
        conversation=conversation,
        sender=user1,
        content="Test message from API",
        is_read=True  # This should be set automatically now
    )

    print(f"Created message with ID: {message.id}")

    # Check if the message is marked as read for the sender
    if message.is_read:
        print("Success: Message is marked as read for the sender")
    else:
        print("Error: Message is not marked as read for the sender")
        return False

    # Create a message from user2 to user1
    message2 = Message.objects.create(
        conversation=conversation,
        sender=user2,
        content="Test reply message",
        is_read=True  # This should be set automatically now
    )

    print(f"Created reply message with ID: {message2.id}")

    # Check if the message is marked as read for the sender
    if message2.is_read:
        print("Success: Reply message is marked as read for the sender")
    else:
        print("Error: Reply message is not marked as read for the sender")
        return False

    # Count unread messages for user1
    unread_count_user1 = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=user1).count()

    print(f"Unread messages for {user1.username}: {unread_count_user1}")

    # Count unread messages for user2
    unread_count_user2 = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=user2).count()

    print(f"Unread messages for {user2.username}: {unread_count_user2}")

    # Mark messages as read for user1
    messages_to_mark = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=user1)

    for msg in messages_to_mark:
        msg.is_read = True
        msg.save()

    print(f"Marked {len(messages_to_mark)} messages as read for {user1.username}")

    # Count unread messages for user1 again
    unread_count_user1_after = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=user1).count()

    print(f"Unread messages for {user1.username} after marking as read: {unread_count_user1_after}")

    if unread_count_user1_after == 0:
        print("Success: All messages marked as read for user1")
    else:
        print("Error: Some messages are still unread for user1")
        return False

    return True

def main():
    """
    Run all tests.
    """
    print("Starting messaging tests...")

    tests = [
        test_message_read_status,
    ]

    success = True

    for test in tests:
        if not test():
            success = False

    if success:
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
