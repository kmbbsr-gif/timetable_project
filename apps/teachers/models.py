import re
from django.core.exceptions import ValidationError
from django.db import models
from apps.schools.models import School


class Teacher(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)

    max_daily_load = models.PositiveSmallIntegerField(default=8)
    max_weekly_load = models.PositiveSmallIntegerField(default=40)

    is_class_teacher = models.BooleanField(default=False)
    is_co_class_teacher = models.BooleanField(default=False)

    preferred_periods = models.JSONField(default=list, blank=True)
    preferred_days = models.JSONField(default=list, blank=True)
    unavailable_days = models.JSONField(default=list, blank=True)
    unavailable_periods = models.JSONField(default=list, blank=True)

    half_day = models.BooleanField(default=False)
    late_arrival = models.TimeField(null=True, blank=True)
    early_departure = models.TimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

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
            max_id = 0
            for t in Teacher.objects.all():
                if t.employee_id:
                    match = re.search(r'\d+$', t.employee_id)
                    if match:
                        num = int(match.group())
                        if num > max_id:
                            max_id = num
            self.employee_id = f"TCH{max_id + 1:04d}"

        if not self.pk and not self.max_weekly_load:
            from django.db.models import Sum
            total = TeacherSubjectAssignment.objects.aggregate(total=Sum('weekly_periods'))['total'] or 0
            active_count = Teacher.objects.filter(is_active=True).count()
            if active_count > 0:
                self.max_weekly_load = int(round(total / active_count))
            else:
                self.max_weekly_load = 40

        super().save(*args, **kwargs)

    def total_assigned_periods(self):
        from django.db.models import Sum
        total = self.subject_assignments.aggregate(total=Sum('weekly_periods'))['total']
        return total if total else 0

    def remaining_periods(self):
        return self.max_weekly_load - self.total_assigned_periods()

    def __str__(self):
        return self.name


class TeacherSubjectAssignment(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='subject_assignments'
    )
    class_subject = models.ForeignKey(
        'academic.ClassSubject',
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    weekly_periods = models.PositiveSmallIntegerField()
    is_primary = models.BooleanField(default=False)
    preference_weight = models.FloatField(default=1.0)

    is_combined = models.BooleanField(
        default=False,
        help_text="Check if this subject is taught as a joint/combined period across multiple classes/sections."
    )
    combined_group_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Required for combined classes. Use a unique label per group (e.g. 'Drawing-Standards')."
    )

    # NEW: Section-specific support
    target_sections = models.ManyToManyField(
        'academic.Section',
        blank=True,
        related_name='teacher_assignments',
        help_text='Leave empty to assign to ALL sections of this class. '
                  'Select specific sections to limit this assignment.'
    )

    class Meta:
        unique_together = ['teacher', 'class_subject']

    def clean(self):
        super().clean()
        if self.is_combined and not (self.combined_group_name or '').strip():
            raise ValidationError({
                'combined_group_name': 'Combined Group Label is required for combined classes.'
            })

    def __str__(self):
        status = "Combined" if self.is_combined else "Single"
        return f"{self.teacher.name} – {self.class_subject} ({status})"