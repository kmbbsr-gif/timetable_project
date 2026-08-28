from apps.schools.models import School


class TenantMiddleware:
    """
    Sets request.school for superusers (session-based switching).
    For non-superusers, request.school is set ONLY for convenience,
    but views MUST re-resolve via get_user_school() for security.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.school = None

        if request.user.is_authenticated:
            if request.user.is_superuser:
                selected_school_id = (
                    request.session.get('master_selected_school_id')
                    or request.session.get('active_school_id')
                )
                if selected_school_id:
                    request.school = School.objects.filter(id=selected_school_id).first()
            else:
                # Regular users: resolve via profile only.
                # NEVER use request.user.school — it may be a stale property.
                school = None
                profile = getattr(request.user, 'profile', None)
                if profile and hasattr(profile, 'school'):
                    school = profile.school

                if not school:
                    try:
                        from apps.utils.tenancy import get_user_school
                        school = get_user_school(request.user)
                    except Exception:
                        school = None

                request.school = school

        response = self.get_response(request)
        return response