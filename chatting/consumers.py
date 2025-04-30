import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Conversation, Message, UserStatus

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat functionality.
    """
    async def connect(self):
        self.user = self.scope["user"]

        # Anonymous users can't use WebSockets
        if self.user.is_anonymous:
            await self.close()
            return

        # Set user as online
        await self.set_user_online(self.user.id, True)

        # Create a unique channel group name for the user
        self.user_group_name = f"user_{self.user.id}"

        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # Join the global online users group
        await self.channel_layer.group_add(
            "online_users",
            self.channel_name
        )

        # Broadcast user online status to all connected clients
        await self.channel_layer.group_send(
            "online_users",
            {
                "type": "user_status",
                "user_id": self.user.id,
                "status": True
            }
        )

        # Add user to specific conversation groups
        user_conversations = await self.get_user_conversations(self.user.id)
        for conversation_id in user_conversations:
            conversation_group_name = f"conversation_{conversation_id}"
            await self.channel_layer.group_add(
                conversation_group_name,
                self.channel_name
            )

        # Add user to online status group
        await self.channel_layer.group_add(
            "online_users",
            self.channel_name
        )

        # Broadcast user online status
        await self.channel_layer.group_send(
            "online_users",
            {
                "type": "user_status",
                "user_id": self.user.id,
                "status": True
            }
        )

        # Accept the connection
        await self.accept()

    async def disconnect(self, _):
        if hasattr(self, 'user') and not self.user.is_anonymous:
            # Set user as offline
            user_status = await self.set_user_online(self.user.id, False)

            # Leave user group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

            # Leave conversation groups
            user_conversations = await self.get_user_conversations(self.user.id)
            for conversation_id in user_conversations:
                conversation_group_name = f"conversation_{conversation_id}"
                await self.channel_layer.group_discard(
                    conversation_group_name,
                    self.channel_name
                )

            # Leave online status group
            await self.channel_layer.group_discard(
                "online_users",
                self.channel_name
            )

            # Broadcast user offline status with last seen time
            await self.channel_layer.group_send(
                "online_users",
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "status": False,
                    "last_seen": user_status.last_active.isoformat() if hasattr(user_status, 'last_active') else timezone.now().isoformat()
                }
            )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', '')

        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'read_messages':
            await self.handle_read_messages(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)

    async def handle_chat_message(self, data):
        """
        Handle incoming chat messages.
        """
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()

        if not content:
            return

        # Check if the user is a participant in this conversation
        is_participant = await self.is_conversation_participant(conversation_id, self.user.id)
        if not is_participant:
            return

        # Create the message in the database
        message = await self.create_message(conversation_id, self.user.id, content)

        # Update conversation timestamp
        await self.update_conversation_timestamp(conversation_id)

        # Get the other participant in the conversation
        other_participant = await self.get_other_participant(conversation_id, self.user.id)

        # Prepare the message data
        message_data = {
            "type": "chat_message",
            "message": {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "sender_id": self.user.id,
                "sender_name": f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
                "is_read": False
            },
            "conversation_id": conversation_id
        }

        # Send the message to the conversation group
        conversation_group_name = f"conversation_{conversation_id}"
        await self.channel_layer.group_send(
            conversation_group_name,
            message_data
        )

        # Also send a notification to the other participant's personal group
        if other_participant:
            await self.channel_layer.group_send(
                f"user_{other_participant}",
                {
                    "type": "new_message_notification",
                    "conversation_id": conversation_id,
                    "message": message_data["message"]
                }
            )

    async def handle_read_messages(self, data):
        """
        Handle message read status updates.
        """
        conversation_id = data.get('conversation_id')

        # Check if the user is a participant in this conversation
        is_participant = await self.is_conversation_participant(conversation_id, self.user.id)
        if not is_participant:
            return

        # Mark messages as read
        await self.mark_messages_as_read(conversation_id, self.user.id)

        # Get the other participant in the conversation
        other_participant = await self.get_other_participant(conversation_id, self.user.id)

        # Notify the other participant that messages have been read
        if other_participant:
            await self.channel_layer.group_send(
                f"user_{other_participant}",
                {
                    "type": "messages_read",
                    "conversation_id": conversation_id,
                    "reader_id": self.user.id
                }
            )

    async def handle_typing(self, data):
        """
        Handle typing indicators.
        """
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', False)

        # Check if the user is a participant in this conversation
        is_participant = await self.is_conversation_participant(conversation_id, self.user.id)
        if not is_participant:
            return

        # Get the other participant in the conversation
        other_participant = await self.get_other_participant(conversation_id, self.user.id)

        if other_participant:
            # Send typing indicator to the other participant
            await self.channel_layer.group_send(
                f"user_{other_participant}",
                {
                    "type": "typing_indicator",
                    "conversation_id": conversation_id,
                    "user_id": self.user.id,
                    "is_typing": is_typing
                }
            )

    async def chat_message(self, event):
        """
        Send the chat message to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "conversation_id": event["conversation_id"]
        }))

    async def new_message_notification(self, event):
        """
        Send a new message notification to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "new_message_notification",
            "conversation_id": event["conversation_id"],
            "message": event["message"]
        }))

    async def messages_read(self, event):
        """
        Send a messages read notification to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "messages_read",
            "conversation_id": event["conversation_id"],
            "reader_id": event["reader_id"]
        }))

    async def typing_indicator(self, event):
        """
        Send a typing indicator to the WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "typing_indicator",
            "conversation_id": event["conversation_id"],
            "user_id": event["user_id"],
            "is_typing": event["is_typing"]
        }))

    async def user_status(self, event):
        """
        Send user online status update to the WebSocket.
        """
        status_data = {
            "type": "user_status",
            "user_id": event["user_id"],
            "status": event["status"]
        }

        # Add last_seen if available
        if "last_seen" in event:
            status_data["last_seen"] = event["last_seen"]

        await self.send(text_data=json.dumps(status_data))

    # Database access methods

    @database_sync_to_async
    def set_user_online(self, user_id, status):
        """
        Set the user's online status in the database.
        """
        user_status, _ = UserStatus.objects.get_or_create(user_id=user_id)
        user_status.is_online = status
        if not status:
            user_status.last_active = timezone.now()
        user_status.save()
        return user_status

    @database_sync_to_async
    def get_user_conversations(self, user_id):
        """
        Get all conversation IDs that the user is a participant in.
        """
        return list(Conversation.objects.filter(participants__id=user_id).values_list('id', flat=True))

    @database_sync_to_async
    def is_conversation_participant(self, conversation_id, user_id):
        """
        Check if a user is a participant in a conversation.
        """
        return Conversation.objects.filter(id=conversation_id, participants__id=user_id).exists()

    @database_sync_to_async
    def create_message(self, conversation_id, user_id, content):
        """
        Create a new message in the database.
        """
        message = Message.objects.create(
            conversation_id=conversation_id,
            sender_id=user_id,
            content=content
        )
        return message

    @database_sync_to_async
    def update_conversation_timestamp(self, conversation_id):
        """
        Update the conversation's timestamp.
        """
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.update_timestamp()
        return conversation

    @database_sync_to_async
    def get_other_participant(self, conversation_id, user_id):
        """
        Get the ID of the other participant in a conversation.
        """
        conversation = Conversation.objects.get(id=conversation_id)
        other_participant = conversation.participants.exclude(id=user_id).first()
        return other_participant.id if other_participant else None

    @database_sync_to_async
    def mark_messages_as_read(self, conversation_id, user_id):
        """
        Mark all messages in a conversation as read for a user.
        """
        messages = Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender_id=user_id)

        for message in messages:
            message.is_read = True
            message.save()

        return messages.count()