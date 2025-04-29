from rest_framework import serializers
from home.models import Post, Comment, Like, Notification
from authentication.models import CustomUser
from home.utils import extract_mentions, format_content_with_mentions


class UserMiniSerializer(serializers.ModelSerializer):
    """Simplified serializer for user data in nested relationships."""
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'user_type')


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for the Comment model."""
    
    user = UserMiniSerializer(read_only=True)
    formatted_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'content', 'formatted_content', 'created_at')
        read_only_fields = ('id', 'user', 'created_at', 'formatted_content')
    
    def get_formatted_content(self, obj):
        """Return content with formatted mentions."""
        return format_content_with_mentions(obj.content)
    
    def create(self, validated_data):
        """Create a new comment and process mentions."""
        # Get the user from the context
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Create the comment
        comment = Comment.objects.create(**validated_data)
        
        return comment


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for the Like model."""
    
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ('id', 'user', 'post', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class PostSerializer(serializers.ModelSerializer):
    """Serializer for the Post model."""
    
    user = UserMiniSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    formatted_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ('id', 'user', 'content', 'formatted_content', 'image', 'video', 
                  'document', 'created_at', 'updated_at', 'comments_count', 
                  'likes_count', 'is_liked')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 
                           'comments_count', 'likes_count', 'is_liked', 
                           'formatted_content')
    
    def get_comments_count(self, obj):
        """Return the number of comments for the post."""
        return obj.comments.count()
    
    def get_likes_count(self, obj):
        """Return the number of likes for the post."""
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        """Return whether the current user has liked the post."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False
    
    def get_formatted_content(self, obj):
        """Return content with formatted mentions."""
        return format_content_with_mentions(obj.content)
    
    def create(self, validated_data):
        """Create a new post and process mentions."""
        # Get the user from the context
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Create the post
        post = Post.objects.create(**validated_data)
        
        return post


class PostDetailSerializer(PostSerializer):
    """Detailed serializer for the Post model including comments."""
    
    comments = CommentSerializer(many=True, read_only=True, source='comments.all')
    
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ('comments',)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for the Notification model."""
    
    recipient = UserMiniSerializer(read_only=True)
    sender = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ('id', 'recipient', 'sender', 'notification_type', 
                  'text', 'is_read', 'created_at', 'post', 'comment')
        read_only_fields = ('id', 'recipient', 'sender', 'notification_type', 
                           'text', 'created_at', 'post', 'comment')


class UserSearchSerializer(serializers.ModelSerializer):
    """Serializer for user search results."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'user_type')
    
    def get_full_name(self, obj):
        """Return the user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()
