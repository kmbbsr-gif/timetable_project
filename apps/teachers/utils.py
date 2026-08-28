from django.db.models import Sum
from .models import Teacher, TeacherSubjectAssignment

def get_average_load():
    total_periods = TeacherSubjectAssignment.objects.aggregate(total=Sum('weekly_periods'))['total'] or 0
    active_teachers = Teacher.objects.filter(is_active=True).count()
    if active_teachers == 0:
        return 0
    return int(round(total_periods / active_teachers))