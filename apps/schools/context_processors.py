# apps/schools/context_processors.py
from .models import School

def active_tenant_context(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return {
            'all_schools_for_master': School.objects.all().order_by('name'),
            'current_active_school': getattr(request, 'school', None),
        }
    return {
        'all_schools_for_master': [],
        'current_active_school': getattr(request, 'school', None),
    }