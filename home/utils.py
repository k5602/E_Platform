import re
import random
from authentication.models import CustomUser
from .utils_cache import (
    cache_response, cache_model_method, clear_model_cache, 
    cached_property_with_ttl, timed_cache
)

def extract_mentions(text):
    """
    Extract @username mentions from text and return a list of valid user objects
    """
    if not text:
        return []

    # Find all @username patterns - match word characters after @
    pattern = r'@([a-zA-Z0-9_]+)'
    usernames = re.findall(pattern, text)

    # Debug information
    print(f"Found usernames in text: {usernames}")

    # Get valid users from the database
    if usernames:
        users = []
        for username in usernames:
            try:
                # Try to find each user individually with case-insensitive matching
                user = CustomUser.objects.get(username__iexact=username)
                users.append(user)
                print(f"Found user: {user.username}")
            except CustomUser.DoesNotExist:
                print(f"User not found: {username}")
            except CustomUser.MultipleObjectsReturned:
                # In case multiple users match (shouldn't happen with iexact)
                print(f"Multiple users found for: {username}")
                matching_users = CustomUser.objects.filter(username__iexact=username)
                users.extend(list(matching_users))

        # Return list of user objects
        return users

    return []

def format_content_with_mentions(content):
    """
    Format content by converting @username mentions to HTML links
    """
    if not content:
        return content

    # Replace @username with HTML link - match word characters after @
    pattern = r'@([a-zA-Z0-9_]+)'

    def replace_mention(match):
        username = match.group(1)
        # Check if user exists
        try:
            # Debug information
            print(f"Formatting mention for username: {username}")
            user = CustomUser.objects.get(username__iexact=username)
            print(f"Found user for formatting: {user.username}")
            return f'<a href="#" class="mention" data-username="{user.username}">@{user.username}</a>'
        except CustomUser.DoesNotExist:
            print(f"User not found for formatting: {username}")
            return f'@{username}'
        except Exception as e:
            print(f"Error formatting mention for {username}: {str(e)}")
            return f'@{username}'

    return re.sub(pattern, replace_mention, content)

def search_users(query, exclude_user=None, limit=10):
    """
    Search for users by username, first_name, or last_name
    If query is empty, return a limited set of users
    """
    if not query:
        # Return a limited set of users when query is empty
        users = CustomUser.objects.all()
    else:
        # Search for users matching the query
        users = CustomUser.objects.filter(
            username__icontains=query
        ) | CustomUser.objects.filter(
            first_name__icontains=query
        ) | CustomUser.objects.filter(
            last_name__icontains=query
        )

    # Exclude the current user if provided
    if exclude_user:
        users = users.exclude(id=exclude_user.id)

    # Limit results and return
    return users.distinct()[:limit]
