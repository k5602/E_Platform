from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import Post, Like, Comment, FAQ, Notification
from .forms import PostForm, CommentForm, ContactForm, AppointmentForm
from django.db import transaction
from authentication.models import CustomUser
from .utils import search_users
from .services.post_service import PostService
from .services.comment_service import CommentService
from .services.notification_service import NotificationService
from .services.search_service import SearchService
from .services.contact_service import ContactService


@login_required
def home_view(request):
    """Main home page view that displays the feed of posts."""
    # Handle post creation
    if request.method == "POST":
        # Handle post creation with transaction
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
            return redirect("home")
        # If form is invalid, continue to showing the feed
    else:
        form = PostForm()

    # Get optimized posts feed
    posts = PostService.get_posts_feed()

    # Pagination
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "form": form,
    }
    return render(request, "home/home.html", context)


@login_required
@require_POST
def create_post(request):
    """API endpoint for creating a new post."""
    try:
        result = PostService.create_post(request.user, request.POST, request.FILES)

        if result["success"]:
            post = result["post"]
            return JsonResponse(
                {
                    "status": "success",
                    "post_id": post.id,
                    "user": {
                        "username": request.user.username,
                        "first_name": request.user.first_name,
                        "last_name": request.user.last_name,
                    },
                    "content": post.content,
                    "formatted_content": result["formatted_content"],
                    "has_image": bool(post.image),
                    "has_video": bool(post.video),
                    "has_document": bool(post.document),
                    "image_url": post.image.url if post.image else None,
                    "video_url": post.video.url if post.video else None,
                    "document_url": post.document.url if post.document else None,
                    "document_name": post.document.name if post.document else None,
                    "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
                    "message": "Post created successfully!",
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "errors": result["errors"],
                    "message": "Failed to create post due to validation errors.",
                },
                status=400,
            )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error creating post: {str(e)}")

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while creating your post. Please try again.",
            },
            status=500,
        )


@login_required
@require_POST
def like_post(request, post_id):
    """API endpoint for liking/unliking a post."""
    try:
        result = PostService.toggle_like(request.user, post_id)

        return JsonResponse(
            {
                "status": "success",
                "liked": result["liked"],
                "like_count": result["like_count"],
            }
        )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in like_post view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while processing your like. Please try again.",
            },
            status=500,
        )


@login_required
@require_POST
def add_comment(request, post_id):
    """API endpoint for adding a comment to a post."""
    try:
        result = CommentService.create_comment(request.user, post_id, request.POST)

        if result["success"]:
            comment = result["comment"]
            return JsonResponse(
                {
                    "status": "success",
                    "comment_id": comment.id,
                    "user": comment.user.username,
                    "content": comment.content,
                    "formatted_content": result["formatted_content"],
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                    "profile_picture": (
                        comment.user.profile_picture.url
                        if comment.user.profile_picture
                        else None
                    ),
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "errors": result["errors"],
                    "message": "Failed to add comment.",
                },
                status=400,
            )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in add_comment view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while adding your comment. Please try again.",
            },
            status=500,
        )


@login_required
@require_POST
def delete_post(request, post_id):
    """API endpoint for deleting a post."""
    try:
        PostService.delete_post(request.user, post_id)

        return JsonResponse(
            {"status": "success", "message": "Post deleted successfully!"}
        )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in delete_post view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while deleting the post. Please try again.",
            },
            status=500,
        )


@login_required
@require_POST
def delete_comment(request, comment_id):
    """API endpoint for deleting a comment."""
    try:
        CommentService.delete_comment(request.user, comment_id)

        return JsonResponse(
            {"status": "success", "message": "Comment deleted successfully!"}
        )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in delete_comment view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while deleting the comment. Please try again.",
            },
            status=500,
        )


@require_GET
def get_post_comments(request, post_id):
    """API endpoint to fetch the latest comments for a post."""
    try:
        comments_data = CommentService.get_post_comments(post_id)
        return JsonResponse({"status": "success", "comments": comments_data})
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_post_comments view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while fetching comments. Please try again.",
            },
            status=500,
        )


@require_GET
def get_post_likes(request, post_id):
    """API endpoint to fetch the latest likes for a post."""
    try:
        result = PostService.get_post_likes_data(post_id)
        return JsonResponse(
            {
                "status": "success",
                "like_count": result["like_count"],
                "users": result["users"],
            }
        )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_post_likes view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while fetching likes. Please try again.",
            },
            status=500,
        )


