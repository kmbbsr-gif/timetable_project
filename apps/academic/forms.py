from django import forms
from .models import AcademicSession, Class, Section, Room, PeriodDefinition

class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ['school', 'name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['school', 'name', 'display_order', 'is_active']

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['class_instance', 'name', 'student_strength', 'working_days', 'wing', 'is_active']

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['school', 'name', 'type', 'capacity', 'is_active']

class PeriodDefinitionForm(forms.ModelForm):
    class Meta:
        model = PeriodDefinition
        fields = [
            'school', 'wing', 'period_number', 'day_of_week', 'special_activity',
            'start_time', 'end_time', 'duration_minutes',
            'is_assembly', 'is_lunch', 'is_break', 'break_duration'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'day_of_week': forms.Select(choices=[('', 'All days')] + PeriodDefinition.DAY_CHOICES),
        }
        
from .models import ClassSubject

class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = [
            'class_instance', 'subject', 'weekly_periods',
            'double_period_allowed', 'practical_required',
            'lab_required', 'consecutive_allowed'
        ]
        
# inside apps/academic/forms.py

from .models import ClassSubject

class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = [
            'class_instance', 'subject', 'weekly_periods',
            'double_period_allowed', 'practical_required',
            'lab_required', 'consecutive_allowed'
        ]
        
from django import forms
from .models import School

class BulkPeriodForm(forms.Form):
    school = forms.ModelChoiceField(queryset=School.objects.all(), label="School")
    wing = forms.ChoiceField(choices=[('Junior','Junior'),('Middle','Middle'),('Senior','Senior')])
    total_periods = forms.IntegerField(min_value=1, max_value=15, label="Number of periods per day")
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type':'time'}), label="Start time of first period")
    default_duration = forms.IntegerField(min_value=1, label="Default period duration (minutes)")

    # We'll use a JSON field to pass period-specific data; but we can also generate fields dynamically.
    # For simplicity, we'll use a TextArea that accepts a JSON array, but we'll provide an interactive table via JS.
    # I'll implement a method to create dynamic fields in the view.