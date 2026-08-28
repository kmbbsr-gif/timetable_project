from django.contrib import admin
from .models import Subject

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'school', 'is_optional', 'requires_lab')
    list_filter = ('school', 'is_optional', 'requires_lab')
    search_fields = ('code', 'name')