def contact_view(request):
    """View for the contact page."""
    contact_form_submitted = False
    appointment_form_submitted = False

    # Handle contact form submission
    if request.method == "POST" and "contact_form" in request.POST:
        result = ContactService.handle_contact_form_submission(request.POST)
        if result["success"]:
            messages.success(request, result["message"])
            contact_form_submitted = True
            contact_form = ContactForm()  # Reset the form
        else:
            contact_form = result["form"]
        appointment_form = AppointmentForm()  # Empty form for GET request

    # Handle appointment form submission
    elif request.method == "POST" and "appointment_form" in request.POST:
        result = ContactService.handle_appointment_form_submission(
            request.POST, request.user if request.user.is_authenticated else None
        )
        if result["success"]:
            messages.success(request, result["message"])
            appointment_form_submitted = True
            appointment_form = AppointmentForm()  # Reset the form
        else:
            appointment_form = result["form"]
        contact_form = ContactForm()  # Empty form for GET request

    else:
        contact_form = ContactForm()
        appointment_form = AppointmentForm()

    # Get contact page data
    contact_data = ContactService.get_contact_page_data()

    context = {
        "contact_form": contact_form,
        "appointment_form": appointment_form,
        "contact_form_submitted": contact_form_submitted,
        "appointment_form_submitted": appointment_form_submitted,
        "active_page": "contact",
        "faqs": contact_data["faqs"],
        "categories": contact_data["categories"],
        "instructors": contact_data["instructors"],
    }
    return render(request, "home/contact.html", context)


# Notification and Mention System Views


@login_required
@require_GET
def get_notifications(request):
    """API endpoint to fetch user notifications."""
    try:
        notifications_data = NotificationService.get_user_notifications(request.user)
        unread_count = NotificationService.get_unread_count(request.user)

        response_data = {
            "status": "success",
            "notifications": notifications_data,
            "unread_count": unread_count,
        }

        return JsonResponse(response_data)
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_notifications view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while fetching notifications. Please try again.",
            },
            status=500,
        )


@login_required
@require_GET
def get_unread_notification_count(request):
    """API endpoint to get the count of unread notifications."""
    try:
        count = NotificationService.get_unread_count(request.user)
        return JsonResponse({"status": "success", "unread_count": count})
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error in get_unread_notification_count view: {str(e)}", exc_info=True
        )

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while fetching notification count. Please try again.",
            },
            status=500,
        )


@login_required
@require_POST
def mark_notification_read(request, notification_id=None):
    """API endpoint to mark notifications as read."""
    try:
        result = NotificationService.mark_notification_read(
            request.user, notification_id
        )

        return JsonResponse(
            {
                "status": "success",
                "message": result["message"],
                "unread_count": result["unread_count"],
            }
        )
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in mark_notification_read view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while marking notifications as read. Please try again.",
            },
            status=500,
        )


@login_required
@require_GET
def search_users_view(request):
    """API endpoint to search for users by username, first name, or last name."""
    try:
        query = request.GET.get("q", "").strip()
        users_data = SearchService.search_users_api(query, request.user)

        return JsonResponse({"status": "success", "users": users_data})
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in search_users_view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while searching for users. Please try again.",
            },
            status=500,
        )


@login_required
def notifications_view(request):
    """View for the notifications page."""
    return render(request, "home/notifications.html", {"active_page": "notifications"})


@login_required
def user_search_page(request):
    """View for searching users by name or username."""
    query = request.GET.get("q", "")

    if query:
        # Search for users by first name, last name, or username
        users = CustomUser.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
        ).distinct()

        # Paginate results
        paginator = Paginator(users, 20)  # Show 20 users per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "query": query,
            "page_obj": page_obj,
            "total_results": users.count(),
            "active_page": "home",
        }

        return render(request, "home/search_results.html", context)

    # If no query, redirect back to home
    return redirect("home:home")


@login_required
def search_suggestions(request):
    """API endpoint for search suggestions with autocomplete."""
    try:
        query = request.GET.get("q", "")
        suggestions = SearchService.get_search_suggestions(query, request.user)

        return JsonResponse({"suggestions": suggestions})
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error in search_suggestions view: {str(e)}", exc_info=True)

        # Return a generic error message
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred while fetching search suggestions. Please try again.",
            },
            status=500,
        )


# Helper function to format time ago
def get_time_ago(timestamp):
    """Return a human-readable string representing how long ago the timestamp was."""
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    diff = now - timestamp

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = diff.days // 365
        return f'{years} year{"s" if years != 1 else ""} ago'
