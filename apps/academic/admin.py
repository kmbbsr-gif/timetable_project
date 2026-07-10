from django.contrib import admin
from .models import AcademicSession, Class, Section, Room, ClassSubject, PeriodDefinition

admin.site.register(AcademicSession)
admin.site.register(Class)
admin.site.register(Section)
admin.site.register(Room)
admin.site.register(ClassSubject)
admin.site.register(PeriodDefinition)