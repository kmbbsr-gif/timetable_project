from django import forms
from .models import Subject

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['school', 'code', 'name', 'color', 'is_optional', 'requires_lab',
                  'requires_practical', 'min_gap_periods', 'max_gap_periods',
                  'default_double_period_allowed']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['rows'] = 4
            else:
                field.widget.attrs['class'] = 'form-control'
            
            # Add placeholder if field has help_text
            if field.help_text:
                field.widget.attrs['placeholder'] = field.help_text
            
            # Add rounded corners
            field.widget.attrs['class'] += ' rounded-3'