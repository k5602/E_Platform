from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Password'})
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'remember-checkbox', 'class': 'remember-checkbox'})
    )

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
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirm Password'})
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
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'})
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'user_type', 'password1', 'password2', 'birthdate')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        admin_access_code = cleaned_data.get('admin_access_code')
        instructor_access_code = cleaned_data.get('instructor_access_code')

        if user_type == 'admin' and admin_access_code != 'KFS2025':
            raise ValidationError('Admin access code is incorrect')

        if user_type == 'instructor' and instructor_access_code != 'INS2025':
            raise ValidationError('Instructor access code is incorrect')

        return cleaned_data
