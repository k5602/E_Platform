from django.db import transaction
from django.core.exceptions import PermissionDenied
from home.models import Post, Like
from home.utils import format_content_with_mentions
from home.forms import PostForm
import logging

logger = logging.getLogger(__name__)


class PostService:
    """Service class for post-related business logic."""

    @staticmethod
    def create_post(user, form_data, files=None):
        """Create a new post with proper validation and formatting."""
        from home.forms import PostForm

        with transaction.atomic():
            form = PostForm(form_data, files)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = user
                post.save()
                form.save_m2m()

                # Format content with mentions
                formatted_content = format_content_with_mentions(post.content)

                return {
                    "success": True,
                    "post": post,
                    "formatted_content": formatted_content,
                }
            else:
                return {"success": False, "errors": form.errors}

    @staticmethod
    def toggle_like(user, post_id):
        """Toggle like status for a post."""
        post = Post.objects.get(id=post_id)
        like, created = Like.objects.get_or_create(user=user, post=post)

        if not created:
            # User already liked the post, so unlike it
            like.delete()
            liked = False
        else:
            liked = True

        like_count = post.likes.count()

        return {"liked": liked, "like_count": like_count}

    @staticmethod
    def delete_post(user, post_id):
        """Delete a post if user has permission."""
        post = Post.objects.get(id=post_id)

        if post.user != user:
            raise PermissionDenied("You do not have permission to delete this post.")

        post.delete()
        return True

    @staticmethod
    def get_post_with_details(post_id):
        """Get a post with optimized related data."""
        return (
            Post.objects.select_related("user")
            .prefetch_related("likes__user", "comments__user")
            .get(id=post_id)
        )

    @staticmethod
    def get_posts_feed():
        """Get optimized posts feed for home page."""
        return (
            Post.objects.select_related("user")
            .prefetch_related("likes", "likes__user", "comments", "comments__user")
            .order_by("-created_at")
        )

    @staticmethod
    def get_post_likes_data(post_id):
        """Get likes data for a post."""
        post = Post.objects.get(id=post_id)
        likes = post.likes.select_related("user").order_by("-created_at")
        like_users = [like.user.username for like in likes]

        return {"like_count": likes.count(), "users": like_users}
