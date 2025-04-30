from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import Post, Like, Comment, Contact, FAQ, Appointment, Notification
from .forms import PostForm, CommentForm, ContactForm, AppointmentForm
from django.db import transaction
from authentication.models import CustomUser
from .utils import search_users, format_content_with_mentions
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def home_view(request):
    """Main home page view that displays the feed of posts."""
    posts = Post.objects.select_related('user').prefetch_related('likes', 'comments').all()

    # Pagination
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Handle post creation
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('home')
    else:
        form = PostForm()

    context = {
        'page_obj': page_obj,
        'form': form,
    }
    return render(request, 'home/home.html', context)

@login_required
@require_POST
def create_post(request):
    """API endpoint for creating a new post."""
    try:
        # Use a transaction to ensure all database operations are atomic
        with transaction.atomic():
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                # Create post but don't save to database yet
                post = form.save(commit=False)
                post.user = request.user

                # Save the post to the database
                post.save()

                # Save the form to create any related objects
                form.save_m2m()

                # Format content with mentions
                from home.utils import format_content_with_mentions
                formatted_content = format_content_with_mentions(post.content)

                # Return success response with post details
                return JsonResponse({
                    'status': 'success',
                    'post_id': post.id,
                    'user': {
                        'username': request.user.username,
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name
                    },
                    'content': post.content,
                    'formatted_content': formatted_content,
                    'has_image': bool(post.image),
                    'has_video': bool(post.video),
                    'has_document': bool(post.document),
                    'image_url': post.image.url if post.image else None,
                    'video_url': post.video.url if post.video else None,
                    'document_url': post.document.url if post.document else None,
                    'document_name': post.document.name if post.document else None,
                    'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                    'message': 'Post created successfully!'
                })
            else:
                # Return form validation errors
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors,
                    'message': 'Failed to create post due to validation errors.'
                }, status=400)
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating post: {str(e)}")

        # Return a generic error message
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred while creating your post. Please try again.'
        }, status=500)

@login_required
@require_POST
def like_post(request, post_id):
    """API endpoint for liking/unliking a post."""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        # User already liked the post, so unlike it
        like.delete()
        liked = False
    else:
        liked = True

    like_count = post.likes.count()

    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'like_count': like_count
    })

@login_required
@require_POST
def add_comment(request, post_id):
    """API endpoint for adding a comment to a post."""
    post = get_object_or_404(Post, id=post_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        comment.save()

        # Format content with mentions
        from home.utils import format_content_with_mentions
        formatted_content = format_content_with_mentions(comment.content)

        return JsonResponse({
            'status': 'success',
            'comment_id': comment.id,
            'user': comment.user.username,
            'content': comment.content,
            'formatted_content': formatted_content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'profile_picture': comment.user.profile_picture.url if comment.user.profile_picture else None
        })

    return JsonResponse({
        'status': 'error',
        'errors': form.errors,
        'message': 'Failed to add comment.'
    }, status=400)

@login_required
@require_POST
def delete_post(request, post_id):
    """API endpoint for deleting a post."""
    post = get_object_or_404(Post, id=post_id)

    # Only allow the post owner to delete it
    if post.user != request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to delete this post.'
        }, status=403)

    post.delete()

    return JsonResponse({
        'status': 'success',
        'message': 'Post deleted successfully!'
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    """API endpoint for deleting a comment."""
    comment = get_object_or_404(Comment, id=comment_id)

    # Only allow the comment owner to delete it
    if comment.user != request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to delete this comment.'
        }, status=403)

    comment.delete()

    return JsonResponse({
        'status': 'success',
        'message': 'Comment deleted successfully!'
    })

@require_GET
def get_post_comments(request, post_id):
    """API endpoint to fetch the latest comments for a post."""
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('user').order_by('-created_at')

    # Import format_content_with_mentions
    from home.utils import format_content_with_mentions

    comments_data = [
        {
            'id': c.id,
            'user': c.user.username,
            'content': c.content,
            'formatted_content': format_content_with_mentions(c.content),
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
            'profile_picture': c.user.profile_picture.url if c.user.profile_picture else None
        }
        for c in comments
    ]
    return JsonResponse({'status': 'success', 'comments': comments_data})

@require_GET
def get_post_likes(request, post_id):
    """API endpoint to fetch the latest likes for a post."""
    post = get_object_or_404(Post, id=post_id)
    likes = post.likes.select_related('user').order_by('-created_at')
    like_users = [like.user.username for like in likes]
    return JsonResponse({'status': 'success', 'like_count': likes.count(), 'users': like_users})

def contact_view(request):
    """View for the contact page."""
    contact_form_submitted = False
    appointment_form_submitted = False

    # Handle contact form submission
    if request.method == 'POST' and 'contact_form' in request.POST:
        contact_form = ContactForm(request.POST)
        appointment_form = AppointmentForm()  # Empty form for GET request
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, "Thank you! Your message has been sent successfully.")
            contact_form_submitted = True
            contact_form = ContactForm()  # Reset the form
    # Handle appointment form submission
    elif request.method == 'POST' and 'appointment_form' in request.POST:
        appointment_form = AppointmentForm(request.POST)
        contact_form = ContactForm()  # Empty form for GET request
        if appointment_form.is_valid():
            appointment = appointment_form.save(commit=False)

            # If user is logged in, associate the appointment with them
            if request.user.is_authenticated:
                appointment.user = request.user

            # Find the first instructor
            instructors = CustomUser.objects.filter(is_staff=True).first()
            if instructors:
                appointment.instructor = instructors

            appointment.save()
            messages.success(request, "Thank you! Your appointment request has been submitted. We'll confirm it shortly.")
            appointment_form_submitted = True
            appointment_form = AppointmentForm()  # Reset the form
    else:
        contact_form = ContactForm()
        appointment_form = AppointmentForm()

    # Get active FAQs and their unique categories
    faqs = FAQ.objects.filter(is_active=True).order_by('order', 'question')
    categories = faqs.values_list('category', flat=True).distinct()

    # Get available instructors for appointment booking
    instructors = CustomUser.objects.filter(is_staff=True)

    context = {
        'contact_form': contact_form,
        'appointment_form': appointment_form,
        'contact_form_submitted': contact_form_submitted,
        'appointment_form_submitted': appointment_form_submitted,
        'active_page': 'contact',
        'faqs': faqs,
        'categories': categories,
        'instructors': instructors
    }
    return render(request, 'home/contact.html', context)


