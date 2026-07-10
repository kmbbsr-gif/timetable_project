from django import forms
from .models import Teacher, TeacherSubjectAssignment


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'school', 'name', 'employee_id', 'mobile', 'email',
            'designation', 'department',
            'max_daily_load', 'max_weekly_load',
            'is_class_teacher', 'class_teacher_for', 'is_co_class_teacher',
            'preferred_periods', 'preferred_days',
            'unavailable_days', 'unavailable_periods',
            'half_day', 'late_arrival', 'early_departure',
            'is_active'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'placeholder': 'Auto-generated if left blank'}),
            'mobile': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Optional'}),
            'preferred_periods': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., [1,2,3]'}),
            'preferred_days': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., [0,1,2] (0=Mon)'}),
            'unavailable_days': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., [3,4]'}),
            'unavailable_periods': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., [1,5]'}),
            'late_arrival': forms.TimeInput(attrs={'type': 'time'}),
            'early_departure': forms.TimeInput(attrs={'type': 'time'}),
            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make JSON fields optional
        self.fields['preferred_periods'].required = False
        self.fields['preferred_days'].required = False
        self.fields['unavailable_days'].required = False
        self.fields['unavailable_periods'].required = False
        
class TeacherSubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherSubjectAssignment
        fields = ['teacher', 'class_subject', 'weekly_periods', 'is_primary', 'preference_weight']