from django.urls import path

from . import views

app_name = 'chat_api'

urlpatterns = [
    # Conversation APIs
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/start/', views.StartConversationView.as_view(), name='start_conversation'),
    path('conversations/<int:pk>/messages/', views.MessageListView.as_view(), name='message_list'),
    path('conversations/<int:pk>/add_message/', views.AddMessageView.as_view(), name='add_message'),
    path('conversations/<int:pk>/mark_read/', views.MarkMessagesReadView.as_view(), name='mark_messages_read'),

    # User status APIs
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/status/', views.UserStatusView.as_view(), name='user_status'),
    path('users/status/update/', views.UpdateUserStatusView.as_view(), name='update_user_status'),

    # Message count API
    path('unread-count/', views.UnreadMessageCountView.as_view(), name='unread_count'),

    # Message editing and deletion APIs
    path('messages/<int:pk>/edit/', views.EditMessageView.as_view(), name='edit_message'),
    path('messages/<int:pk>/delete/', views.DeleteMessageView.as_view(), name='delete_message'),
]
