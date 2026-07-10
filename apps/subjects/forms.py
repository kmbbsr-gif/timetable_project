from django import forms
from .models import Subject

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = [
            'school', 'code', 'name', 'is_optional', 'requires_lab',
            'requires_practical', 'min_gap_periods', 'max_gap_periods',
            'default_double_period_allowed'
        ]
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            # ... other widgets ...
        }