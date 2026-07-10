from django.db import models
from apps.schools.models import School

class Teacher(models.Model):
    # Core fields
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)

    # Workload limits
    max_daily_load = models.PositiveSmallIntegerField(default=8)
    max_weekly_load = models.PositiveSmallIntegerField(default=40)

    # Class teacher flags
    is_class_teacher = models.BooleanField(default=False)
    is_co_class_teacher = models.BooleanField(default=False)

    # Preferences & availability (JSON fields)
    preferred_periods = models.JSONField(default=list, blank=True)
    preferred_days = models.JSONField(default=list, blank=True)
    unavailable_days = models.JSONField(default=list, blank=True)
    unavailable_periods = models.JSONField(default=list, blank=True)

    # Daily exceptions
    half_day = models.BooleanField(default=False)
    late_arrival = models.TimeField(null=True, blank=True)
    early_departure = models.TimeField(null=True, blank=True)

    # Active status
    is_active = models.BooleanField(default=True)

    # NEW: Which class is this teacher the class teacher for?
    class_teacher_for = models.ForeignKey(
        'academic.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_teachers',
        help_text="If this teacher is a class teacher, select the class."
    )

    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Get the last teacher and increment
            last = Teacher.objects.order_by('id').last()
            if last and last.employee_id and last.employee_id.startswith('TCH'):
                try:
                    num = int(last.employee_id[3:]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.employee_id = f"TCH{num:04d}"
        super().save(*args, **kwargs)
    
    def total_assigned_periods(self):
        """Total periods assigned to this teacher via all subject assignments."""
        from django.db.models import Sum
        total = self.subject_assignments.aggregate(total=Sum('weekly_periods'))['total']
        return total if total else 0

    def remaining_periods(self):
        """Remaining periods the teacher can still take."""
        return self.max_weekly_load - self.total_assigned_periods()
    
    def save(self, *args, **kwargs):
        if not self.pk:  # new teacher
            avg = get_average_load()
            if avg > 0:
                self.max_weekly_load = avg
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TeacherSubjectAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='subject_assignments')
    class_subject = models.ForeignKey('academic.ClassSubject', on_delete=models.CASCADE, related_name='teacher_assignments')
    weekly_periods = models.PositiveSmallIntegerField()
    is_primary = models.BooleanField(default=False)   # optional: primary teacher for that subject
    preference_weight = models.FloatField(default=1.0) # for soft constraints

    class Meta:
        unique_together = ['teacher', 'class_subject']

    def __str__(self):
        return f"{self.teacher.name} – {self.class_subject}"