from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to home page if already logged in

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes

                # Redirect based on user type
                if user.user_type == 'admin':
                    return redirect('admin:index')  # Redirect to admin panel
                else:
                    return redirect('home')  # Redirect to home page
            else:
                messages.error(request, 'Invalid username or password')
        else:
            # Display specific form errors instead of a generic message
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"{error}")
                    else:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'authentication/login.html', {'form': form})

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'authentication/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return response

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def home_view(request):
    # Redirect to the home app's home view
    return redirect('home:home')


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """
    Custom password reset view that adds a success message and uses a custom template.
    """
    template_name = 'authentication/password_reset_form.html'
    email_template_name = 'authentication/password_reset_email.html'
    subject_template_name = 'authentication/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    success_message = "We've emailed you instructions for setting your password. " \
                      "If you don't receive an email, please make sure you've entered " \
                      "the address you registered with, and check your spam folder."

    def form_valid(self, form):
        """
        Add extra security by not revealing whether an email exists in the system.
        Always show success message even if email doesn't exist.
        """
        # Get the email from the form
        email = form.cleaned_data.get('email')

        # Check if the email exists in the system
        active_users = CustomUser.objects.filter(email=email, is_active=True)

        if not active_users.exists():
            # If email doesn't exist, still show success but don't send email
            # This prevents user enumeration
            return redirect(self.get_success_url())

        # If email exists, proceed with normal password reset
        return super().form_valid(form)
