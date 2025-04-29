from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterAPIView,
    LoginAPIView,
    UserProfileAPIView,
    ProfilePictureUploadView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('profile/', UserProfileAPIView.as_view(), name='api-profile'),
    path('profile/upload-picture/', ProfilePictureUploadView.as_view(), name='api-profile-picture-upload'),
]
