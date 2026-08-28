from django.core.exceptions import PermissionDenied


def get_user_school(user):
    """
    Retrieves the school instance associated with the given user.
    Returns None if unauthenticated or unassigned.
    """
    if not user or not user.is_authenticated:
        return None

    # 1. Cached profile relation
    profile = getattr(user, 'profile', None)
    if profile and hasattr(profile, 'school'):
        return profile.school

    # 2. Fallback direct lookup
    from apps.users.models import UserProfile
    try:
        user_profile = UserProfile.objects.select_related('school').get(user=user)
        return user_profile.school
    except UserProfile.DoesNotExist:
        return None