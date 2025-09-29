import logging
import re
import random
from datetime import datetime, timezone
from authentication.models import CustomUser

logger = logging.getLogger(__name__)


def get_time_ago(timestamp):
    """
    Convert a timestamp to a human-readable "time ago" string.

    Args:
        timestamp: A datetime object or ISO string

    Returns:
        String like "2 hours ago", "3 days ago", etc.
    """
    if isinstance(timestamp, str):
        # Parse ISO string if needed
        try:
            from dateutil import parser

            timestamp = parser.parse(timestamp)
        except ImportError:
            # Fallback if dateutil not available
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    # Ensure timestamp is timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - timestamp

    # Calculate time differences
    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    if seconds < 60:
        return "just now"
    elif minutes < 60:
        return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
    elif hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
    elif days < 7:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
    else:
        return timestamp.strftime("%b %d, %Y")


def extract_mentions(text):
    """
    Extract @username mentions from text and return a list of valid user objects
    """
    if not text:
        return []

    # Find all @username patterns - match word characters after @
    pattern = r"@([a-zA-Z0-9_]+)"
    usernames = re.findall(pattern, text)

    # Debug information
    logger.debug(f"Found usernames in text: {usernames}")

    # Get valid users from the database
    if usernames:
        users = []
        for username in usernames:
            try:
                # Try to find each user individually with case-insensitive matching
                user = CustomUser.objects.get(username__iexact=username)
                users.append(user)
                logger.debug(f"Found user: {user.username}")
            except CustomUser.DoesNotExist:
                logger.debug(f"User not found: {username}")
            except CustomUser.MultipleObjectsReturned:
                # In case multiple users match (shouldn't happen with iexact)
                logger.debug(f"Multiple users found for: {username}")
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
    pattern = r"@([a-zA-Z0-9_]+)"

    def replace_mention(match):
        username = match.group(1)
        # Check if user exists
        try:
            # Debug information
            logger.debug(f"Formatting mention for username: {username}")
            user = CustomUser.objects.get(username__iexact=username)
            logger.debug(f"Found user for formatting: {user.username}")
            return f'<a href="#" class="mention" data-username="{user.username}">@{user.username}</a>'
        except CustomUser.DoesNotExist:
            logger.debug(f"User not found for formatting: {username}")
            return f"@{username}"
        except Exception as e:
            logger.error(f"Error formatting mention for {username}: {str(e)}")
            return f"@{username}"

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
        users = (
            CustomUser.objects.filter(username__icontains=query)
            | CustomUser.objects.filter(first_name__icontains=query)
            | CustomUser.objects.filter(last_name__icontains=query)
        )

    # Exclude the current user if provided
    if exclude_user:
        users = users.exclude(id=exclude_user.id)

    # Limit results and return
    return users.distinct()[:limit]
