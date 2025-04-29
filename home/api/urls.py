from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet,
    CommentViewSet,
    NotificationViewSet,
    UserSearchAPIView,
    PostSearchAPIView
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='api-post')
router.register(r'comments', CommentViewSet, basename='api-comment')
router.register(r'notifications', NotificationViewSet, basename='api-notification')

urlpatterns = [
    path('', include(router.urls)),
    path('users/search/', UserSearchAPIView.as_view(), name='api-user-search'),
    path('posts/search/', PostSearchAPIView.as_view(), name='api-post-search'),
]
