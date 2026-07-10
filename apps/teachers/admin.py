from django.contrib import admin
from .models import Teacher, TeacherSubjectAssignment

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_id', 'school', 'designation', 'is_active')
    list_filter = ('school', 'designation', 'is_active')
    search_fields = ('name', 'employee_id', 'email', 'mobile')

@admin.register(TeacherSubjectAssignment)
class TeacherSubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'class_subject', 'weekly_periods', 'is_primary')
    list_filter = ('teacher__school', 'is_primary')
    search_fields = ('teacher__name', 'class_subject__subject__name')