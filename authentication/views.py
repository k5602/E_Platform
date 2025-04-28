from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
            messages.error(request, 'Invalid form submission')
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
