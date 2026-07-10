from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import AcademicSession, Class, Section, Room, PeriodDefinition
from .forms import AcademicSessionForm, ClassForm, SectionForm, RoomForm, PeriodDefinitionForm

# -------- AcademicSession --------
class SessionListView(ListView):
    model = AcademicSession
    template_name = 'academic/session_list.html'
    context_object_name = 'sessions'

class SessionDetailView(DetailView):
    model = AcademicSession
    template_name = 'academic/session_detail.html'

class SessionCreateView(SuccessMessageMixin, CreateView):
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = 'academic/session_form.html'
    success_url = reverse_lazy('session_list')
    success_message = "Academic Session created successfully!"

class SessionUpdateView(SuccessMessageMixin, UpdateView):
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = 'academic/session_form.html'
    success_url = reverse_lazy('session_list')
    success_message = "Academic Session updated successfully!"

class SessionDeleteView(DeleteView):
    model = AcademicSession
    template_name = 'academic/session_confirm_delete.html'
    success_url = reverse_lazy('session_list')

# -------- Class --------
class ClassListView(ListView):
    model = Class
    template_name = 'academic/class_list.html'
    context_object_name = 'classes'

class ClassDetailView(DetailView):
    model = Class
    template_name = 'academic/class_detail.html'

class ClassCreateView(SuccessMessageMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = 'academic/class_form.html'
    success_url = reverse_lazy('class_list')
    success_message = "Class created successfully!"

class ClassUpdateView(SuccessMessageMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = 'academic/class_form.html'
    success_url = reverse_lazy('class_list')
    success_message = "Class updated successfully!"

class ClassDeleteView(DeleteView):
    model = Class
    template_name = 'academic/class_confirm_delete.html'
    success_url = reverse_lazy('class_list')

# -------- Section --------
class SectionListView(ListView):
    model = Section
    template_name = 'academic/section_list.html'
    context_object_name = 'sections'

class SectionDetailView(DetailView):
    model = Section
    template_name = 'academic/section_detail.html'

class SectionCreateView(SuccessMessageMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'academic/section_form.html'
    success_url = reverse_lazy('section_list')
    success_message = "Section created successfully!"

class SectionUpdateView(SuccessMessageMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'academic/section_form.html'
    success_url = reverse_lazy('section_list')
    success_message = "Section updated successfully!"

class SectionDeleteView(DeleteView):
    model = Section
    template_name = 'academic/section_confirm_delete.html'
    success_url = reverse_lazy('section_list')

# -------- Room --------
class RoomListView(ListView):
    model = Room
    template_name = 'academic/room_list.html'
    context_object_name = 'rooms'

class RoomDetailView(DetailView):
    model = Room
    template_name = 'academic/room_detail.html'

class RoomCreateView(SuccessMessageMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'academic/room_form.html'
    success_url = reverse_lazy('room_list')
    success_message = "Room created successfully!"

class RoomUpdateView(SuccessMessageMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'academic/room_form.html'
    success_url = reverse_lazy('room_list')
    success_message = "Room updated successfully!"

class RoomDeleteView(DeleteView):
    model = Room
    template_name = 'academic/room_confirm_delete.html'
    success_url = reverse_lazy('room_list')

# -------- PeriodDefinition --------
class PeriodListView(ListView):
    model = PeriodDefinition
    template_name = 'academic/period_list.html'
    context_object_name = 'periods'

class PeriodDetailView(DetailView):
    model = PeriodDefinition
    template_name = 'academic/period_detail.html'

class PeriodCreateView(SuccessMessageMixin, CreateView):
    model = PeriodDefinition
    form_class = PeriodDefinitionForm
    template_name = 'academic/period_form.html'
    success_url = reverse_lazy('period_list')
    success_message = "Period definition created successfully!"

class PeriodUpdateView(SuccessMessageMixin, UpdateView):
    model = PeriodDefinition
    form_class = PeriodDefinitionForm
    template_name = 'academic/period_form.html'
    success_url = reverse_lazy('period_list')
    success_message = "Period definition updated successfully!"

class PeriodDeleteView(DeleteView):
    model = PeriodDefinition
    template_name = 'academic/period_confirm_delete.html'
    success_url = reverse_lazy('period_list')
from .models import ClassSubject
from .forms import ClassSubjectForm

class ClassSubjectListView(ListView):
    model = ClassSubject
    template_name = 'academic/classsubject_list.html'
    context_object_name = 'classsubjects'

class ClassSubjectDetailView(DetailView):
    model = ClassSubject
    template_name = 'academic/classsubject_detail.html'

class ClassSubjectCreateView(SuccessMessageMixin, CreateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academic/classsubject_form.html'
    success_url = reverse_lazy('classsubject_list')
    success_message = "Class-Subject assignment created successfully!"

class ClassSubjectUpdateView(SuccessMessageMixin, UpdateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academic/classsubject_form.html'
    success_url = reverse_lazy('classsubject_list')
    success_message = "Class-Subject assignment updated successfully!"

class ClassSubjectDeleteView(DeleteView):
    model = ClassSubject
    template_name = 'academic/classsubject_confirm_delete.html'
    success_url = reverse_lazy('classsubject_list')
    
from .models import ClassSubject
from .forms import ClassSubjectForm

class ClassSubjectListView(ListView):
    model = ClassSubject
    template_name = 'academic/classsubject_list.html'
    context_object_name = 'classsubjects'

class ClassSubjectDetailView(DetailView):
    model = ClassSubject
    template_name = 'academic/classsubject_detail.html'

class ClassSubjectCreateView(SuccessMessageMixin, CreateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academic/classsubject_form.html'
    success_url = reverse_lazy('classsubject_list')
    success_message = "Class-Subject assignment created successfully!"

class ClassSubjectUpdateView(SuccessMessageMixin, UpdateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'academic/classsubject_form.html'
    success_url = reverse_lazy('classsubject_list')
    success_message = "Class-Subject assignment updated successfully!"

class ClassSubjectDeleteView(DeleteView):
    model = ClassSubject
    template_name = 'academic/classsubject_confirm_delete.html'
    success_url = reverse_lazy('classsubject_list')
    
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import PeriodDefinition, School
import json
from datetime import datetime, timedelta

@login_required
def bulk_create_periods(request):
    if request.method == 'POST':
        school_id = request.POST.get('school')
        wing = request.POST.get('wing')
        total_periods = int(request.POST.get('total_periods'))
        start_time_str = request.POST.get('start_time')
        default_duration = int(request.POST.get('default_duration'))
        period_data = json.loads(request.POST.get('period_data'))  # list of dicts

        school = School.objects.get(id=school_id)
        # Calculate start times
        start = datetime.strptime(start_time_str, '%H:%M')
        for i, data in enumerate(period_data, start=1):
            period_num = data.get('period_number', i)
            type_ = data.get('type', 'Normal')
            duration = data.get('duration') or default_duration
            special_activity = data.get('special_activity', '')
            day_of_week = data.get('day_of_week')  # None for all days, or 0-5

            # Calculate start and end times based on previous periods
            # We assume continuous schedule; but if previous periods have different durations, we need cumulative.
            # Simpler: we compute start time by adding durations of previous periods.
            # For this, we'll compute start time by iterating through periods and adding durations.
            # We'll store durations list.
            # But we can also compute start time from the base start_time and sum of durations of previous periods.
            # Let's do that.
            # We'll store all periods' durations in a list.
        # To avoid complexity, we can assume all periods are contiguous and use the default duration unless overridden.
        # For a production version, we would loop and accumulate durations.

        # I'll provide a simpler implementation: periods are contiguous with default duration except when overridden.
        # We'll create a list of (period_num, start, end, duration, ...)
        periods = []
        current_time = datetime.strptime(start_time_str, '%H:%M')
        for i, data in enumerate(period_data, start=1):
            dur = data.get('duration') or default_duration
            end_time = current_time + timedelta(minutes=dur)
            periods.append({
                'number': i,
                'start': current_time.time(),
                'end': end_time.time(),
                'duration': dur,
                'type': data.get('type', 'Normal'),
                'special_activity': data.get('special_activity', ''),
                'day_of_week': data.get('day_of_week'),  # None or 0-5
            })
            current_time = end_time

        # Create PeriodDefinition objects
        for p in periods:
            PeriodDefinition.objects.create(
                school=school,
                wing=wing,
                period_number=p['number'],
                start_time=p['start'],
                end_time=p['end'],
                duration_minutes=p['duration'],
                is_assembly=(p['type'] == 'Assembly'),
                is_lunch=(p['type'] == 'Lunch'),
                is_break=(p['type'] == 'Break'),
                break_duration=(p['duration'] if p['type'] in ['Break','Lunch'] else 0),
                special_activity=p['special_activity'] or None,
                day_of_week=p['day_of_week'],  # None for all days
            )

        messages.success(request, f"Created {len(periods)} periods for {wing} wing.")
        return redirect('period_list')

    schools = School.objects.all()
    return render(request, 'academic/bulk_period_form.html', {'schools': schools})