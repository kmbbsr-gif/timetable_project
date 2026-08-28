from django.db import models
from apps.schools.models import School
from apps.academic.models import AcademicSession, Class, Section, Room, ClassSubject
from apps.teachers.models import Teacher
from apps.subjects.models import Subject

DAY_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]

# class PeriodDefinition(models.Model):
#     school = models.ForeignKey(School, on_delete=models.CASCADE)
#     wing = models.CharField(max_length=10, choices=[('Junior', 'Junior'), ('Middle', 'Middle'), ('Senior', 'Senior')])
#     period_number = models.PositiveSmallIntegerField()
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     duration_minutes = models.PositiveSmallIntegerField()
#     is_assembly = models.BooleanField(default=False)
#     is_lunch = models.BooleanField(default=False)
#     is_break = models.BooleanField(default=False)
#     break_duration = models.PositiveSmallIntegerField(default=0)

#     class Meta:
#         unique_together = ['school', 'wing', 'period_number']
#         ordering = ['wing', 'period_number']

#     def __str__(self):
#         return f"{self.wing} P{self.period_number}"

class TimetableEntry(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)   # only once
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    period_number = models.PositiveSmallIntegerField()
    is_double = models.BooleanField(default=False)
    is_practical = models.BooleanField(default=False)
    is_fixed = models.BooleanField(default=False)   # <-- add this
    is_combined = models.BooleanField(default=False, help_text="True if this period is shared with another section/class")
    combined_group_id = models.CharField(max_length=50, blank=True, null=True, help_text="Unique ID pairing joint sections together")
    class Meta:
        unique_together = ['school', 'session', 'class_instance', 'section', 'day_of_week', 'period_number']
        indexes = [
            models.Index(fields=['class_instance', 'section', 'day_of_week', 'period_number']),
            models.Index(fields=['teacher', 'day_of_week', 'period_number']),
        ]

    def __str__(self):
        return f"{self.class_instance} - {self.section} - {self.day_of_week} P{self.period_number}"

from apps.academic.models import Subject  # import directly

class SubstituteAssignment(models.Model):
    absent_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='absences')
    substitute_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='substitutions')
    date = models.DateField()
    period_number = models.PositiveSmallIntegerField()
    class_instance = models.ForeignKey('academic.Class', on_delete=models.CASCADE)
    section = models.ForeignKey('academic.Section', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)  # use imported class
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['absent_teacher', 'date', 'period_number', 'class_instance', 'section']
# apps/timetable/models.py
class TimetableVersion(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    version = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['school', 'session']
    def __str__(self):
        return f"{self.school.name} - {self.session.name} - {self.version}"                                  
        
        