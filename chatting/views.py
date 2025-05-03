from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import Conversation

User = get_user_model()

@login_required
def chat_home(request):
    """
    Main chat page showing a list of all conversations.

    Uses annotations to efficiently get unread message counts in a single query
    instead of querying the database for each conversation.
    """
    from django.db.models import Count, Q

    # Get all conversations with unread counts in a single query
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) &
                   ~Q(messages__sender=request.user) &
                   Q(messages__sender__isnull=False)
        )
    ).prefetch_related(
        'participants'
    ).order_by('-updated_at')

    # Get the other participant for each conversation
    for conversation in conversations:
        conversation.other_user = conversation.get_other_participant(request.user)

    # Get users who are online
    online_users = User.objects.filter(
        chat_status__is_online=True
    ).exclude(
        id=request.user.id
    )

    context = {
        'conversations': conversations,
        'online_users': online_users,
        'active_page': 'chat',
    }

    return render(request, 'chatting/chat_home.html', context)

@login_required
def conversation_detail(request, conversation_id):
    """
    View for displaying a specific conversation.

    Implements pagination for messages and optimized queries for better
    performance with long conversation histories.
    """
    from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

    # Get the conversation or return 404 if not found
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Check if the current user is a participant in the conversation
    if request.user not in conversation.participants.all():
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('chatting:chat_home')

    # Get messages with pagination
    page = request.GET.get('page', 1)
    messages_query = conversation.messages.all().select_related('sender').order_by('timestamp')

    # Mark all unread messages as read in a single query for better performance
    unread_count = messages_query.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(
        is_read=True
    )

    # Paginate results - 50 messages per page
    paginator = Paginator(messages_query, 50)

    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        messages_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        messages_page = paginator.page(paginator.num_pages)

    # Get the other participant in the conversation
    other_user = conversation.get_other_participant(request.user)

    context = {
        'conversation': conversation,
        'messages': messages_page,
        'other_user': other_user,
        'active_page': 'chat',
        'unread_count': unread_count,  # Could be useful for notifications
    }

    return render(request, 'chatting/conversation_detail.html', context)

@login_required
def start_conversation(request, user_id):
    """
    Start a new conversation with a user or redirect to an existing one.
    """
    # Get the user to start a conversation with
    other_user = get_object_or_404(User, id=user_id)

    # Don't allow starting a conversation with yourself
    if other_user == request.user:
        messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('chatting:chat_home')

    # Check if a conversation already exists between these users
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()

    # If no conversation exists, create a new one
    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        conversation.save()

    # Redirect to the conversation detail page
    return redirect('chatting:conversation_detail', conversation_id=conversation.id)

@login_required
def users_list(request):
    """
    View for displaying a list of users to chat with.

    Implements pagination and optimized queries for better performance
    with large user bases.
    """
    from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

    # Get query parameters
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    # Base query - exclude current user and select related fields for efficiency
    users_query = User.objects.exclude(
        id=request.user.id
    ).select_related(
        'chat_status'  # Optimize by pre-fetching related status
    ).order_by(
        'username'  # Consistent ordering
    )

    # Apply search filter if provided
    if query:
        users_query = users_query.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )

    # Paginate results - 20 users per page
    paginator = Paginator(users_query, 20)

    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        users_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        users_page = paginator.page(paginator.num_pages)

    context = {
        'users': users_page,
        'search_query': query,
        'active_page': 'chat',
    }

    return render(request, 'chatting/users_list.html', context)
