from django import forms
from .models import AcademicSession, Class, Section, Room, PeriodDefinition, ClassSubject, School
from datetime import datetime, date, timedelta
from .models import PeriodDefinition, WING_CHOICES

DAY_CHOICES = [
    (0, "Mon"), (1, "Tue"), (2, "Wed"),
    (3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun"),
]

WING_CHOICES = [
    ("Junior", "Junior"),
    ("Middle", "Middle"),
    ("Senior", "Senior"),
]



# apps/academic/forms.py

from .models import AcademicSession
from apps.schools.models import School

class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ['school', 'name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026-2027'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Style the school field
        if 'school' in self.fields:
            self.fields['school'].widget.attrs.update({'class': 'form-select'})

            # Non-superuser (School Admin): Lock down to their own school
            if self.user and not self.user.is_superuser:
                if self.school:
                    self.fields['school'].queryset = School.objects.filter(id=self.school.id)
                    self.fields['school'].initial = self.school
                    # Make it read-only/disabled visually and keep initial
                    self.fields['school'].empty_label = None
                else:
                    self.fields['school'].queryset = School.objects.none()
            
            # Superuser: pre-select active context school if available
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['school'].initial = self.school


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ["school", "name", "display_order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Class 10"}),
            "school": forms.Select(attrs={"class": "form-select"}),
            "display_order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if 'school' in self.fields:
            if self.user and not self.user.is_superuser:
                if self.school:
                    self.fields['school'].queryset = School.objects.filter(id=self.school.id)
                    self.fields['school'].initial = self.school
                    self.fields['school'].empty_label = None
                else:
                    self.fields['school'].queryset = School.objects.none()
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['school'].initial = self.school



from .models import Section


DAY_CHOICES = [
    ('0', 'Mon'),
    ('1', 'Tue'),
    ('2', 'Wed'),
    ('3', 'Thu'),
    ('4', 'Fri'),
    ('5', 'Sat'),
    ('6', 'Sun'),
]


class SectionForm(forms.ModelForm):
    working_days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Section
        fields = ['class_instance', 'name', 'wing', 'student_strength', 'working_days', 'is_active']
        widgets = {
            'class_instance': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A, B, C'}),
            'wing': forms.Select(attrs={'class': 'form-select'}),
            'student_strength': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 40', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Multi-tenant isolation for class selection
        if 'class_instance' in self.fields:
            if self.user and not self.user.is_superuser:
                if self.school:
                    self.fields['class_instance'].queryset = Class.objects.filter(school=self.school, is_active=True).order_by('display_order', 'name')
                else:
                    self.fields['class_instance'].queryset = Class.objects.none()
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['class_instance'].queryset = Class.objects.filter(school=self.school).order_by('display_order', 'name')
                else:
                    self.fields['class_instance'].queryset = Class.objects.all().order_by('school__name', 'display_order', 'name')

        # Pre-populate working days on edit
        if self.instance and self.instance.pk and self.instance.working_days is not None:
            val = self.instance.working_days
            if isinstance(val, (list, tuple)):
                self.initial['working_days'] = [str(d) for d in val]
            elif isinstance(val, (int, str)) and str(val).strip() != "":
                self.initial['working_days'] = [str(val)]
            else:
                self.initial['working_days'] = []

    def clean_working_days(self):
        data = self.cleaned_data.get('working_days', [])
        return [int(day) for day in data]


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["school", "name", "type", "capacity", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Room 101"}),
            "school": forms.Select(attrs={"class": "form-select"}),
            "type": forms.Select(
                choices=[
                    ('Classroom', 'Classroom'),
                    ('Lab', 'Lab'),
                    ('Hall', 'Hall'),
                    ('Auditorium', 'Auditorium'),
                    ('Library', 'Library'),
                    ('Staff Room', 'Staff Room'),
                    ('Playground/Ground', 'Playground/Ground'),
                    ('Other', 'Other'),
                ],
                attrs={"class": "form-select"}
            ),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if 'school' in self.fields:
            if self.user and not self.user.is_superuser:
                if self.school:
                    self.fields['school'].queryset = School.objects.filter(id=self.school.id)
                    self.fields['school'].initial = self.school
                    self.fields['school'].empty_label = None
                else:
                    self.fields['school'].queryset = School.objects.none()
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['school'].initial = self.school


from datetime import datetime, date

from .models import PeriodDefinition

from datetime import datetime, date, timedelta

from .models import PeriodDefinition

DAY_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]


class PeriodDefinitionForm(forms.ModelForm):
    wings = forms.MultipleChoiceField(
        choices=WING_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Wing(s)"
    )
    
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select specific days, or leave empty for all days.",
    )

    class Meta:
        model = PeriodDefinition
        fields = [
            "school", "wing", "period_number", "days",
            "start_time", "end_time", "duration_minutes",
            "is_assembly", "is_lunch", "is_break", "break_duration",
            "special_activity",
        ]
        widgets = {
            "school": forms.Select(attrs={"class": "form-select"}),
            "wing": forms.Select(attrs={"class": "form-select"}),
            "period_number": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control", "id": "id_start_time"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control", "id": "id_end_time"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 1, "id": "id_duration_minutes", "placeholder": "Auto-calculated"}),
            "break_duration": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "special_activity": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Assembly, Sports, MPT"}),
            "is_assembly": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_lunch": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_break": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if 'school' in self.fields:
            if self.user and not self.user.is_superuser:
                if self.school:
                    self.fields['school'].queryset = School.objects.filter(id=self.school.id)
                    self.fields['school'].initial = self.school
                    self.fields['school'].empty_label = None
                else:
                    self.fields['school'].queryset = School.objects.none()
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['school'].initial = self.school

        if "duration_minutes" in self.fields:
            self.fields["duration_minutes"].required = False

        if self.instance and self.instance.pk and getattr(self.instance, "days", None) is not None:
            raw_val = self.instance.days
            if isinstance(raw_val, (int, str)):
                days_list = [str(raw_val)]
            elif isinstance(raw_val, (list, tuple, set)):
                days_list = [str(d) for d in raw_val]
            else:
                days_list = []
            self.initial["days"] = days_list

    def clean_days(self):
        data = self.cleaned_data.get("days", [])
        return [int(d) for d in data]

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        duration = cleaned_data.get("duration_minutes")

        if start_time and end_time:
            dt_start = datetime.combine(date.today(), start_time)
            dt_end = datetime.combine(date.today(), end_time)

            if dt_end > dt_start:
                calculated_duration = int((dt_end - dt_start).total_seconds() / 60)
            else:
                calculated_duration = 0

            if not duration:
                duration = calculated_duration
                cleaned_data["duration_minutes"] = duration

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.start_time and instance.end_time:
            dt_start = datetime.combine(date.today(), instance.start_time)
            dt_end = datetime.combine(date.today(), instance.end_time)
            if dt_end > dt_start:
                instance.duration_minutes = int((dt_end - dt_start).total_seconds() / 60)

        if commit:
            instance.save()

            # Cascade Timing Update for subsequent periods in the same school and wing
            next_periods = PeriodDefinition.objects.filter(
                school=instance.school,
                wing=instance.wing,
                period_number__gt=instance.period_number
            ).order_by('period_number')

            current_end_time = instance.end_time

            for period in next_periods:
                period.start_time = current_end_time
                dur = period.duration_minutes if period.duration_minutes and period.duration_minutes > 0 else 45
                dt_curr_start = datetime.combine(date.today(), period.start_time)
                dt_curr_end = dt_curr_start + timedelta(minutes=dur)
                
                period.end_time = dt_curr_end.time()
                period.duration_minutes = dur
                period.save()
                current_end_time = period.end_time

        return instance



