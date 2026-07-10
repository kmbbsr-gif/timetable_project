from django.db import models
from apps.schools.models import School
from apps.subjects.models import Subject

WING_CHOICES = [
    ('Junior', 'Junior'),
    ('Middle', 'Middle'),
    ('Senior', 'Senior'),
]

class AcademicSession(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # e.g., "2025-2026"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Class(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)  # e.g., "Class VI"
    display_order = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['school', 'name']
        ordering = ['display_order']

    def __str__(self):
        return self.name

class Section(models.Model):
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=5)  # A, B, C...
    student_strength = models.PositiveIntegerField(default=0)
    working_days = models.JSONField(default=list)  # list of ints 0-6
    wing = models.CharField(max_length=10, choices=WING_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['class_instance', 'name']

    def __str__(self):
        return f"{self.class_instance} - {self.name}"

class Room(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('Classroom', 'Classroom'), ('Lab', 'Lab'), ('Library', 'Library'), ('Sports', 'Sports'), ('Assembly', 'Assembly')])
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ClassSubject(models.Model):
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    weekly_periods = models.PositiveSmallIntegerField()
    double_period_allowed = models.BooleanField(default=False)
    practical_required = models.BooleanField(default=False)
    lab_required = models.BooleanField(default=False)
    consecutive_allowed = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ['class_instance', 'subject']

    def __str__(self):
        return f"{self.class_instance} - {self.subject}"

class PeriodDefinition(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='period_definitions')
    wing = models.CharField(max_length=10, choices=WING_CHOICES)
    period_number = models.PositiveSmallIntegerField()
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES, null=True, blank=True,
                                                   help_text="Leave blank for all days, or select a specific day for exceptions.")
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField()
    is_assembly = models.BooleanField(default=False)
    is_lunch = models.BooleanField(default=False)
    is_break = models.BooleanField(default=False)
    break_duration = models.PositiveSmallIntegerField(default=0)
    special_activity = models.CharField(max_length=100, blank=True, null=True,
                                        help_text="e.g., MPT, Yoga, Games, Library")