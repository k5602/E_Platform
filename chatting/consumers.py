import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.utils.html import escape
from django.urls import reverse

from .models import Conversation, Message, UserStatus

# Set up logger
logger = logging.getLogger(__name__)

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat functionality.
    """
    async def connect(self):
        # Enhanced logging for connection attempts
        user_id = self.scope["user"].id if hasattr(self.scope["user"], "id") else "anonymous"
        client_info = {
            "user_id": user_id,
            "path": self.scope.get("path", "unknown"),
            "client": f"{self.scope.get('client', ('unknown', 0))[0]}:{self.scope.get('client', ('unknown', 0))[1]}",
            "headers": dict(self.scope.get("headers", [])),
        }

        logger.info(f"WebSocket connection attempt: {client_info}")
        print(f"ChatConsumer.connect called for user {user_id}")

        self.user = self.scope["user"]

        # Anonymous users can't use WebSockets
        if self.user.is_anonymous:
            logger.warning("Anonymous user attempted to connect to chat WebSocket")
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

        # Add user to specific conversation groups
        user_conversations = await self.get_user_conversations(self.user.id)
        for conversation_id in user_conversations:
            conversation_group_name = f"conversation_{conversation_id}"
            await self.channel_layer.group_add(
                conversation_group_name,
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

        # Accept the connection
        await self.accept()

        # Log successful connection
        user_id = self.user.id if hasattr(self.user, "id") else "anonymous"
        logger.info(f"WebSocket connection established for user {user_id}")
        print(f"WebSocket connection established for user {user_id}")

        # Deliver any pending messages to the user who just came online
        if hasattr(self.user, "id") and not self.user.is_anonymous:
            delivered_count = await self.deliver_pending_messages(self.user.id)
            if delivered_count > 0:
                logger.info(f"Delivered {delivered_count} pending messages to user {self.user.id} on connect")
                print(f"Delivered {delivered_count} pending messages to user {self.user.id} on connect")

    async def disconnect(self, close_code):
        # Enhanced logging for disconnections
        user_id = self.scope["user"].id if hasattr(self.scope["user"], "id") else "anonymous"
        client_info = {
            "user_id": user_id,
            "path": self.scope.get("path", "unknown"),
            "client": f"{self.scope.get('client', ('unknown', 0))[0]}:{self.scope.get('client', ('unknown', 0))[1]}",
            "close_code": close_code
        }

        logger.info(f"WebSocket disconnection: {client_info}")
        print(f"ChatConsumer.disconnect called for user {user_id} with code {close_code}")

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

        This method parses the incoming JSON message, determines its type,
        and routes it to the appropriate handler method.

        Args:
            text_data: The raw WebSocket message as a string

        Returns:
            None
        """
        try:
            # Parse JSON data
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')

            # Log the received message type (but not content for privacy)
            logger.debug(f"Received WebSocket message of type '{message_type}' from user {self.user.id}")
            print(f"Received WebSocket message of type '{message_type}' from user {self.user.id}")

            # Route to appropriate handler based on message type
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'read_messages':
                await self.handle_read_messages(text_data_json)
            elif message_type == 'typing' or message_type == 'typing_indicator':
                # Handle both 'typing' and 'typing_indicator' for backward compatibility
                await self.handle_typing(text_data_json)
                print(f"Handling typing indicator: {text_data_json.get('is_typing')}")
            elif message_type == 'file_message_sent':
                # Handle notification that a file message was sent via HTTP
                await self.handle_file_message_sent(text_data_json)
                print(f"Handling file message sent notification for message {text_data_json.get('message_id')}")
            else:
                logger.warning(f"Unknown message type '{message_type}' received from user {self.user.id}")
                print(f"Unknown message type '{message_type}' received from user {self.user.id}")
                # Notify client about the error
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user.id}: {text_data[:100]}...")
            # Notify client about the error
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid message format. Please send valid JSON."
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message from user {self.user.id}: {str(e)}", exc_info=True)
            print(f"Error processing WebSocket message: {str(e)}")
            # Notify client about the error
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "An error occurred while processing your message."
            }))

    async def handle_chat_message(self, data):
        """
        Handle incoming chat messages from WebSocket clients.

        This method:
        1. Validates the message content and conversation ID
        2. Checks if the user is authorized to post in this conversation
        3. Applies rate limiting to prevent message flooding
        4. Sanitizes the message content to prevent XSS attacks
        5. Creates the message in the database
        6. Broadcasts the message to all participants

        Args:
            data (dict): The message data containing:
                - conversation_id: ID of the conversation
                - content: Text content of the message

        Returns:
            None
        """
        try:
            # Validate conversation_id
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                logger.warning(f"Missing conversation_id in message from user {self.user.id}")
                return

            # Validate and sanitize content
            content = data.get('content', '').strip()
            if not content:
                logger.debug(f"Empty message content from user {self.user.id}")
                return

            # Apply rate limiting
            rate_limit_key = f"message_rate_{self.user.id}"
            rate = cache.get(rate_limit_key, 0)

            if rate >= 10:  # Max 10 messages per minute
                logger.warning(f"Rate limit exceeded for user {self.user.id}")
                # Notify user about rate limiting
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "You're sending messages too quickly. Please wait a moment."
                }))
                return

            # Increment rate counter
            cache.set(rate_limit_key, rate + 1, 60)  # Reset after 60 seconds

            # Check if the user is a participant in this conversation
            is_participant = await self.is_conversation_participant(conversation_id, self.user.id)
            if not is_participant:
                logger.warning(
                    f"User {self.user.id} attempted to send message to conversation {conversation_id} they're not part of")
                return

            # Sanitize content to prevent XSS attacks
            sanitized_content = escape(content)

            # Create the message in the database (this also updates the conversation timestamp)
            message = await self.create_message(conversation_id, self.user.id, sanitized_content)
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}", exc_info=True)
            return

        # Get the other participant in the conversation
        other_participant = await self.get_other_participant(conversation_id, self.user.id)

        # Check if the recipient is online
        recipient_online = await self.is_user_online(other_participant)

        # Update message delivery status based on recipient's online status
        if recipient_online:
            await self.update_message_status(message.id, 'delivered')
            logger.info(f"Message {message.id} delivered to online user {other_participant}")
        else:
            logger.info(f"Message {message.id} queued for offline user {other_participant}")
            # Message remains in 'pending' status (default)

        # Prepare the message data
        message_data = {
            "type": "chat_message",
            "message": {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "sender_id": self.user.id,
                "sender_name": f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
                "is_read": False,
                "delivery_status": "delivered" if recipient_online else "pending"
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

        # Log the typing indicator
        print(f"Handling typing indicator from user {self.user.id}: is_typing={is_typing}")
        logger.debug(f"Handling typing indicator from user {self.user.id}: is_typing={is_typing}")

        # Check if the user is a participant in this conversation
        is_participant = await self.is_conversation_participant(conversation_id, self.user.id)
        if not is_participant:
            logger.warning(f"User {self.user.id} tried to send typing indicator for conversation {conversation_id} they're not part of")
            return

        # Get the other participant in the conversation
        other_participant = await self.get_other_participant(conversation_id, self.user.id)

        if other_participant:
            print(f"Sending typing indicator to user {other_participant}: is_typing={is_typing}")

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
        else:
            logger.warning(f"Could not find other participant for conversation {conversation_id}")
            print(f"Could not find other participant for conversation {conversation_id}")

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
        
    async def handle_file_message_sent(self, data):
        """
        Handle notification that a file message was sent through HTTP.
        Updates other participants about the new file message.
        """
        conversation_id = data.get('conversation_id')
        message_id = data.get('message_id')
        
        # Validate the data
        if not conversation_id or not message_id:
            return
        
        try:
            # Get message details
            message = await self.get_message(message_id)
            if not message:
                return
                
            # Get other participants
            other_participants = await self.get_other_participants(conversation_id, self.user.id)
            
            # Format message data for WebSocket
            message_data = await self.format_message_for_ws(message)
            
            # Send to the conversation group for other participants
            for participant_id in other_participants:
                await self.channel_layer.group_send(
                    f"user_{participant_id}",
                    {
                        "type": "chat_message",
                        "message": message_data,
                        "conversation_id": conversation_id,
                        "is_file": True
                    }
                )
        except Exception as e:
            logger.error(f"Error handling file message notification: {str(e)}", exc_info=True)

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
    def get_message(self, message_id):
        """
        Get a message by its ID.
        
        Args:
            message_id: The ID of the message
            
        Returns:
            The Message object or None if not found
        """
        try:
            return Message.objects.select_related('sender', 'conversation').get(id=message_id)
        except Message.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_other_participants(self, conversation_id, user_id):
        """
        Get the other participants in a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            user_id: The ID of the current user
            
        Returns:
            List of user IDs for other participants
        """
        try:
            # Get the conversation
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Get other participants (excluding current user)
            other_participants = conversation.participants.exclude(id=user_id).values_list('id', flat=True)
            
            return list(other_participants)
        except Conversation.DoesNotExist:
            return []
    
    @database_sync_to_async
    def format_message_for_ws(self, message):
        """
        Format a message for WebSocket transmission.
        
        Args:
            message: The Message object
            
        Returns:
            Dict with message data formatted for WebSocket
        """
        data = {
            'id': message.id,
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
                'first_name': message.sender.first_name or '',
                'last_name': message.sender.last_name or '',
            },
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'is_read': message.is_read,
            'delivery_status': message.delivery_status,
        }
        
        # Add file info if this is a file message
        if message.file_attachment:
            data['is_file'] = True
            data['file_type'] = message.file_type
            data['file_name'] = message.file_name
            data['file_size'] = message.file_size
            data['file_attachment'] = message.file_attachment.name
            # We can't construct absolute URLs here since we don't have request object
            # The frontend will handle this
            
        return data
    
    @database_sync_to_async
    def create_message(self, conversation_id, user_id, content):
        """
        Create a new message in the database.

        Uses SELECT FOR UPDATE to prevent race conditions when multiple
        messages are created simultaneously for the same conversation.

        Args:
            conversation_id: The ID of the conversation
            user_id: The ID of the message sender
            content: The sanitized message content

        Returns:
            The created Message object
        """
        from django.db import transaction

        try:
            with transaction.atomic():
                # Get conversation with a SELECT FOR UPDATE to prevent race conditions
                conversation = Conversation.objects.select_for_update().get(id=conversation_id)

                # Create message
                message = Message.objects.create(
                    conversation=conversation,
                    sender_id=user_id,
                    content=content,
                    is_read=True  # Messages are always read by the sender
                )

                # Update conversation timestamp
                conversation.update_timestamp()

            return message
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}", exc_info=True)
            raise  # Re-raise to be handled by the caller

    @database_sync_to_async
    def update_conversation_timestamp(self, conversation_id):
        """
        Update the conversation's timestamp.
        """
        from django.db import transaction

        with transaction.atomic():
            conversation = Conversation.objects.get(id=conversation_id)
            conversation.update_timestamp()

        return conversation

    @database_sync_to_async
    def get_other_participant(self, conversation_id, user_id):
        """
        Get the ID of the other participant in a conversation.

        Uses a single optimized query instead of loading the entire conversation
        and then querying its participants.

        Args:
            conversation_id: The ID of the conversation
            user_id: The ID of the current user

        Returns:
            The ID of the other participant, or None if not found
        """
        try:
            # Get the other participant in a single query
            other_participant_id = Conversation.objects.filter(
                id=conversation_id
            ).values_list(
                'participants__id', flat=True
            ).exclude(
                participants__id=user_id
            ).first()

            return other_participant_id
        except Exception as e:
            logger.error(f"Error getting other participant: {str(e)}", exc_info=True)
            return None

    @database_sync_to_async
    def mark_messages_as_read(self, conversation_id, user_id):
        """
        Mark all messages in a conversation as read for a user.

        Uses bulk_update for better performance instead of individual save calls.

        Args:
            conversation_id: The ID of the conversation
            user_id: The ID of the user marking messages as read

        Returns:
            The number of messages marked as read
        """
        from django.db import transaction

        try:
            with transaction.atomic():
                # Update all unread messages in a single query
                updated_count = Message.objects.filter(
                    conversation_id=conversation_id,
                    is_read=False
                ).exclude(sender_id=user_id).update(
                    is_read=True,
                    delivery_status='read'
                )
                return updated_count
        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}", exc_info=True)
            return 0

    @database_sync_to_async
    def is_user_online(self, user_id):
        """
        Check if a user is currently online.

        Args:
            user_id: The ID of the user to check

        Returns:
            Boolean indicating if the user is online
        """
        try:
            user_status = UserStatus.objects.filter(user_id=user_id, is_online=True).exists()
            return user_status
        except Exception as e:
            logger.error(f"Error checking user online status: {str(e)}", exc_info=True)
            return False

    @database_sync_to_async
    def update_message_status(self, message_id, status):
        """
        Update the delivery status of a message.

        Args:
            message_id: The ID of the message to update
            status: The new delivery status ('pending', 'delivered', 'read', 'failed')

        Returns:
            The updated Message object
        """
        from django.db import transaction

        try:
            with transaction.atomic():
                message = Message.objects.get(id=message_id)
                message.delivery_status = status

                if status == 'delivered' or status == 'read':
                    message.delivery_attempts += 1
                    message.last_delivery_attempt = timezone.now()

                message.save()
                return message
        except Exception as e:
            logger.error(f"Error updating message status: {str(e)}", exc_info=True)
            return None

    @database_sync_to_async
    def get_pending_messages_for_user(self, user_id):
        """
        Get all pending messages for a user.

        Args:
            user_id: The ID of the user

        Returns:
            List of pending Message objects
        """
        try:
            # Get all conversations the user is part of
            conversations = Conversation.objects.filter(participants__id=user_id)

            # Get all pending messages in those conversations where the user is not the sender
            pending_messages = Message.objects.filter(
                conversation__in=conversations,
                delivery_status='pending'
            ).exclude(sender_id=user_id).order_by('timestamp')

            return list(pending_messages)
        except Exception as e:
            logger.error(f"Error getting pending messages: {str(e)}", exc_info=True)
            return []

    async def deliver_pending_messages(self, user_id):
        """
        Deliver all pending messages for a user who has just come online.

        Args:
            user_id: The ID of the user who has come online

        Returns:
            Number of messages delivered
        """
        try:
            # Get all pending messages for the user
            pending_messages = await self.get_pending_messages_for_user(user_id)

            if not pending_messages:
                logger.info(f"No pending messages for user {user_id}")
                return 0

            logger.info(f"Delivering {len(pending_messages)} pending messages to user {user_id}")

            # Group messages by conversation for more efficient delivery
            messages_by_conversation = {}
            for message in pending_messages:
                conv_id = message.conversation_id
                if conv_id not in messages_by_conversation:
                    messages_by_conversation[conv_id] = []
                messages_by_conversation[conv_id].append(message)

            # Deliver messages for each conversation
            delivered_count = 0
            for conv_id, messages in messages_by_conversation.items():
                for message in messages:
                    # Update message status to delivered
                    await self.update_message_status(message.id, 'delivered')

                    # Prepare message data
                    sender = await self.get_user_info(message.sender_id)
                    message_data = {
                        "type": "chat_message",
                        "message": {
                            "id": message.id,
                            "content": message.content,
                            "timestamp": message.timestamp.isoformat(),
                            "sender_id": message.sender_id,
                            "sender_name": f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip() or sender.get(
                                'username', 'Unknown'),
                            "is_read": False,
                            "delivery_status": "delivered"
                        },
                        "conversation_id": conv_id
                    }

                    # Send to the user's personal group
                    await self.channel_layer.group_send(
                        f"user_{user_id}",
                        message_data
                    )

                    delivered_count += 1

            logger.info(f"Successfully delivered {delivered_count} pending messages to user {user_id}")
            return delivered_count

        except Exception as e:
            logger.error(f"Error delivering pending messages: {str(e)}", exc_info=True)
            return 0

    @database_sync_to_async
    def get_user_info(self, user_id):
        """
        Get basic user information.

        Args:
            user_id: The ID of the user

        Returns:
            Dictionary with user information
        """
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}", exc_info=True)
            return {'username': 'Unknown'}
