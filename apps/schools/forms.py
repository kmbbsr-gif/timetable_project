from django import forms
from django.contrib.auth.models import User
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
        
class SchoolRegistrationForm(forms.ModelForm):
    admin_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name (e.g. Principal Mishra)"}),
        label="Administrator Name"
    )
    admin_email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "admin@school.com"}),
        label="Admin Login Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Secure Password"}),
        label="Password"
    )

    class Meta:
        model = School
        fields = ['name', 'school_code', 'udise_code', 'affiliation_no', 'email', 'contact_number']
        widgets = {
            'name': forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Public English Medium School"}),
            'school_code': forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. PEMS_BHUBANESWAR"}),
            'udise_code': forms.TextInput(attrs={"class": "form-control", "placeholder": "11-Digit UDISE Code (e.g. 21030100101)"}),
            'affiliation_no': forms.TextInput(attrs={"class": "form-control", "placeholder": "Board Affiliation No. (e.g. 1530001)"}),
            'email': forms.EmailInput(attrs={"class": "form-control", "placeholder": "school.official@school.com"}),
            'contact_number': forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
        }

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email