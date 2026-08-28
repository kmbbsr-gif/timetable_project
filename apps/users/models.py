from django.db import models
from django.contrib.auth.models import User
from apps.schools.models import School


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('SCHOOL_ADMIN', 'School Admin / Principal'),
        ('COORDINATOR', 'Timetable Coordinator'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student / Parent'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='user_profiles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} ({self.school.name})"