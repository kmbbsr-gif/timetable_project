from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied


def group_required(*group_names):
    """
    Decorator that checks if the logged-in user belongs to any of the specified groups.
    Superusers bypass group checks automatically.
    Loop-protected against redirecting login paths back to themselves.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            login_url = reverse('login')

            # 1. If unauthenticated, redirect to login (unless already on the login page)
            if not request.user.is_authenticated:
                if request.path.startswith(login_url):
                    return view_func(request, *args, **kwargs)
                return redirect(f"{login_url}?next={request.path}")

            # 2. Superusers bypass all group checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # 3. Check group membership
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)

            # 4. Authenticated but unauthorized
            raise PermissionDenied("You do not have access to this section.")

        return wrapper
    return decorator