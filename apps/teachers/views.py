import traceback
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.contrib import messages

from apps.users.decorators import group_required
from .models import Teacher, TeacherSubjectAssignment
from .forms import TeacherForm, TeacherSubjectAssignmentForm
from apps.academic.models import ClassSubject, Section, PeriodDefinition
from apps.schools.models import School


# ==========================================
# Teacher CRUD Views
# ==========================================

class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = "teachers/teacher_list.html"
    context_object_name = "teachers"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            qs = Teacher.objects.filter(is_active=True)
            if school:
                qs = qs.filter(school=school)
            return qs.order_by("name")

        if school:
            return Teacher.objects.filter(school=school, is_active=True).order_by("name")
        return Teacher.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for teacher in context.get("teachers", []):
            teacher.total_periods = (
                TeacherSubjectAssignment.objects.filter(teacher=teacher).aggregate(
                    total=Sum("weekly_periods")
                )["total"]
                or 0
            )
        return context


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = "teachers/teacher_detail.html"
    context_object_name = "teacher"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Teacher.objects.all()
        if school:
            return Teacher.objects.filter(school=school)
        return Teacher.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherCreateView(SuccessMessageMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    success_url = reverse_lazy("teacher_list")
    next_url_name = "classsubject_create"
    success_message = "Teacher created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        return kwargs

    def form_valid(self, form):
        school = getattr(self.request, "school", None)
        if school:
            form.instance.school = school
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherUpdateView(SuccessMessageMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    success_url = reverse_lazy("teacher_list")
    success_message = "Teacher updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Teacher.objects.all()
        if school:
            return Teacher.objects.filter(school=school)
        return Teacher.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherDeleteView(DeleteView):
    model = Teacher
    template_name = "teachers/teacher_confirm_delete.html"
    success_url = reverse_lazy("teacher_list")

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Teacher.objects.all()
        if school:
            return Teacher.objects.filter(school=school)
        return Teacher.objects.none()


# ==========================================
# TeacherSubjectAssignment Views
# ==========================================

class TeacherAssignmentListView(LoginRequiredMixin, ListView):
    model = TeacherSubjectAssignment
    template_name = "teachers/teacherassignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "teacher",
                "class_subject__class_instance",
                "class_subject__subject",
            )
            .prefetch_related("target_sections")
        )

        if self.request.user.is_superuser:
            if school:
                queryset = queryset.filter(teacher__school=school)
        elif school:
            queryset = queryset.filter(teacher__school=school)
        else:
            return TeacherSubjectAssignment.objects.none()

        # 1. Filter by Teacher (if selected from dropdown)
        teacher_id = self.request.GET.get("teacher_id")
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        # 2. Apply Sorting
        sort = self.request.GET.get("sort")
        if sort == "teacher":
            queryset = queryset.order_by("teacher__name")
        elif sort == "subject":
            queryset = queryset.order_by("class_subject__subject__name")
        elif sort == "class":
            queryset = queryset.order_by(
                "class_subject__class_instance__display_order",
                "class_subject__class_instance__name",
            )
        else:
            # Default: teacher name, then subject
            queryset = queryset.order_by("teacher__name", "class_subject__subject__name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = context.get("assignments", [])
        school = getattr(self.request, "school", None)

        # Pass active teachers list & selected ID to template
        if self.request.user.is_superuser:
            teachers_qs = Teacher.objects.filter(is_active=True)
            if school:
                teachers_qs = teachers_qs.filter(school=school)
        elif school:
            teachers_qs = Teacher.objects.filter(school=school, is_active=True)
        else:
            teachers_qs = Teacher.objects.none()

        context["teachers"] = teachers_qs.order_by("name")
        context["selected_teacher_id"] = self.request.GET.get("teacher_id", "")

        # Annotate each assignment with teacher load info
        for assignment in assignments:
            teacher = assignment.teacher
            total = (
                TeacherSubjectAssignment.objects.filter(teacher=teacher).aggregate(
                    total=Sum("weekly_periods")
                )["total"]
                or 0
            )
            assignment.teacher_load = total
            assignment.teacher_max = teacher.max_weekly_load

        # Total required periods
        total_required = 0
        if self.request.user.is_superuser:
            cs_qs = ClassSubject.objects.filter(class_instance__is_active=True)
            if school:
                cs_qs = cs_qs.filter(class_instance__school=school)
        elif school:
            cs_qs = ClassSubject.objects.filter(class_instance__school=school, class_instance__is_active=True)
        else:
            cs_qs = ClassSubject.objects.none()

        for cs in cs_qs:
            sec_qs = Section.objects.filter(class_instance=cs.class_instance, is_active=True)
            if school:
                sec_qs = sec_qs.filter(class_instance__school=school)
            total_required += cs.weekly_periods * sec_qs.count()

        # Total assigned periods
        if self.request.user.is_superuser:
            assign_qs = TeacherSubjectAssignment.objects.all()
            if school:
                assign_qs = assign_qs.filter(teacher__school=school)
        elif school:
            assign_qs = TeacherSubjectAssignment.objects.filter(teacher__school=school)
        else:
            assign_qs = TeacherSubjectAssignment.objects.none()

        total_assigned = assign_qs.aggregate(total=Sum("weekly_periods"))["total"] or 0

        # Total teaching slots (excluding breaks, assembly, lunch)
        teaching_slots = 0
        total_slots = 0
        active_school = school or (School.objects.first() if self.request.user.is_superuser else None)

        if active_school:
            sections = Section.objects.filter(is_active=True, class_instance__school=active_school)
            for section in sections:
                periods = PeriodDefinition.objects.filter(
                    school=active_school, wing=section.wing
                )
                periods_per_day = periods.count()
                teaching_periods = periods.filter(
                    is_assembly=False, is_lunch=False, is_break=False
                )
                teaching_per_day = teaching_periods.count()
                if periods_per_day > 0:
                    working_days = section.working_days or list(range(0, 6))
                    total_slots += periods_per_day * len(working_days)
                    teaching_slots += teaching_per_day * len(working_days)

        context["total_required"] = total_required
        context["total_assigned"] = total_assigned
        context["total_remaining"] = total_required - total_assigned
        context["teaching_slots"] = teaching_slots
        context["total_slots"] = total_slots

        # Active teacher count
        active_teacher_count = teachers_qs.count()

        # Realistic averages
        average_per_teacher = 0
        required_avg_per_teacher = 0
        assigned_avg_per_teacher = 0

        if active_teacher_count > 0:
            average_per_teacher = round(teaching_slots / active_teacher_count, 1)
            required_avg_per_teacher = round(total_required / active_teacher_count, 1)
            assigned_avg_per_teacher = round(total_assigned / active_teacher_count, 1)

        context["active_teacher_count"] = active_teacher_count
        context["average_per_teacher"] = average_per_teacher
        context["required_avg_per_teacher"] = required_avg_per_teacher
        context["assigned_avg_per_teacher"] = assigned_avg_per_teacher

        return context


class TeacherAssignmentDetailView(LoginRequiredMixin, DetailView):
    model = TeacherSubjectAssignment
    template_name = "teachers/teacherassignment_detail.html"
    context_object_name = "assignment"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return TeacherSubjectAssignment.objects.all()
        if school:
            return TeacherSubjectAssignment.objects.filter(teacher__school=school)
        return TeacherSubjectAssignment.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherAssignmentCreateView(SuccessMessageMixin, CreateView):
    model = TeacherSubjectAssignment
    form_class = TeacherSubjectAssignmentForm
    template_name = "teachers/teacherassignment_form.html"
    success_url = reverse_lazy("teacherassignment_list")
    next_url_name = "timetable_dashboard"
    success_message = "Teacher assignment created successfully!"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        school = getattr(self.request, "school", None)
        if school and not self.request.user.is_superuser:
            form.fields["teacher"].queryset = Teacher.objects.filter(school=school, is_active=True)
            if "class_subject" in form.fields:
                form.fields["class_subject"].queryset = form.fields["class_subject"].queryset.filter(
                    class_instance__school=school
                )
            if "combined_class_subjects" in form.fields:
                form.fields["combined_class_subjects"].queryset = form.fields["combined_class_subjects"].queryset.filter(
                    class_instance__school=school
                )
            if "target_sections" in form.fields:
                form.fields["target_sections"].queryset = form.fields["target_sections"].queryset.filter(
                    class_instance__school=school
                )
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["preselected_sections"] = []
        return ctx

    def form_valid(self, form):
        is_combined = form.cleaned_data.get("is_combined")
        combined_class_subjects = form.cleaned_data.get("combined_class_subjects")

        # If Combined Class is enabled and joint sections are selected
        if is_combined and combined_class_subjects:
            teacher = form.cleaned_data["teacher"]
            weekly_periods = form.cleaned_data["weekly_periods"]
            is_primary = form.cleaned_data["is_primary"]
            preference_weight = form.cleaned_data["preference_weight"]
            group_name = form.cleaned_data.get("combined_group_name", "").strip()

            last_obj = None
            for cs in combined_class_subjects:
                created_item, _ = TeacherSubjectAssignment.objects.get_or_create(
                    teacher=teacher,
                    class_subject=cs,
                    defaults={
                        "weekly_periods": weekly_periods,
                        "is_primary": is_primary,
                        "preference_weight": preference_weight,
                        "is_combined": True,
                        "combined_group_name": group_name,
                    },
                )
                last_obj = created_item

            self.object = last_obj
            messages.success(
                self.request,
                f"Successfully created combined assignment across {combined_class_subjects.count()} sections!",
            )
            return redirect(self.get_success_url())

        # Standard single class assignment
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherAssignmentUpdateView(SuccessMessageMixin, UpdateView):
    model = TeacherSubjectAssignment
    form_class = TeacherSubjectAssignmentForm
    template_name = "teachers/teacherassignment_form.html"
    success_message = "Teacher assignment updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return TeacherSubjectAssignment.objects.all()
        if school:
            return TeacherSubjectAssignment.objects.filter(teacher__school=school)
        return TeacherSubjectAssignment.objects.none()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        school = getattr(self.request, "school", None)
        if school and not self.request.user.is_superuser:
            form.fields["teacher"].queryset = Teacher.objects.filter(school=school, is_active=True)
            if "class_subject" in form.fields:
                form.fields["class_subject"].queryset = form.fields["class_subject"].queryset.filter(
                    class_instance__school=school
                )
            if "combined_class_subjects" in form.fields:
                form.fields["combined_class_subjects"].queryset = form.fields["combined_class_subjects"].queryset.filter(
                    class_instance__school=school
                )
            if "target_sections" in form.fields:
                form.fields["target_sections"].queryset = form.fields["target_sections"].queryset.filter(
                    class_instance__school=school
                )
        return form

    def get_success_url(self):
        teacher_id = self.request.GET.get("teacher_id") or self.request.POST.get("teacher_id")
        if teacher_id:
            return f"{reverse_lazy('teacherassignment_list')}?teacher_id={teacher_id}"
        return reverse_lazy("teacherassignment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_teacher_id"] = self.request.GET.get("teacher_id", "")
        context["preselected_sections"] = (
            list(self.object.target_sections.values_list("pk", flat=True))
            if self.object and hasattr(self.object, "target_sections")
            else []
        )
        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherAssignmentDeleteView(DeleteView):
    model = TeacherSubjectAssignment
    template_name = "teachers/teacherassignment_confirm_delete.html"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return TeacherSubjectAssignment.objects.all()
        if school:
            return TeacherSubjectAssignment.objects.filter(teacher__school=school)
        return TeacherSubjectAssignment.objects.none()

    def get_success_url(self):
        teacher_id = (
            self.request.GET.get("teacher_id")
            or self.request.POST.get("teacher_id")
            or (self.object.teacher.id if self.object and self.object.teacher else None)
        )
        messages.success(self.request, "Assignment deleted successfully.")

        if teacher_id:
            return f"{reverse_lazy('teacherassignment_list')}?teacher_id={teacher_id}"
        return reverse_lazy("teacherassignment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_teacher_id"] = (
            self.request.GET.get("teacher_id")
            or (self.object.teacher.id if self.object and self.object.teacher else "")
        )
        return context


# ==========================================
# Teacher Load API
# ==========================================

@login_required
def teacher_load(request, teacher_id):
    try:
        school = getattr(request, "school", None)
        if request.user.is_superuser:
            qs = Teacher.objects.all()
        elif school:
            qs = Teacher.objects.filter(school=school)
        else:
            return JsonResponse({"error": "Unauthorized access"}, status=403)

        teacher = get_object_or_404(qs, id=teacher_id)
        load = teacher.total_assigned_periods()
        remaining = teacher.remaining_periods()
        return JsonResponse(
            {
                "load": load,
                "remaining": remaining,
                "max": teacher.max_weekly_load,
            }
        )
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)