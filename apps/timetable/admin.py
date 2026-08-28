from django.contrib import admin
from .models import TimetableEntry, SubstituteAssignment

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('class_instance', 'section', 'teacher', 'subject', 'day_of_week', 'period_number', 'room')
    list_filter = ('class_instance', 'day_of_week', 'teacher')
    search_fields = ('teacher__name', 'subject__name', 'class_instance__name')

@admin.register(SubstituteAssignment)
class SubstituteAssignmentAdmin(admin.ModelAdmin):
    list_display = ('absent_teacher', 'substitute_teacher', 'date', 'period_number', 'class_instance', 'section')
    list_filter = ('date', 'absent_teacher')
    search_fields = ('absent_teacher__name', 'substitute_teacher__name')