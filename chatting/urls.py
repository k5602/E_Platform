from django.urls import path, include
from . import views
from chatting.api.views import UnreadMessageCountView

app_name = 'chatting'

urlpatterns = [
    # Web interface URLs
    path('', views.chat_home, name='chat_home'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('users/', views.users_list, name='users_list'),

    # API URLs
    path('api/', include('chatting.api.urls')),

    # Direct API endpoints
    path('api/unread-count/', UnreadMessageCountView.as_view(), name='unread_count'),
]