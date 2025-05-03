from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone

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
    """API view for listing messages in a conversation."""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs.get('pk')

        try:
            # Check if the user is a participant in the conversation
            conversation = Conversation.objects.filter(
                id=conversation_id,
                participants=self.request.user
            ).first()

            if not conversation:
                return Message.objects.none()

            # Mark all unread messages as read
            unread_messages = Message.objects.filter(
                conversation=conversation,
                is_read=False
            ).exclude(sender=self.request.user)

            for message in unread_messages:
                message.mark_as_read()

            return Message.objects.filter(conversation=conversation)

        except Conversation.DoesNotExist:
            return Message.objects.none()


class AddMessageView(APIView):
    """API view for adding a message to a conversation."""
    permission_classes = [permissions.IsAuthenticated]

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

        if not content:
            return Response(
                {"error": "Message content cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        # Update the conversation timestamp
        conversation.update_timestamp()

        return Response(
            MessageSerializer(message).data,
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
                is_read=False
            ).exclude(sender=request.user).count()

        return Response({
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)