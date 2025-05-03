from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Post, Like, Comment


class PostModelTest(TestCase):
    """Test the Post model."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.post = Post.objects.create(
            user=self.user,
            content='This is a test post'
        )

    def test_post_creation(self):
        """Test that a post can be created."""
        self.assertEqual(self.post.content, 'This is a test post')
        self.assertEqual(self.post.user, self.user)

    def test_post_str_method(self):
        """Test the string representation of a post."""
        expected_str = f"Post by {self.user.username} on {self.post.created_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.post), expected_str)


class CommentModelTest(TestCase):
    """Test the Comment model."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.post = Post.objects.create(
            user=self.user,
            content='This is a test post'
        )

        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='This is a test comment'
        )

    def test_comment_creation(self):
        """Test that a comment can be created."""
        self.assertEqual(self.comment.content, 'This is a test comment')
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.post, self.post)

    def test_comment_str_method(self):
        """Test the string representation of a comment."""
        expected = f"Comment by {self.user.username} on {self.post}"
        self.assertEqual(str(self.comment), expected)


class LikeModelTest(TestCase):
    """Test the Like model."""

    def setUp(self):
        """Set up test data."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.post = Post.objects.create(
            user=self.user,
            content='This is a test post'
        )

        self.like = Like.objects.create(
            user=self.user,
            post=self.post
        )

    def test_like_creation(self):
        """Test that a like can be created."""
        self.assertEqual(self.like.user, self.user)
        self.assertEqual(self.like.post, self.post)

    def test_like_count(self):
        """Test that likes can be counted."""
        # Create another user and like
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword123'
        )
        Like.objects.create(
            user=user2,
            post=self.post
        )

        # Check that the post has 2 likes
        self.assertEqual(self.post.likes.count(), 2)
