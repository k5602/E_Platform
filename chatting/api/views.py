from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status, permissions, pagination, parsers
from rest_framework.response import Response
from rest_framework.views import APIView

from chatting.models import Conversation, Message, UserStatus
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    StartConversationSerializer,
    UserSerializer,
    UserStatusSerializer
)

User = get_user_model()

class ConversationListView(generics.ListAPIView):
    """API view for listing all conversations for the current user."""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)


class ConversationDetailView(generics.RetrieveAPIView):
    """API view for retrieving a specific conversation."""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)


class StartConversationView(APIView):
    """API view for starting a new conversation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = StartConversationSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            initial_message = serializer.validated_data.get('message', '')

            # Don't allow starting a conversation with yourself
            if user_id == request.user.id:
                return Response(
                    {"error": "You cannot start a conversation with yourself."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the user to start a conversation with
            try:
                other_user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if a conversation already exists between these users
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=other_user
            ).first()

            # If no conversation exists, create a new one
            if conversation is None:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, other_user)
                conversation.save()

            # Create an initial message if one was provided
            if initial_message:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=initial_message
                )
                # Update the conversation timestamp
                conversation.update_timestamp()

            # Return the conversation details
            return Response(
                ConversationSerializer(conversation, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageListView(generics.ListAPIView):
    """API view for listing messages in a conversation with pagination."""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = pagination.PageNumberPagination

    def get_queryset(self):
        conversation_id = self.kwargs.get('pk')

        # Get pagination parameters
        page_size = self.request.query_params.get('page_size', 50)
        try:
            page_size = int(page_size)
            # Limit page size to prevent performance issues
            page_size = min(max(10, page_size), 100)
            self.pagination_class.page_size = page_size
        except (ValueError, TypeError):
            pass

        # Get before_id parameter for cursor-based pagination
        before_id = self.request.query_params.get('before_id')
        after_id = self.request.query_params.get('after_id')

        try:
            # Check if the user is a participant in the conversation
            conversation = Conversation.objects.filter(
                id=conversation_id,
                participants=self.request.user
            ).select_related().first()

            if not conversation:
                return Message.objects.none()

            # Mark all unread messages as read
            unread_messages = Message.objects.filter(
                conversation=conversation,
                is_read=False
            ).exclude(sender=self.request.user)

            # Use bulk update for better performance
            for message in unread_messages:
                message.is_read = True
                message.delivery_status = 'read'

            if unread_messages:
                Message.objects.bulk_update(unread_messages, ['is_read', 'delivery_status'])

            # Base queryset
            queryset = Message.objects.filter(conversation=conversation)

            # Apply cursor-based pagination if requested
            if before_id:
                try:
                    oldest_message = Message.objects.get(id=before_id)
                    queryset = queryset.filter(timestamp__lt=oldest_message.timestamp)
                except Message.DoesNotExist:
                    pass

            if after_id:
                try:
                    newest_message = Message.objects.get(id=after_id)
                    queryset = queryset.filter(timestamp__gt=newest_message.timestamp)
                except Message.DoesNotExist:
                    pass

            return queryset.order_by('-timestamp')

        except Conversation.DoesNotExist:
            return Message.objects.none()


class AddMessageView(APIView):
    """API view for adding a message to a conversation, with support for file attachments."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def post(self, request, pk, *args, **kwargs):
        try:
            conversation = Conversation.objects.get(
                id=pk,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found or you don't have permission."},
                status=status.HTTP_404_NOT_FOUND
            )

        content = request.data.get('content', '').strip()
        file_attachment = request.FILES.get('file_attachment')

        # Check if we have either content or a file
        if not content and not file_attachment:
            return Response(
                {"error": "Message must have either content or a file attachment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the message with basic fields
        message = Message(
            conversation=conversation,
            sender=request.user,
            content=content,
            is_read=True  # Messages are always read by the sender
        )

        # Handle file attachment if present
        if file_attachment:
            # Get file size
            file_size = file_attachment.size

            # Get original file name
            file_name = file_attachment.name

            # Determine file type based on content type or extension
            content_type = file_attachment.content_type
            file_type = 'other'

            if content_type.startswith('image/'):
                file_type = 'image'
            elif content_type.startswith('audio/'):
                file_type = 'audio'
            elif content_type.startswith('video/'):
                file_type = 'video'
            elif content_type.startswith('application/') or content_type.startswith('text/'):
                file_type = 'document'

            # Set file metadata
            message.file_attachment = file_attachment
            message.file_type = file_type
            message.file_name = file_name
            message.file_size = file_size

        # Save the message
        message.save()

        # Update the conversation timestamp
        conversation.update_timestamp()

        # Return the serialized message
        serializer = MessageSerializer(message, context={'request': request})
        response_data = serializer.data

        # Ensure file_url is included if file_attachment exists
        if response_data.get('file_attachment') and not response_data.get('file_url'):
            response_data['file_url'] = request.build_absolute_uri(message.file_attachment.url)

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


class UserListView(generics.ListAPIView):
    """API view for listing all users with their online status."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')

        # Exclude the current user and search for users
        queryset = User.objects.exclude(id=self.request.user.id)

        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        return queryset


class UserStatusView(generics.RetrieveAPIView):
    """API view for retrieving a user's online status."""
    serializer_class = UserStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user_id = self.kwargs.get('pk')
        try:
            user = User.objects.get(pk=user_id)
            status_obj, created = UserStatus.objects.get_or_create(user=user)
            return status_obj
        except User.DoesNotExist:
            return None


class UpdateUserStatusView(APIView):
    """API view for updating the current user's online status."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        is_online = request.data.get('is_online', True)

        status_obj, created = UserStatus.objects.get_or_create(user=request.user)
        status_obj.is_online = is_online

        if not is_online:
            status_obj.last_active = timezone.now()

        status_obj.save()

        return Response(
            UserStatusSerializer(status_obj).data,
            status=status.HTTP_200_OK
        )


class UnreadMessageCountView(APIView):
    """API view for getting the count of unread messages for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all conversations for the current user
        conversations = Conversation.objects.filter(participants=request.user)

        # Count unread messages across all conversations
        unread_count = 0
        for conversation in conversations:
            unread_count += Message.objects.filter(
                conversation=conversation,
                is_read=False,
                is_deleted=False  # Don't count deleted messages
            ).exclude(sender=request.user).count()

        return Response({
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)


class EditMessageView(APIView):
    """API view for editing a message."""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk, *args, **kwargs):
        try:
            # Get the message and verify ownership
            message = Message.objects.get(pk=pk, sender=request.user)

            # Check if message is deleted
            if message.is_deleted:
                return Response(
                    {"error": "Cannot edit a deleted message."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get new content
            content = request.data.get('content', '').strip()

            if not content:
                return Response(
                    {"error": "Message content cannot be empty."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Edit the message
            message.edit_message(content)

            # Return the updated message
            return Response(
                MessageSerializer(message).data,
                status=status.HTTP_200_OK
            )

        except Message.DoesNotExist:
            return Response(
                {"error": "Message not found or you don't have permission to edit it."},
                status=status.HTTP_404_NOT_FOUND
            )


class MarkMessagesReadView(APIView):
    """API view for marking all messages in a conversation as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            # Get the conversation and verify the user is a participant
            conversation = Conversation.objects.get(
                id=pk,
                participants=request.user
            )

            # Mark all unread messages from other users as read
            unread_count = Message.objects.filter(
                conversation=conversation,
                is_read=False
            ).exclude(
                sender=request.user
            ).update(
                is_read=True,
                delivery_status='read'
            )

            return Response({
                'success': True,
                'marked_read': unread_count
            })

        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found or you don't have permission."},
                status=status.HTTP_404_NOT_FOUND
            )


class DeleteMessageView(APIView):
    """API view for deleting a message."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, *args, **kwargs):
        try:
            # Get the message and verify ownership
            message = Message.objects.get(pk=pk, sender=request.user)

            # Soft delete the message
            message.delete_message()

            # Return success response
            return Response(
                {"message": "Message deleted successfully."},
                status=status.HTTP_200_OK
            )

        except Message.DoesNotExist:
            return Response(
                {"error": "Message not found or you don't have permission to delete it."},
                status=status.HTTP_404_NOT_FOUND
            )
