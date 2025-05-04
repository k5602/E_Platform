from django.urls import path

from . import consumers

websocket_urlpatterns = [
    # Single, clear pattern for chat WebSocket
    path('ws/chat/', consumers.ChatConsumer.as_asgi()),
]
