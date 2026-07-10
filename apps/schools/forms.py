from django import forms
from .models import School

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            'name', 'logo', 'board', 'affiliation_no', 'udise_code', 'school_code',
            'address', 'city', 'district', 'state', 'pin_code',
            'principal_name', 'vice_principal_name', 'academic_coordinator', 'exam_incharge',
            'session_start', 'session_end',
            'opening_time', 'closing_time',
            'contact_number', 'email', 'website'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'session_start': forms.DateInput(attrs={'type': 'date'}),
            'session_end': forms.DateInput(attrs={'type': 'date'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time'}),
        }