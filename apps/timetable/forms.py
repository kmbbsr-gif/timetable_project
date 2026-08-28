from django import forms
from apps.academic.models import Class, Section
from apps.academic.forms import DAY_CHOICES
from apps.schools.models import School


class FixedEntryForm(forms.Form):
    apply_to_all = forms.BooleanField(
        required=False,
        label="Apply to all classes & sections",
        help_text="If checked, this fixed entry will be created for every active class and section in your school."
    )
    class_instance = forms.ModelChoiceField(
        queryset=Class.objects.none(),
        required=False,
        label="Class"
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        required=False,
        label="Section"
    )

    day = forms.ChoiceField(choices=DAY_CHOICES, label="Day")
    period = forms.IntegerField(min_value=1, max_value=15, label="Period Number")
    activity_name = forms.CharField(
        max_length=100,
        label="Activity Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g., MPT, Yoga, Library, Games, Assembly"})
    )

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        class_qs = Class.objects.filter(is_active=True)
        sec_qs = Section.objects.filter(is_active=True)

        if self.user and not self.user.is_superuser:
            if self.school:
                class_qs = class_qs.filter(school=self.school)
                sec_qs = sec_qs.filter(class_instance__school=self.school)
            else:
                class_qs = Class.objects.none()
                sec_qs = Section.objects.none()
        elif self.user and self.user.is_superuser and self.school:
            class_qs = class_qs.filter(school=self.school)
            sec_qs = sec_qs.filter(class_instance__school=self.school)

        self.fields['class_instance'].queryset = class_qs.order_by('display_order', 'name')
        self.fields['section'].queryset = sec_qs.select_related('class_instance').order_by('class_instance__display_order', 'name')

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        apply_all = cleaned_data.get('apply_to_all')
        cls = cleaned_data.get('class_instance')
        sec = cleaned_data.get('section')

        if not apply_all and not cls:
            raise forms.ValidationError("Please select a class or check 'Apply to all'.")
        if not apply_all and cls and not sec:
            raise forms.ValidationError("Please select a section for the chosen class.")
        if apply_all and (cls or sec):
            raise forms.ValidationError("When 'Apply to all' is checked, do not select a specific class or section.")
        return cleaned_data


class FixedEntryEditForm(forms.Form):
    day = forms.ChoiceField(choices=DAY_CHOICES, label="Day")
    period = forms.IntegerField(min_value=1, max_value=15, label="Period Number")
    activity_name = forms.CharField(max_length=100, label="Activity Name (e.g., MPT, Yoga)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'