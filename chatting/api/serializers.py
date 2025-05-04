from django.contrib.auth import get_user_model
from rest_framework import serializers

from chatting.models import Conversation, Message, UserStatus

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(read_only=True)
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'online_status']

    def get_online_status(self, obj):
        try:
            return obj.chat_status.is_online
        except UserStatus.DoesNotExist:
            return False


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_picture = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_name', 'sender_picture',
            'content', 'timestamp', 'is_read', 'delivery_status',
            'is_edited', 'edited_timestamp', 'is_deleted', 'deleted_timestamp',
            'file_attachment', 'file_url', 'file_type', 'file_name', 'file_size'
        ]

    def get_sender_name(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.username
        return None

    def get_sender_picture(self, obj):
        if obj.sender and obj.sender.profile_picture:
            return obj.sender.profile_picture.url
        return None

    def get_file_url(self, obj):
        if obj.file_attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_attachment.url)
            return obj.file_attachment.url
        return None


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return Message.objects.filter(conversation=obj, is_read=False).exclude(sender=user).count()


class StartConversationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)

    def validate_user_id(self, value):
        try:
            User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value


class UserStatusSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserStatus
        fields = ['user', 'is_online', 'last_active']
