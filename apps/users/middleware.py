from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths accessible to unauthenticated visitors
        exempt_urls = (
            '/users/login/',
            '/users/logout/',
            '/schools/register-school/',
            '/api/v1/register-school/',
            '/system-master-panel-99/',
            '/static/',
            '/media/',
            '/favicon.ico',
        )

        path = request.path_info

        # 1. Allow access if path matches exempt list
        if any(path.startswith(url) for url in exempt_urls):
            return self.get_response(request)

        # 2. If user is not logged in, redirect to login page with 'next' parameter
        if not request.user.is_authenticated:
            login_url = reverse('login')
            # Avoid redirect loop if login page itself is requested
            if path != login_url:
                return redirect(f"{login_url}?next={path}")

        return self.get_response(request)