# Notification and Mention System Views

@login_required
@require_GET
def get_notifications(request):
    """API endpoint to fetch user notifications."""
    notifications = Notification.objects.filter(recipient=request.user).select_related(
        'sender', 'post', 'comment'
    ).order_by('-created_at')[:20]  # Limit to 20 most recent

    notifications_data = []
    for notification in notifications:
        data = {
            'id': notification.id,
            'type': notification.notification_type,
            'text': notification.text,
            'sender': {
                'username': notification.sender.username,
                'first_name': notification.sender.first_name,
                'last_name': notification.sender.last_name,
            },
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'time_ago': get_time_ago(notification.created_at)
        }

        # Add post info if available
        if notification.post:
            data['post'] = {
                'id': notification.post.id,
                'content_preview': notification.post.content[:50] + '...' if len(notification.post.content) > 50 else notification.post.content
            }

        # Add comment info if available
        if notification.comment:
            data['comment'] = {
                'id': notification.comment.id,
                'content_preview': notification.comment.content[:50] + '...' if len(notification.comment.content) > 50 else notification.comment.content
            }

        notifications_data.append(data)

    return JsonResponse({
        'status': 'success',
        'notifications': notifications_data,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })

@login_required
@require_GET
def get_unread_notification_count(request):
    """API endpoint to get the count of unread notifications."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({
        'status': 'success',
        'unread_count': count
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id=None):
    """API endpoint to mark notifications as read."""
    if notification_id:
        # Mark a specific notification as read
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        message = 'Notification marked as read'
    else:
        # Mark all notifications as read
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        message = 'All notifications marked as read'

    return JsonResponse({
        'status': 'success',
        'message': message,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })

@login_required
@require_GET
def search_users_view(request):
    """API endpoint to search for users by username, first name, or last name."""
    query = request.GET.get('q', '').strip()
    # Allow empty queries - will return a limited set of users

    users = search_users(query, exclude_user=request.user)

    users_data = [
        {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'user_type': user.user_type
        }
        for user in users
    ]

    return JsonResponse({
        'status': 'success',
        'users': users_data
    })

@login_required
def notifications_view(request):
    """View for the notifications page."""
    return render(request, 'home/notifications.html', {
        'active_page': 'notifications'
    })

@login_required
def debug_mentions_view(request):
    """Debug view for testing the mention system."""
    return render(request, 'home/debug_mentions.html', {
        'active_page': 'debug'
    })

@login_required
def debug_notifications_view(request):
    """Debug view for testing the notification system."""
    notifications = Notification.objects.all().select_related('recipient', 'sender').order_by('-created_at')[:50]
    return render(request, 'home/debug_notifications.html', {
        'active_page': 'debug',
        'notifications': notifications
    })

@login_required
@require_POST
def create_test_notification(request):
    """Create a test notification."""
    recipient_username = request.POST.get('recipient')
    notification_type = request.POST.get('notification_type')
    text = request.POST.get('text')

    try:
        recipient = CustomUser.objects.get(username=recipient_username)

        notification = Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type=notification_type,
            text=text
        )

        messages.success(request, f'Notification created successfully with ID: {notification.id}')
    except CustomUser.DoesNotExist:
        messages.error(request, f'User with username {recipient_username} does not exist')
    except Exception as e:
        messages.error(request, f'Error creating notification: {str(e)}')

    return redirect('home:debug_notifications')

@login_required
@require_POST
def test_extract_mentions(request):
    """Test the extract_mentions function."""
    import json
    data = json.loads(request.body)
    text = data.get('text', '')

    from home.utils import extract_mentions
    mentioned_users = extract_mentions(text)

    return JsonResponse({
        'status': 'success',
        'mentioned_users': [
            {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            for user in mentioned_users
        ]
    })

@login_required
def search_users(request):
    """View for searching users by name or username."""
    query = request.GET.get('q', '')

    if query:
        # Search for users by first name, last name, or username
        users = CustomUser.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        ).distinct()

        # Paginate results
        paginator = Paginator(users, 20)  # Show 20 users per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'query': query,
            'page_obj': page_obj,
            'total_results': users.count(),
            'active_page': 'home',
        }

        return render(request, 'home/search_results.html', context)

    # If no query, redirect back to home
    return redirect('home:home')


@login_required
def search_suggestions(request):
    """API endpoint for search suggestions with autocomplete."""
    query = request.GET.get('q', '')

    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})

    # Search for users by first name, last name, or username
    users = CustomUser.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query)
    ).distinct()[:10]  # Limit to 10 suggestions

    suggestions = []
    for user in users:
        profile_pic_url = user.profile_picture.url if user.profile_picture else None
        suggestions.append({
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}",
            'profile_pic': profile_pic_url,
            'user_type': user.user_type,
            'url': f"/home/profile/{user.username}/"
        })

    return JsonResponse({'suggestions': suggestions})


# Helper function to format time ago
def get_time_ago(timestamp):
    """Return a human-readable string representing how long ago the timestamp was."""
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    diff = now - timestamp

    if diff < timedelta(minutes=1):
        return 'just now'
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
