from django.db import models
from django.utils.translation import gettext_lazy as _

BOARD_CHOICES = [
    ('CBSE', 'CBSE'),
    ('ICSE', 'ICSE'),
    ('STATE', 'State Board'),
    ('OTHER', 'Other'),
]

class School(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    board = models.CharField(max_length=20, choices=BOARD_CHOICES, default='CBSE')
    affiliation_no = models.CharField(max_length=50, unique=True)
    udise_code = models.CharField(max_length=20, unique=True)
    school_code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    principal_name = models.CharField(max_length=255)
    vice_principal_name = models.CharField(max_length=255, blank=True)
    academic_coordinator = models.CharField(max_length=255, blank=True)
    exam_incharge = models.CharField(max_length=255, blank=True)
    session_start = models.DateField()
    session_end = models.DateField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name