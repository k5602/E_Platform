from django.db.models import Q
from authentication.models import CustomUser
from home.utils import search_users
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Service class for search-related business logic."""

    @staticmethod
    def search_users_api(query, user, exclude_user=None):
        """Search for users via API."""
        users = search_users(query, exclude_user=exclude_user or user)

        users_data = [
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "user_type": user.user_type,
            }
            for user in users
        ]

        return users_data

    @staticmethod
    def get_search_suggestions(query, user):
        """Get search suggestions for autocomplete."""
        if not query or len(query) < 2:
            return []

        # Search for users by first name, last name, or username
        users = CustomUser.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
        ).distinct()[
            :10
        ]  # Limit to 10 suggestions

        suggestions = []
        for user in users:
            profile_pic_url = user.profile_picture.url if user.profile_picture else None
            suggestions.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "full_name": f"{user.first_name} {user.last_name}",
                    "profile_pic": profile_pic_url,
                    "user_type": user.user_type,
                    "url": f"/home/profile/{user.username}/",
                }
            )

        return suggestions

    @staticmethod
    def search_users_page(query):
        """Search for users for page display with pagination."""
        if not query:
            return None

        # Search for users by first name, last name, or username
        users = CustomUser.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
        ).distinct()

        return users
