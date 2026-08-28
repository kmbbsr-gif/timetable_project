from django.db.models import Sum, Count, Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
import traceback
from django.http import HttpResponse

from apps.users.decorators import group_required
from apps.teachers.models import Teacher, TeacherSubjectAssignment
from apps.teachers.forms import TeacherForm, TeacherSubjectAssignmentForm
from apps.academic.models import ClassSubject, Section, PeriodDefinition
from apps.schools.models import School
from .models import ( AcademicSession, Class, Section, Subject, ClassSubject, PeriodDefinition, Room )
from .forms import SectionForm
from .forms import PeriodDefinitionForm, BulkPeriodForm
from .models import PeriodDefinition
from datetime import datetime, date, time, timedelta
from apps.utils.tenancy import get_user_school
from .forms import AcademicSessionForm
from .forms import (
    AcademicSessionForm,
    ClassForm,              # <-- ADD THIS LINE
    # ... any other forms you have imported ...
)
from .models import Room
from .forms import RoomForm
from .forms import SubjectForm, ClassSubjectForm

# ---------- Teacher CRUD Views ----------

class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = "teachers/teacher_list.html"
    context_object_name = "teachers"

    def get_queryset(self):
        return Teacher.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for teacher in context["teachers"]:
            teacher.total_periods = TeacherSubjectAssignment.objects.filter(
                teacher=teacher
            ).aggregate(total=Sum("weekly_periods"))["total"] or 0
        return context


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = "teachers/teacher_detail.html"


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherCreateView(SuccessMessageMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    success_url = reverse_lazy("teacher_list")
    success_message = "Teacher created successfully!"


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherUpdateView(SuccessMessageMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    success_url = reverse_lazy("teacher_list")
    success_message = "Teacher updated successfully!"


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherDeleteView(DeleteView):
    model = Teacher
    template_name = "teachers/teacher_confirm_delete.html"
    success_url = reverse_lazy("teacher_list")


# ---------- TeacherSubjectAssignment Views ----------

class TeacherAssignmentListView(LoginRequiredMixin, ListView):
    model = TeacherSubjectAssignment
    template_name = "teachers/teacherassignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("teacher", "class_subject__class_instance", "class_subject__subject")
            .prefetch_related("target_sections")
        )

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
        assignments = context["assignments"]

        # Pass active teachers list & selected ID to the template for the dropdown filter
        context["teachers"] = Teacher.objects.filter(is_active=True).order_by("name")
        context["selected_teacher_id"] = self.request.GET.get("teacher_id", "")

        # Annotate each assignment with teacher load info
        for assignment in assignments:
            teacher = assignment.teacher
            total = TeacherSubjectAssignment.objects.filter(teacher=teacher).aggregate(
                total=Sum("weekly_periods")
            )["total"]
            assignment.teacher_load = total if total else 0
            assignment.teacher_max = teacher.max_weekly_load

        # Total required periods (sum of weekly_periods per class-section)
        total_required = 0
        for cs in ClassSubject.objects.filter(class_instance__is_active=True):
            section_count = Section.objects.filter(
                class_instance=cs.class_instance, is_active=True
            ).count()
            total_required += cs.weekly_periods * section_count

        # Total assigned periods (sum of weekly_periods from TeacherSubjectAssignment)
        total_assigned = (
            TeacherSubjectAssignment.objects.aggregate(total=Sum("weekly_periods"))["total"]
            or 0
        )

        # Total teaching slots (excluding breaks, assembly, lunch)
        school = School.objects.first()
        teaching_slots = 0
        total_slots = 0
        if school:
            sections = Section.objects.filter(is_active=True)
            for section in sections:
                periods = PeriodDefinition.objects.filter(school=school, wing=section.wing)
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
        active_teacher_count = Teacher.objects.filter(is_active=True).count()

        # ---------- REALISTIC AVERAGES ----------
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


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class TeacherAssignmentCreateView(SuccessMessageMixin, CreateView):
    model = TeacherSubjectAssignment
    form_class = TeacherSubjectAssignmentForm
    template_name = "teachers/teacherassignment_form.html"
    success_url = reverse_lazy("teacherassignment_list")
    success_message = "Teacher assignment created successfully!"

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


# ---------- Teacher Load API (for real-time load display) ----------
def teacher_load(request, teacher_id):
    try:
        teacher = get_object_or_404(Teacher, id=teacher_id)
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
    
# ============================================================
#  ACADEMIC SESSION VIEWS
# ============================================================

class SessionListView(LoginRequiredMixin, ListView):
    model = AcademicSession
    template_name = "academic/session_list.html"
    context_object_name = "sessions"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            if school:
                return AcademicSession.objects.filter(school=school).order_by("-start_date")
            return AcademicSession.objects.all().order_by("-start_date")
        if school:
            return AcademicSession.objects.filter(school=school).order_by("-start_date")
        return AcademicSession.objects.none()


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = AcademicSession
    template_name = "academic/session_detail.html"


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SessionCreateView(SuccessMessageMixin, CreateView):
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = "academic/session_form.html"
    success_url = reverse_lazy("session_list")
    success_message = "Academic session created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        school = getattr(self.request, "school", None)
        if not self.request.user.is_superuser and school:
            form.instance.school = school
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SessionUpdateView(SuccessMessageMixin, UpdateView):
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = "academic/session_form.html"
    success_url = reverse_lazy("session_list")
    success_message = "Academic session updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return AcademicSession.objects.all()
        if school:
            return AcademicSession.objects.filter(school=school)
        return AcademicSession.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SessionDeleteView(SuccessMessageMixin, DeleteView):
    model = AcademicSession
    template_name = "academic/session_confirm_delete.html"
    success_url = reverse_lazy("session_list")
    success_message = "Academic session deleted successfully."

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return AcademicSession.objects.all()
        if school:
            return AcademicSession.objects.filter(school=school)
        return AcademicSession.objects.none()


# ============================================================
#  CLASS VIEWS
# ============================================================

class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = "academic/class_list.html"
    context_object_name = "classes"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            if school:
                return Class.objects.filter(school=school).order_by("display_order", "name")
            return Class.objects.all().order_by("display_order", "name")
        if school:
            return Class.objects.filter(school=school).order_by("display_order", "name")
        return Class.objects.none()


class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Class
    template_name = "academic/class_detail.html"
    context_object_name = "class"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Class.objects.all()
        if school:
            return Class.objects.filter(school=school)
        return Class.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class ClassCreateView(SuccessMessageMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = "academic/class_form.html"
    success_url = reverse_lazy("class_list")
    success_message = "Class created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        school = getattr(self.request, "school", None)
        if not self.request.user.is_superuser and school:
            form.instance.school = school
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class ClassUpdateView(SuccessMessageMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = "academic/class_form.html"
    success_url = reverse_lazy("class_list")
    success_message = "Class updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Class.objects.all()
        if school:
            return Class.objects.filter(school=school)
        return Class.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class ClassDeleteView(SuccessMessageMixin, DeleteView):
    model = Class
    template_name = "academic/class_confirm_delete.html"
    success_url = reverse_lazy("class_list")
    success_message = "Class deleted successfully."

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Class.objects.all()
        if school:
            return Class.objects.filter(school=school)
        return Class.objects.none()

# ============================================================
#  SECTION VIEWS
# ============================================================

class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = "academic/section_list.html"
    context_object_name = "sections"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            if school:
                return Section.objects.filter(class_instance__school=school).select_related("class_instance", "class_instance__school").order_by("class_instance__display_order", "name")
            return Section.objects.all().select_related("class_instance", "class_instance__school").order_by("class_instance__school__name", "class_instance__display_order", "name")
        if school:
            return Section.objects.filter(class_instance__school=school).select_related("class_instance", "class_instance__school").order_by("class_instance__display_order", "name")
        return Section.objects.none()


class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = "academic/section_detail.html"
    context_object_name = "section"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Section.objects.all().select_related("class_instance")
        if school:
            return Section.objects.filter(class_instance__school=school).select_related("class_instance")
        return Section.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SectionCreateView(SuccessMessageMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = "academic/section_form.html"
    success_url = reverse_lazy("section_list")
    success_message = "Section created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SectionUpdateView(SuccessMessageMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = "academic/section_form.html"
    success_url = reverse_lazy("section_list")
    success_message = "Section updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Section.objects.all().select_related("class_instance")
        if school:
            return Section.objects.filter(class_instance__school=school).select_related("class_instance")
        return Section.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SectionDeleteView(SuccessMessageMixin, DeleteView):
    model = Section
    template_name = "academic/section_confirm_delete.html"
    success_url = reverse_lazy("section_list")
    success_message = "Section deleted successfully."

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Section.objects.all()
        if school:
            return Section.objects.filter(class_instance__school=school)
        return Section.objects.none()


# ============================================================
#  SUBJECT CRUD VIEWS (TENANT-AWARE)
# ============================================================


from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from apps.utils.tenancy import get_user_school
from apps.subjects.models import Subject
from apps.academic.forms import SubjectForm

# KEEP YOUR ORIGINAL WORKING IMPORT — edit this line to match your project:



def get_subject_queryset(request):
    """
    STRICT tenant isolation. Non-superusers CANNOT bypass their school.
    """
    user = request.user
    print(f"[DEBUG] User: {user.username} | is_superuser: {user.is_superuser}")

    if user.is_superuser:
        school = getattr(request, "school", None)
        print(f"[DEBUG] Superuser branch | request.school: {school}")
        if school:
            return Subject.objects.filter(school=school)
        return Subject.objects.all()

    # REGULAR USERS: completely ignore request.school
    school = get_user_school(user)
    print(f"[DEBUG] Regular user branch | get_user_school(): {school}")
    if school:
        return Subject.objects.filter(school=school)

    return Subject.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator", "Teacher"), name="dispatch")
class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = "subjects/subject_list.html"
    context_object_name = "subjects"
    paginate_by = 25

    def get_queryset(self):
        return get_subject_queryset(self.request).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_superuser:
            context["current_school"] = getattr(self.request, "school", None)
        else:
            context["current_school"] = get_user_school(user)

        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator", "Teacher"), name="dispatch")
class SubjectDetailView(LoginRequiredMixin, DetailView):
    model = Subject
    template_name = "academic/subject_detail.html"
    context_object_name = "subject"

    def get_queryset(self):
        return get_subject_queryset(self.request)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SubjectCreateView(SuccessMessageMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "academic/subject_form.html"
    success_url = reverse_lazy("subject_list")
    success_message = "Subject created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        if self.request.user.is_superuser:
            kwargs["school"] = getattr(self.request, "school", None)
        else:
            kwargs["school"] = get_user_school(self.request.user)

        return kwargs

    def form_valid(self, form):
        user = self.request.user

        if not form.instance.school_id:
            if not user.is_superuser:
                user_school = get_user_school(user)
                if user_school:
                    form.instance.school = user_school

        if not form.instance.color:
            form.instance.color = "#4f46e5"
        if form.instance.min_gap_periods is None:
            form.instance.min_gap_periods = 0
        if form.instance.max_gap_periods is None:
            form.instance.max_gap_periods = 4

        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SubjectUpdateView(SuccessMessageMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = "academic/subject_form.html"
    success_url = reverse_lazy("subject_list")
    success_message = "Subject updated successfully!"

    def get_queryset(self):
        return get_subject_queryset(self.request)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        if self.request.user.is_superuser:
            kwargs["school"] = getattr(self.request, "school", None)
        else:
            kwargs["school"] = get_user_school(self.request.user)

        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class SubjectDeleteView(SuccessMessageMixin, DeleteView):
    model = Subject
    template_name = "academic/subject_confirm_delete.html"
    success_url = reverse_lazy("subject_list")
    success_message = "Subject deleted successfully."

    def get_queryset(self):
        return get_subject_queryset(self.request)
# ============================================================
#  CLASS-SUBJECT VIEWS
# ============================================================

class ClassSubjectListView(LoginRequiredMixin, ListView):
    model = ClassSubject
    template_name = "academic/classsubject_list.html"
    context_object_name = "classsubjects"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            if school:
                return ClassSubject.objects.filter(class_instance__school=school).select_related(
                    "class_instance", "subject", "class_instance__school"
                ).order_by("class_instance__display_order", "subject__name")
            return ClassSubject.objects.all().select_related(
                "class_instance", "subject", "class_instance__school"
            ).order_by("class_instance__school__name", "class_instance__display_order", "subject__name")
        if school:
            return ClassSubject.objects.filter(class_instance__school=school).select_related(
                "class_instance", "subject", "class_instance__school"
            ).order_by("class_instance__display_order", "subject__name")
        return ClassSubject.objects.none()


class ClassSubjectDetailView(LoginRequiredMixin, DetailView):
    model = ClassSubject
    template_name = "academic/classsubject_detail.html"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return ClassSubject.objects.all()
        if school:
            return ClassSubject.objects.filter(class_instance__school=school)
        return ClassSubject.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class ClassSubjectCreateView(SuccessMessageMixin, CreateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = "academic/classsubject_form.html"
    success_url = reverse_lazy("classsubject_list")
    success_message = "Class subject mapping created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class ClassSubjectUpdateView(SuccessMessageMixin, UpdateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = "academic/classsubject_form.html"
    success_url = reverse_lazy("classsubject_list")
    success_message = "Class subject mapping updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return ClassSubject.objects.all()
        if school:
            return ClassSubject.objects.filter(class_instance__school=school)
        return ClassSubject.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class ClassSubjectDeleteView(SuccessMessageMixin, DeleteView):
    model = ClassSubject
    template_name = "academic/classsubject_confirm_delete.html"
    success_url = reverse_lazy("classsubject_list")
    success_message = "Class subject mapping removed successfully."

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return ClassSubject.objects.all()
        if school:
            return ClassSubject.objects.filter(class_instance__school=school)
        return ClassSubject.objects.none()

# ============================================================
#  PERIOD DEFINITION VIEWS
# ============================================================

class PeriodListView(LoginRequiredMixin, ListView):
    model = PeriodDefinition
    template_name = "academic/period_list.html"
    context_object_name = "periods"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            if school:
                return PeriodDefinition.objects.filter(school=school).order_by("wing", "period_number")
            return PeriodDefinition.objects.all().order_by("school", "wing", "period_number")
        if school:
            return PeriodDefinition.objects.filter(school=school).order_by("wing", "period_number")
        return PeriodDefinition.objects.none()


class PeriodDetailView(LoginRequiredMixin, DetailView):
    model = PeriodDefinition
    template_name = "academic/period_detail.html"
    context_object_name = "period"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return PeriodDefinition.objects.all()
        if school:
            return PeriodDefinition.objects.filter(school=school)
        return PeriodDefinition.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class PeriodCreateView(SuccessMessageMixin, CreateView):
    model = PeriodDefinition
    form_class = PeriodDefinitionForm
    template_name = "academic/period_form.html"
    success_url = reverse_lazy("period_list")
    success_message = "Period created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        school = getattr(self.request, "school", None)
        
        # Scope auto-increment and defaults to the active school
        period_qs = PeriodDefinition.objects.all()
        if school:
            period_qs = period_qs.filter(school=school)
            initial['school'] = school

        last_period = period_qs.order_by('-period_number').first()
        
        if last_period:
            initial['period_number'] = last_period.period_number + 1
            if last_period.end_time:
                initial['start_time'] = last_period.end_time.strftime('%H:%M')
            initial['wing'] = last_period.wing
        else:
            initial['period_number'] = 1

        return initial

    def form_valid(self, form):
        school = getattr(self.request, "school", None)
        if not self.request.user.is_superuser and school:
            form.instance.school = school
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class PeriodUpdateView(SuccessMessageMixin, UpdateView):
    model = PeriodDefinition
    form_class = PeriodDefinitionForm
    template_name = "academic/period_form.html"
    success_url = reverse_lazy("period_list")
    success_message = "Period updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return PeriodDefinition.objects.all()
        if school:
            return PeriodDefinition.objects.filter(school=school)
        return PeriodDefinition.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class PeriodDeleteView(SuccessMessageMixin, DeleteView):
    model = PeriodDefinition
    template_name = "academic/period_confirm_delete.html"
    success_url = reverse_lazy("period_list")
    success_message = "Period deleted successfully."

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return PeriodDefinition.objects.all()
        if school:
            return PeriodDefinition.objects.filter(school=school)
        return PeriodDefinition.objects.none()

# ============================================================
#  ROOM VIEWS
# ============================================================

class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = "academic/room_list.html"
    context_object_name = "rooms"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            if school:
                return Room.objects.filter(school=school).order_by("name")
            return Room.objects.all().order_by("name")
        if school:
            return Room.objects.filter(school=school).order_by("name")
        return Room.objects.none()


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = "academic/room_detail.html"
    context_object_name = "room"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Room.objects.all()
        if school:
            return Room.objects.filter(school=school)
        return Room.objects.none()


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class RoomCreateView(SuccessMessageMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = "academic/room_form.html"
    success_url = reverse_lazy("room_list")
    success_message = "Room created successfully!"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        school = getattr(self.request, "school", None)
        if not self.request.user.is_superuser and school:
            form.instance.school = school
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class RoomUpdateView(SuccessMessageMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "academic/room_form.html"
    success_url = reverse_lazy("room_list")
    success_message = "Room updated successfully!"

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Room.objects.all()
        if school:
            return Room.objects.filter(school=school)
        return Room.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["school"] = getattr(self.request, "school", None)
        kwargs["user"] = self.request.user
        return kwargs


@method_decorator(login_required, name="dispatch")
@method_decorator(group_required("Admin", "Coordinator"), name="dispatch")
class RoomDeleteView(SuccessMessageMixin, DeleteView):
    model = Room
    template_name = "academic/room_confirm_delete.html"
    success_url = reverse_lazy("room_list")
    success_message = "Room deleted successfully."

    def get_queryset(self):
        school = getattr(self.request, "school", None)
        if self.request.user.is_superuser:
            return Room.objects.all()
        if school:
            return Room.objects.filter(school=school)
        return Room.objects.none()
    
# ============================================================
#  BULK PERIOD CREATION
# ============================================================

import json
from apps.users.decorators import group_required  # Adjust import paths if needed

from apps.schools.models import School
from .models import PeriodDefinition
from django.db import transaction


@login_required
@group_required("Admin", "Coordinator")
def bulk_create_periods(request):
    """Create multiple period definitions at once for a school."""
    user_school = getattr(request, "school", None)
    if not user_school and request.user.is_superuser:
        schools = School.objects.all().order_by("name")
    elif user_school:
        schools = School.objects.filter(id=user_school.id)
    else:
        schools = School.objects.none()

    if request.method == "POST":
        if request.user.is_superuser:
            school_id = request.POST.get("school")
            school = get_object_or_404(School, id=school_id) if school_id else user_school
        else:
            school = user_school

        wing = request.POST.get("wing", "Junior")
        start_time_str = request.POST.get("start_time")
        period_data_raw = request.POST.get("period_data")

        if not (school and wing):
            messages.error(request, "Please select both School and Wing.")
            return redirect("bulk_create_periods")

        # -------------------------------------------------------------
        # OPTION 1: Process JSON payload generated from dynamic JS table
        # -------------------------------------------------------------
        if period_data_raw and start_time_str:
            try:
                period_data = json.loads(period_data_raw)
                current_dt = datetime.strptime(start_time_str, "%H:%M")
                created = 0

                with transaction.atomic():
                    for item in period_data:
                        p_num = item.get("period_number")
                        p_type = item.get("type", "Normal")
                        duration = int(item.get("duration", 35))
                        activity = item.get("special_activity", "").strip()
                        day_val = item.get("day_of_week")

                        start_time_val = current_dt.time()
                        end_dt = current_dt + timedelta(minutes=duration)
                        end_time_val = end_dt.time()

                        days_list = [day_val] if day_val is not None else list(range(0, 6))

                        PeriodDefinition.objects.update_or_create(
                            school=school,
                            wing=wing,
                            period_number=p_num,
                            defaults={
                                "start_time": start_time_val,
                                "end_time": end_time_val,
                                "duration_minutes": duration,
                                "days": days_list,
                                "special_activity": activity,
                                "is_assembly": (p_type == "Assembly"),
                                "is_lunch": (p_type == "Lunch"),
                                "is_break": (p_type == "Break"),
                            }
                        )
                        created += 1
                        current_dt = end_dt

                messages.success(request, f"{created} periods successfully configured for {school.name} ({wing}).")
                return redirect("period_list")

            except Exception as e:
                messages.error(request, f"Error processing bulk creation: {str(e)}")
                return redirect("bulk_create_periods")

        # -------------------------------------------------------------
        # OPTION 2: Fallback simple loop
        # -------------------------------------------------------------
        else:
            try:
                count = int(request.POST.get("total_periods", request.POST.get("count", 8)))
                default_dur = int(request.POST.get("default_duration", request.POST.get("duration", 35)))

                if start_time_str:
                    current_dt = datetime.strptime(start_time_str, "%H:%M")
                else:
                    start_hour = int(request.POST.get("start_hour", 8))
                    start_min = int(request.POST.get("start_min", 0))
                    current_dt = datetime.combine(datetime.today(), time(start_hour, start_min))

                created = 0
                with transaction.atomic():
                    for i in range(1, count + 1):
                        start_val = current_dt.time()
                        end_dt = current_dt + timedelta(minutes=default_dur)
                        end_val = end_dt.time()

                        PeriodDefinition.objects.update_or_create(
                            school=school,
                            wing=wing,
                            period_number=i,
                            defaults={
                                "start_time": start_val,
                                "end_time": end_val,
                                "duration_minutes": default_dur,
                                "days": list(range(0, 6)),
                                "is_assembly": False,
                                "is_lunch": False,
                                "is_break": False,
                            }
                        )
                        created += 1
                        current_dt = end_dt

                messages.success(request, f"{created} periods created for {school.name} ({wing}).")
                return redirect("period_list")

            except Exception as e:
                messages.error(request, f"Error creating default periods: {str(e)}")
                return redirect("bulk_create_periods")

    return render(
        request, 
        "academic/bulk_period_form.html", 
        {
            "schools": schools,
            "current_school": user_school,
        }
    )

@login_required
def some_view(request):
    school = get_user_school(request.user)
    
    # Filter querysets strictly by this school
    if school:
        classes = Class.objects.filter(school=school, is_active=True).order_by('display_order')
    else:
        classes = Class.objects.filter(is_active=True).order_by('display_order')