from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from home.models import Post, Comment, Like, Notification
from authentication.models import CustomUser
from .serializers import (
    PostSerializer,
    PostDetailSerializer,
    CommentSerializer,
    LikeSerializer,
    NotificationSerializer,
    UserSearchSerializer
)
from home.utils import search_users


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for the Post model."""

    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'updated_at', 'likes__count', 'comments__count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return filtered posts, ordered by specified criteria."""
        queryset = Post.objects.select_related('user').prefetch_related('likes', 'comments').all()

        # Filter by user if specified
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Filter by media type if specified
        has_image = self.request.query_params.get('has_image')
        has_video = self.request.query_params.get('has_video')
        has_document = self.request.query_params.get('has_document')

        if has_image == 'true':
            queryset = queryset.exclude(image='')
        elif has_image == 'false':
            queryset = queryset.filter(image='')

        if has_video == 'true':
            queryset = queryset.exclude(video='')
        elif has_video == 'false':
            queryset = queryset.filter(video='')

        if has_document == 'true':
            queryset = queryset.exclude(document='')
        elif has_document == 'false':
            queryset = queryset.filter(document='')

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer

    def perform_create(self, serializer):
        """Save the post with the current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like or unlike a post."""
        post = self.get_object()
        user = request.user

        # Check if the user has already liked the post
        like, created = Like.objects.get_or_create(user=user, post=post)

        if not created:
            # User already liked the post, so unlike it
            like.delete()
            return Response({
                'status': 'success',
                'liked': False,
                'like_count': post.likes.count()
            })

        return Response({
            'status': 'success',
            'liked': True,
            'like_count': post.likes.count()
        })

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """List or create comments for a post."""
        post = self.get_object()

        if request.method == 'GET':
            comments = post.comments.select_related('user').order_by('-created_at')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = CommentSerializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save(user=request.user, post=post)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for the Comment model."""

    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return filtered comments, ordered by specified criteria."""
        queryset = Comment.objects.select_related('user', 'post').all()

        # Filter by post if specified
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)

        # Filter by user if specified
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        """Save the comment with the current user."""
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for the Notification model."""

    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text', 'sender__username', 'notification_type']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return filtered notifications for the current user."""
        queryset = Notification.objects.filter(
            recipient=self.request.user
        ).select_related('recipient', 'sender', 'post', 'comment')

        # Filter by read status if specified
        is_read = self.request.query_params.get('is_read')
        if is_read == 'true':
            queryset = queryset.filter(is_read=True)
        elif is_read == 'false':
            queryset = queryset.filter(is_read=False)

        # Filter by notification type if specified
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'success'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get the count of unread notifications."""
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'status': 'success', 'unread_count': count})


class UserSearchAPIView(generics.ListAPIView):
    """API view for searching users."""

    serializer_class = UserSearchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Search for users based on the query parameter."""
        query = self.request.query_params.get('q', '').strip()
        exclude_user = self.request.user

        return search_users(query, exclude_user=exclude_user)


class PostSearchAPIView(generics.ListAPIView):
    """API view for advanced post searching."""

    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Advanced search for posts with multiple criteria.

        Query parameters:
        - q: Search term for content
        - user: Username to filter by
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        - has_media: true/false
        - min_likes: Minimum number of likes
        - min_comments: Minimum number of comments
        - sort_by: created_at, likes, comments
        - order: asc, desc
        """
        queryset = Post.objects.select_related('user').prefetch_related('likes', 'comments').all()

        # Text search
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(content__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        # User filter
        username = self.request.query_params.get('user', '').strip()
        if username:
            queryset = queryset.filter(user__username__iexact=username)

        # Date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # Media filter
        has_media = self.request.query_params.get('has_media')
        if has_media == 'true':
            queryset = queryset.filter(
                Q(image__isnull=False, image__gt='') |
                Q(video__isnull=False, video__gt='') |
                Q(document__isnull=False, document__gt='')
            )
        elif has_media == 'false':
            queryset = queryset.filter(
                Q(image='') | Q(image__isnull=True),
                Q(video='') | Q(video__isnull=True),
                Q(document='') | Q(document__isnull=True)
            )

        # Annotate with counts for sorting and filtering
        queryset = queryset.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True)
        )

        # Minimum likes/comments filter
        min_likes = self.request.query_params.get('min_likes')
        min_comments = self.request.query_params.get('min_comments')
        if min_likes and min_likes.isdigit():
            queryset = queryset.filter(likes_count__gte=int(min_likes))
        if min_comments and min_comments.isdigit():
            queryset = queryset.filter(comments_count__gte=int(min_comments))

        # Sorting
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        order = self.request.query_params.get('order', 'desc')

        if sort_by == 'likes':
            sort_field = '-likes_count' if order == 'desc' else 'likes_count'
        elif sort_by == 'comments':
            sort_field = '-comments_count' if order == 'desc' else 'comments_count'
        else:  # default to created_at
            sort_field = '-created_at' if order == 'desc' else 'created_at'

        return queryset.order_by(sort_field)
