from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.views import LoginView

from apps.users.models import UserProfile


# ---------------------- Login View ----------------------

# ---------------------- General User Registration ----------------------
@transaction.atomic
def register(request):
    """
    Self-service registration for staff/teachers.
    (School Admins register via /schools/register-school/)
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        # Validations
        if not username or not password1:
            messages.error(request, "Username and password are required.")
            return render(request, 'registration/register.html')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'registration/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'registration/register.html')

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'registration/register.html')

        # 1. Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # 2. Assign Default Group ('Teacher')
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        user.groups.add(teacher_group)

        # 3. Create Associated Profile (if not already handled by signals)
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'TEACHER'}
        )

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('login')

    return render(request, 'registration/register.html')

def login_view(request):
    """
    Handles user login for both usernames and email addresses.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # 1. Try standard username authentication
        user = authenticate(request, username=username_or_email, password=password)

        # 2. Fallback to email lookup if username fails
        if user is None and '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")

            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and not next_url.startswith('/users/login'):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """
    Logs out the user and redirects to login.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')