from .models import Subject, Class, ClassSubject, Section

def _section_map(school=None):
    """Group active sections by class ID, optionally scoped to a school."""
    sections = Section.objects.filter(is_active=True).select_related('class_instance')
    if school:
        sections = sections.filter(class_instance__school=school)
    sec_map = {}
    for s in sections:
        sec_map.setdefault(s.class_instance_id, []).append(s.name)
    return sec_map

# ============================================================
#  SUBJECT FORM
# ============================================================

# D:\timetable_project\apps\academic\forms.py

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = [
            "school", "name", "code", "color", 
            "min_gap_periods", "max_gap_periods"
        ]
        labels = {
            "name": "Subject Name",
            "code": "Subject Code / Abbreviation",
            "color": "Color Tag",
            "min_gap_periods": "Min Gap Between Periods",
            "max_gap_periods": "Max Gap Between Periods",
        }
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_subject_name",
                "placeholder": "e.g., Mathematics, English Language, Physics"
            }),
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "id": "id_subject_code",
                "placeholder": "e.g., MATH, ENG, PHY"
            }),
            "color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "value": "#4f46e5"
            }),
            "min_gap_periods": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "value": 0
            }),
            "max_gap_periods": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "value": 4
            }),
            "school": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set default values if fields exist
        if "color" in self.fields and not self.initial.get("color"):
            self.fields["color"].initial = "#4f46e5"
        if "min_gap_periods" in self.fields and self.initial.get("min_gap_periods") is None:
            self.fields["min_gap_periods"].initial = 0
        if "max_gap_periods" in self.fields and self.initial.get("max_gap_periods") is None:
            self.fields["max_gap_periods"].initial = 4

        if 'school' in self.fields:
            if self.user and not self.user.is_superuser:
                self.fields['school'].required = False
                if self.school:
                    self.fields['school'].queryset = School.objects.filter(id=self.school.id)
                    self.fields['school'].initial = self.school
                    self.fields['school'].empty_label = None
                else:
                    self.fields['school'].queryset = School.objects.none()
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['school'].initial = self.school

