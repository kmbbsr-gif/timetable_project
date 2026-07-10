from django.db import models
from apps.schools.models import School

class Subject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    is_optional = models.BooleanField(default=False)
    requires_lab = models.BooleanField(default=False)
    requires_practical = models.BooleanField(default=False)
    min_gap_periods = models.PositiveSmallIntegerField(default=0)
    max_gap_periods = models.PositiveSmallIntegerField(default=99)
    default_double_period_allowed = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#6c757d', help_text='Hex colour code (e.g., #FF5733)')

    class Meta:
        unique_together = ['school', 'code']

    def __str__(self):
        return self.name