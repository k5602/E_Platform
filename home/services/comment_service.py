from django.core.exceptions import PermissionDenied
from home.models import Comment
from home.forms import CommentForm
from home.utils import format_content_with_mentions
import logging

logger = logging.getLogger(__name__)


class CommentService:
    """Service class for comment-related business logic."""

    @staticmethod
    def create_comment(user, post_id, form_data):
        """Create a new comment on a post."""
        from home.models import Post

        post = Post.objects.get(id=post_id)
        form = CommentForm(form_data)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = user
            comment.post = post
            comment.save()

            # Format content with mentions
            formatted_content = format_content_with_mentions(comment.content)

            return {
                "success": True,
                "comment": comment,
                "formatted_content": formatted_content,
            }
        else:
            return {"success": False, "errors": form.errors}

    @staticmethod
    def delete_comment(user, comment_id):
        """Delete a comment if user has permission."""
        comment = Comment.objects.get(id=comment_id)

        if comment.user != user:
            raise PermissionDenied("You do not have permission to delete this comment.")

        comment.delete()
        return True

    @staticmethod
    def get_post_comments(post_id):
        """Get comments for a post with optimized queries."""
        from home.models import Post

        post = Post.objects.get(id=post_id)
        comments = post.comments.select_related("user").order_by("-created_at")

        comments_data = []
        for comment in comments:
            comments_data.append(
                {
                    "id": comment.id,
                    "user": comment.user.username,
                    "content": comment.content,
                    "formatted_content": format_content_with_mentions(comment.content),
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                    "profile_picture": (
                        comment.user.profile_picture.url
                        if comment.user.profile_picture
                        else None
                    ),
                }
            )

        return comments_data
