from rest_framework import serializers
from django.contrib.auth import authenticate
from authentication.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the CustomUser model."""

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'user_type', 'birthdate', 'date_joined', 'is_active', 'profile_picture')
        read_only_fields = ('id', 'date_joined', 'is_active')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'user_type', 'birthdate', 'profile_picture')
        read_only_fields = ('id', 'username', 'user_type')


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'password2',
                  'first_name', 'last_name', 'user_type', 'birthdate')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'birthdate': {'required': True}
        }

    def validate(self, data):
        """Validate that passwords match."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Passwords don't match."})
        return data

    def create(self, validated_data):
        """Create and return a new user."""
        # Remove password2 from validated data
        validated_data.pop('password2', None)

        # Create user with create_user method to properly hash password
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'student'),
            birthdate=validated_data.get('birthdate', None)
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate user credentials."""
        username = data.get('username', '')
        password = data.get('password', '')

        if not username or not password:
            raise serializers.ValidationError("Please provide both username and password.")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials. Please try again.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Add user to validated data
        data['user'] = user
        return data
