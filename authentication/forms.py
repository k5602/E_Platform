from datetime import date

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Username'}),
        error_messages={'required': 'Please enter your username'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input password-field', 'placeholder': 'Password'}),
        error_messages={'required': 'Please enter your password'}
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'remember-checkbox', 'class': 'remember-checkbox'})
    )

    error_messages = {
        'invalid_login': 'Please enter a correct username and password. Note that both fields may be case-sensitive.',
        'inactive': 'This account is inactive. Please contact the administrator.',
    }

    def clean(self):
        """
        Override the default clean method to provide generic error messages
        that don't reveal whether a username exists or not.
        """
        try:
            return super().clean()
        except forms.ValidationError as e:
            # Use a generic error message to prevent user enumeration
            if 'Please enter a correct username and password' in str(e):
                self.add_error(None, 'Invalid username or password. Please try again.')
                return self.cleaned_data
            # Re-raise the original error
            raise

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Last name'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input password-field', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input password-field', 'placeholder': 'Confirm Password'})
    )
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    admin_access_code = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Admin Access Code'})
    )
    instructor_access_code = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Instructor Access Code'})
    )
    birthdate = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
        help_text='You must be between 17 and 40 years old to register.'
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'user_type', 'password1', 'password2', 'birthdate')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        admin_access_code = cleaned_data.get('admin_access_code')
        instructor_access_code = cleaned_data.get('instructor_access_code')
        birthdate = cleaned_data.get('birthdate')

        if user_type == 'admin' and admin_access_code != settings.ADMIN_ACCESS_CODE:
            raise ValidationError('Admin access code is incorrect')

        if user_type == 'instructor' and instructor_access_code != settings.INSTRUCTOR_ACCESS_CODE:
            raise ValidationError('Instructor access code is incorrect')

        # Age validation
        if not birthdate:
            raise ValidationError('Birthdate is required.')

        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        if age < 17:
            raise ValidationError('You must be at least 17 years old to register.')

        if age > 40:
            raise ValidationError('You must be no older than 40 years old to register.')

        return cleaned_data
