from django import forms
from django.contrib.auth.models import User, Group
from django.db import transaction

from .models import Teacher, TeacherSubjectAssignment
from apps.academic.models import ClassSubject, Section
from apps.users.models import UserProfile

DAY_CHOICES = [
    (0, "Mon"), (1, "Tue"), (2, "Wed"),
    (3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun"),
]

PERIOD_CHOICES = [(str(i), f"Period {i}") for i in range(1, 16)]


def _class_subject_label(cs: ClassSubject) -> str:
    sections = Section.objects.filter(
        class_instance=cs.class_instance, is_active=True
    ).values_list("name", flat=True)
    sec_str = f"  [{', '.join(sections)}]" if sections else ""
    return f"{cs.class_instance.name}{sec_str}  —  {cs.subject.name}"


class TeacherForm(forms.ModelForm):
    # Optional password for creating or updating user portal credentials
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Initial login password"}),
        help_text="Provide an initial password to create portal login credentials for this teacher."
    )

    preferred_days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select preferred teaching days.",
    )
    unavailable_days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select days the teacher is NOT available.",
    )
    preferred_periods = forms.MultipleChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={"size": "6", "class": "form-select"}),
        help_text="Hold Ctrl/Cmd to select multiple periods.",
    )
    unavailable_periods = forms.MultipleChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={"size": "6", "class": "form-select"}),
        help_text="Hold Ctrl/Cmd to select multiple periods.",
    )

    class Meta:
        model = Teacher
        fields = [
            "name", "employee_id", "mobile", "email", "password",
            "designation", "department",
            "max_daily_load", "max_weekly_load",
            "is_class_teacher", "class_teacher_for", "is_co_class_teacher",
            "preferred_periods", "preferred_days",
            "unavailable_days", "unavailable_periods",
            "half_day", "late_arrival", "early_departure",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teacher Full Name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "teacher@school.com"}),
            "employee_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Auto-generated if left blank"}),
            "mobile": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional"}),
            "designation": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. PGT Physics"}),
            "department": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Science"}),
            "class_teacher_for": forms.Select(attrs={"class": "form-select"}),
            "late_arrival": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "early_departure": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "max_daily_load": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 15}),
            "max_weekly_load": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 50}),
            "is_class_teacher": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_co_class_teacher": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "half_day": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, school=None, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)
        for field_name in ("preferred_periods", "unavailable_periods"):
            if field_name in self.fields:
                self.fields[field_name].required = False

        # Filter class choices to the active school
        if self.school and "class_teacher_for" in self.fields:
            from apps.academic.models import Class
            self.fields["class_teacher_for"].queryset = Class.objects.filter(
                school=self.school
            ).order_by("display_order", "name")

    def clean_preferred_days(self):
        return [int(d) for d in self.cleaned_data.get("preferred_days", [])]

    def clean_unavailable_days(self):
        return [int(d) for d in self.cleaned_data.get("unavailable_days", [])]

    def clean_preferred_periods(self):
        return [int(p) for p in self.cleaned_data.get("preferred_periods", [])]

    def clean_unavailable_periods(self):
        return [int(p) for p in self.cleaned_data.get("unavailable_periods", [])]

    @transaction.atomic
    def save(self, commit=True):
        teacher = super().save(commit=False)
        if self.school:
            teacher.school = self.school

        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")
        name = self.cleaned_data.get("name", "")

        # Provision linked Django User account if email and password are provided
        if email and password:
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": name}
            )
            if created or password:
                user.set_password(password)
                user.save()

            teacher_group, _ = Group.objects.get_or_create(name="Teacher")
            user.groups.add(teacher_group)

            if self.school:
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={"school": self.school, "role": "TEACHER"}
                )

            if hasattr(teacher, "user"):
                teacher.user = user

        if commit:
            teacher.save()
            self.save_m2m()

        return teacher


class TeacherSubjectAssignmentForm(forms.ModelForm):
    target_sections = forms.ModelMultipleChoiceField(
        queryset=Section.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Leave empty to assign to ALL sections. Select specific sections to limit.",
    )
    combined_class_subjects = forms.ModelMultipleChoiceField(
        queryset=ClassSubject.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
        help_text="Hold Ctrl (or Cmd) to select multiple joint sections.",
    )

    class Meta:
        model = TeacherSubjectAssignment
        fields = [
            "teacher",
            "class_subject",
            "target_sections",
            "combined_class_subjects",
            "weekly_periods",
            "is_primary",
            "preference_weight",
            "is_combined",
            "combined_group_name",
        ]
        widgets = {
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "class_subject": forms.Select(attrs={"class": "form-select", "id": "id_class_subject"}),
            "weekly_periods": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "preference_weight": forms.NumberInput(attrs={"class": "form-control"}),
            "is_combined": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_is_combined"}),
            "combined_group_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Std 6A + 6B Combined Games"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Standards ordered numerically by display_order
        qs = ClassSubject.objects.select_related("class_instance", "subject").order_by(
            "class_instance__display_order", "subject__name"
        )
        
        if "class_subject" in self.fields:
            self.fields["class_subject"].queryset = qs
            self.fields["class_subject"].required = False
            self.fields["class_subject"].label_from_instance = _class_subject_label

        self.fields["combined_class_subjects"].queryset = qs
        self.fields["combined_class_subjects"].label_from_instance = _class_subject_label

        self.fields["target_sections"].queryset = Section.objects.filter(
            is_active=True
        ).select_related("class_instance").order_by("class_instance__display_order", "name")

        if self.instance and self.instance.pk and self.instance.class_subject:
            self.fields["target_sections"].queryset = Section.objects.filter(
                class_instance=self.instance.class_subject.class_instance,
                is_active=True,
            ).order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        is_combined = cleaned_data.get("is_combined")
        class_subject = cleaned_data.get("class_subject")
        target_sections = cleaned_data.get("target_sections")
        combined_class_subjects = cleaned_data.get("combined_class_subjects")
        combined_group_name = (cleaned_data.get("combined_group_name") or "").strip()

        if is_combined:
            if target_sections and target_sections.exists():
                raise forms.ValidationError(
                    "Combined assignments use 'Combined Class Subjects'. Clear 'Target Sections'."
                )
            if not combined_class_subjects or combined_class_subjects.count() < 2:
                raise forms.ValidationError(
                    "Please select at least 2 joint class sections for a combined class."
                )
            if not combined_group_name:
                self.add_error(
                    "combined_group_name",
                    "Combined Group Label is required. Use a unique name per group "
                    "(e.g. 'Drawing-Standards', 'Drawing-Classes').",
                )
        else:
            if not class_subject:
                raise forms.ValidationError(
                    "Please select a Class Subject for single class mode."
                )
            if target_sections and class_subject:
                invalid = target_sections.exclude(class_instance=class_subject.class_instance)
                if invalid.exists():
                    raise forms.ValidationError(
                        f"Sections {list(invalid.values_list('name', flat=True))} "
                        f"do not belong to {class_subject.class_instance.name}."
                    )

        cleaned_data["combined_group_name"] = combined_group_name
        return cleaned_data