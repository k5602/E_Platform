from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Use a more flexible pattern for user_id to match both numeric and string IDs
    re_path(r'ws/notifications/(?P<user_id>[^/]+)/$', consumers.NotificationConsumer.as_asgi()),
]