# ============================================================
#  CLASS-SUBJECT MAPPING & HELPER FUNCTION
# ============================================================




class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = [
            "class_instance", "subject", "weekly_periods",
            "double_period_allowed", "practical_required",
            "lab_required", "consecutive_allowed",
        ]
        widgets = {
            "class_instance": forms.Select(attrs={"class": "form-select", "id": "id_class_instance"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "weekly_periods": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "consecutive_allowed": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "double_period_allowed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "practical_required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "lab_required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        class_qs = Class.objects.filter(is_active=True)
        subject_qs = Subject.objects.all()

        if self.user and not self.user.is_superuser:
            if self.school:
                class_qs = class_qs.filter(school=self.school)
                subject_qs = subject_qs.filter(school=self.school)
            else:
                class_qs = Class.objects.none()
                subject_qs = Subject.objects.none()
        elif self.user and self.user.is_superuser and self.school:
            class_qs = class_qs.filter(school=self.school)
            subject_qs = subject_qs.filter(school=self.school)

        self.fields["subject"].queryset = subject_qs.order_by("name")

        # Class choices with safe ModelChoiceIteratorValue unpacking for Django 5.0+
        sec_map = _section_map(school=self.school)
        class_field = self.fields["class_instance"]
        class_field.queryset = class_qs.order_by("display_order", "name")

        original_choices = list(class_field.choices)
        custom_choices = []
        for pk, label in original_choices:
            raw_pk = getattr(pk, 'value', pk)
            if raw_pk and str(raw_pk).isdigit():
                sections = sec_map.get(int(raw_pk), [])
                if sections:
                    label = f"{label}   (Sections: {', '.join(sections)})"
            custom_choices.append((pk, label))

        class_field.choices = custom_choices

class BulkPeriodForm(forms.Form):
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label="School",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    wing = forms.ChoiceField(
        choices=WING_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    total_periods = forms.IntegerField(
        min_value=1,
        max_value=15,
        label="Number of periods per day",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        label="Start time of first period",
    )
    default_duration = forms.IntegerField(
        min_value=1,
        label="Default period duration (minutes)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    period_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if 'school' in self.fields:
            if self.user and not self.user.is_superuser:
                if self.school:
                    self.fields['school'].queryset = School.objects.filter(id=self.school.id)
                    self.fields['school'].initial = self.school
                    self.fields['school'].empty_label = None
                else:
                    self.fields['school'].queryset = School.objects.none()
            elif self.user and self.user.is_superuser:
                if self.school:
                    self.fields['school'].initial = self.school