from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from .models import Teacher
from .forms import TeacherForm
from .models import TeacherSubjectAssignment
from .forms import TeacherSubjectAssignmentForm
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from django.db.models import Sum, Count, F, Q
from .models import TeacherSubjectAssignment
from apps.academic.models import ClassSubject, Section

class TeacherListView(ListView):
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'
    queryset = Teacher.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Annotate each teacher with total weekly periods
        for teacher in context['teachers']:
            teacher.total_periods = TeacherSubjectAssignment.objects.filter(
                teacher=teacher
            ).aggregate(total=Sum('weekly_periods'))['total'] or 0
        return context

class TeacherDetailView(DetailView):
    model = Teacher
    template_name = 'teachers/teacher_detail.html'

class TeacherCreateView(SuccessMessageMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teacher_list')
    success_message = "Teacher created successfully!"
    
    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))

class TeacherUpdateView(SuccessMessageMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teacher_list')
    success_message = "Teacher updated successfully!"

class TeacherDeleteView(DeleteView):
    model = Teacher
    template_name = 'teachers/teacher_confirm_delete.html'
    success_url = reverse_lazy('teacher_list')


from django.db.models import Sum
from django.views.generic import ListView
from .models import Teacher, TeacherSubjectAssignment
from apps.academic.models import ClassSubject, Section, PeriodDefinition
from apps.schools.models import School

class TeacherAssignmentListView(ListView):
    model = TeacherSubjectAssignment
    template_name = 'teachers/teacherassignment_list.html'
    context_object_name = 'assignments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = context['assignments']

        # Annotate each assignment with teacher load info
        for assignment in assignments:
            teacher = assignment.teacher
            total = TeacherSubjectAssignment.objects.filter(
                teacher=teacher
            ).aggregate(total=Sum('weekly_periods'))['total']
            assignment.teacher_load = total if total else 0
            assignment.teacher_max = teacher.max_weekly_load

        # Total required periods (sum of weekly_periods per class-section)
        total_required = 0
        for cs in ClassSubject.objects.filter(class_instance__is_active=True):
            section_count = Section.objects.filter(class_instance=cs.class_instance, is_active=True).count()
            total_required += cs.weekly_periods * section_count

        # Total assigned periods (sum of weekly_periods from TeacherSubjectAssignment)
        total_assigned = TeacherSubjectAssignment.objects.aggregate(total=Sum('weekly_periods'))['total'] or 0

        # Total teaching slots (excluding breaks, assembly, lunch)
        school = School.objects.first()
        teaching_slots = 0
        total_slots = 0   # keep for reference (including breaks)
        if school:
            sections = Section.objects.filter(is_active=True)
            for section in sections:
                # Periods for this wing
                periods = PeriodDefinition.objects.filter(school=school, wing=section.wing)
                periods_per_day = periods.count()
                # Teaching periods only
                teaching_periods = periods.filter(is_assembly=False, is_lunch=False, is_break=False)
                teaching_per_day = teaching_periods.count()
                if periods_per_day > 0:
                    working_days = section.working_days or list(range(0, 6))  # default Mon-Sat
                    total_slots += periods_per_day * len(working_days)
                    teaching_slots += teaching_per_day * len(working_days)

        context['total_required'] = total_required
        context['total_assigned'] = total_assigned
        context['total_remaining'] = total_required - total_assigned
        context['teaching_slots'] = teaching_slots      # new metric
        context['total_slots'] = total_slots            # optional (if you want to show both)
        
        # Average periods per teacher
        active_teacher_count = Teacher.objects.filter(is_active=True).count()
        average_per_teacher = 0
        if active_teacher_count > 0:
            average_per_teacher = round(teaching_slots / active_teacher_count, 1)

        context['average_per_teacher'] = average_per_teacher
        context['active_teacher_count'] = active_teacher_count

        return context

class TeacherAssignmentDetailView(DetailView):
    model = TeacherSubjectAssignment
    template_name = 'teachers/teacherassignment_detail.html'

class TeacherAssignmentCreateView(SuccessMessageMixin, CreateView):
    model = TeacherSubjectAssignment
    form_class = TeacherSubjectAssignmentForm
    template_name = 'teachers/teacherassignment_form.html'
    success_url = reverse_lazy('teacherassignment_list')
    success_message = "Teacher assignment created successfully!"

class TeacherAssignmentUpdateView(SuccessMessageMixin, UpdateView):
    model = TeacherSubjectAssignment
    form_class = TeacherSubjectAssignmentForm
    template_name = 'teachers/teacherassignment_form.html'
    success_url = reverse_lazy('teacherassignment_list')
    success_message = "Teacher assignment updated successfully!"

class TeacherAssignmentDeleteView(DeleteView):
    model = TeacherSubjectAssignment
    template_name = 'teachers/teacherassignment_confirm_delete.html'
    success_url = reverse_lazy('teacherassignment_list')    
    
# ... existing imports and views ...

def teacher_load(request, teacher_id):
    import traceback
    try:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        load = teacher.total_assigned_periods()
        remaining = teacher.remaining_periods()
        return JsonResponse({
            'load': load,
            'remaining': remaining,
            'max': teacher.max_weekly_load,
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)   