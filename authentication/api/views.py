from rest_framework import status, generics, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from PIL import Image
from io import BytesIO
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    RegisterSerializer,
    LoginSerializer
)


class RegisterAPIView(generics.CreateAPIView):
    """API view for user registration."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """API view for user login."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """API view for retrieving and updating user profile."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class ProfilePictureUploadView(APIView):
    """API view for uploading profile pictures."""

    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def post(self, request, format=None):
        """Handle profile picture upload."""
        if 'profile_picture' not in request.FILES:
            return Response({
                'error': 'No profile picture provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        profile_picture = request.FILES['profile_picture']

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_picture.content_type not in allowed_types:
            return Response({
                'error': 'Invalid file type. Only JPEG, PNG, and GIF are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            return Response({
                'error': 'File too large. Maximum size is 5MB.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Process image (resize if needed)
            img = Image.open(profile_picture)

            # Resize if larger than 1000x1000
            if img.width > 1000 or img.height > 1000:
                img.thumbnail((1000, 1000))

                # Save to BytesIO
                output = BytesIO()
                if profile_picture.content_type == 'image/jpeg':
                    img.save(output, format='JPEG', quality=85)
                elif profile_picture.content_type == 'image/png':
                    img.save(output, format='PNG')
                elif profile_picture.content_type == 'image/gif':
                    img.save(output, format='GIF')

                # Get the processed image
                output.seek(0)
                processed_image = ContentFile(output.read())

                # Generate a unique filename
                filename = f"profile_{request.user.id}_{os.path.splitext(profile_picture.name)[1]}"

                # Delete old profile picture if exists
                if request.user.profile_picture:
                    if os.path.isfile(request.user.profile_picture.path):
                        os.remove(request.user.profile_picture.path)

                # Save the new profile picture
                request.user.profile_picture.save(filename, processed_image, save=True)
            else:
                # If no resizing needed, just save the uploaded file

                # Delete old profile picture if exists
                if request.user.profile_picture:
                    if os.path.isfile(request.user.profile_picture.path):
                        os.remove(request.user.profile_picture.path)

                # Generate a unique filename
                filename = f"profile_{request.user.id}_{os.path.splitext(profile_picture.name)[1]}"

                # Save the new profile picture
                request.user.profile_picture.save(filename, profile_picture, save=True)

            return Response({
                'message': 'Profile picture uploaded successfully',
                'profile_picture': request.user.profile_picture.url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Error processing image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
