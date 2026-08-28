from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from apps.utils.tenancy import get_user_school
from apps.subjects.models import Subject
from apps.academic.forms import SubjectForm

# Use your actual import path for group_required:
# from apps.core.decorators import group_required


def get_subject_queryset(request):
    """
    STRICT tenant isolation. Non-superusers CANNOT bypass their school.
    """
    user = request.user

    if user.is_superuser:
        school = getattr(request, "school", None)
        if school:
            return Subject.objects.filter(school=school)
        return Subject.objects.all()

    # REGULAR USERS: resolve directly from profile. Ignore request.school.
    school = get_user_school(user)
    if school:
        return Subject.objects.filter(school=school)

    return Subject.objects.none()


@method_decorator(login_required, name="dispatch")
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
class SubjectDetailView(LoginRequiredMixin, DetailView):
    model = Subject
    template_name = "subjects/subject_detail.html"
    context_object_name = "subject"

    def get_queryset(self):
        return get_subject_queryset(self.request)


@method_decorator(login_required, name="dispatch")
class SubjectCreateView(SuccessMessageMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
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

        # Enforce tenant binding
        if not form.instance.school_id:
            if not user.is_superuser:
                user_school = get_user_school(user)
                if user_school:
                    form.instance.school = user_school

        # Defaults
        if not form.instance.color:
            form.instance.color = "#4f46e5"
        if form.instance.min_gap_periods is None:
            form.instance.min_gap_periods = 0
        if form.instance.max_gap_periods is None:
            form.instance.max_gap_periods = 4

        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class SubjectUpdateView(SuccessMessageMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
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
class SubjectDeleteView(SuccessMessageMixin, DeleteView):
    model = Subject
    template_name = "subjects/subject_confirm_delete.html"
    success_url = reverse_lazy("subject_list")
    success_message = "Subject deleted successfully."

    def get_queryset(self):
        return get_subject_queryset(self.request)