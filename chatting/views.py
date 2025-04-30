from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.db.models import Q

from .models import Conversation, Message, UserStatus

User = get_user_model()

@login_required
def chat_home(request):
    """
    Main chat page showing a list of all conversations.
    """
    # Get all conversations for the current user
    conversations = Conversation.objects.filter(participants=request.user)
    
    # Get unread message counts for each conversation
    for conversation in conversations:
        conversation.unread_count = Message.objects.filter(
            conversation=conversation,
            sender__isnull=False,
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Get the other participant in the conversation
        conversation.other_user = conversation.get_other_participant(request.user)
        
    # Get users who are online
    online_users = User.objects.filter(chat_status__is_online=True).exclude(id=request.user.id)
    
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
    """
    # Get the conversation or return 404 if not found
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if the current user is a participant in the conversation
    if request.user not in conversation.participants.all():
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('chatting:chat_home')
    
    # Get all messages in the conversation
    messages_list = conversation.messages.all()
    
    # Mark all unread messages as read
    unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
    for message in unread_messages:
        message.mark_as_read()
    
    # Get the other participant in the conversation
    other_user = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_user': other_user,
        'active_page': 'chat',
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
    """
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id)
    
    # Search functionality
    query = request.GET.get('q', '')
    if query:
        users = users.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )
    
    context = {
        'users': users,
        'search_query': query,
        'active_page': 'chat',
    }
    
    return render(request, 'chatting/users_list.html', context)
