from datetime import date, time, timedelta, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db import transaction

from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from .models import School
from .serializers import SchoolSerializer
from .forms import SchoolForm, SchoolRegistrationForm

from apps.teachers.models import Teacher
from apps.teachers.utils import get_average_load
from apps.subjects.models import Subject
from apps.academic.models import Class, PeriodDefinition
from apps.users.models import UserProfile
from apps.users.decorators import group_required


# ---------------------- API ViewSet ----------------------
class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = []  # Adjust as needed


# ---------------------- Unified Dashboard ----------------------
@login_required
def dashboard(request):
    """
    Main dashboard view accessible to all authenticated users.
    Tenancy filters ensure users only see their own school's data.
    """
    # 1. Check request.school, fallback to request.user.profile.school
    school = getattr(request, 'school', None)
    if not school and hasattr(request.user, 'profile'):
        school = request.user.profile.school

    if school:
        school_count = 1
        teacher_count = Teacher.objects.filter(school=school, is_active=True).count()
        subject_count = Subject.objects.filter(school=school).count()
        class_count = Class.objects.filter(school=school).count()
    elif request.user.is_superuser:
        # Fallback only for master superuser
        school_count = School.objects.count()
        teacher_count = Teacher.objects.count()
        subject_count = Subject.objects.count()
        class_count = Class.objects.count()
    else:
        school_count = 0
        teacher_count = 0
        subject_count = 0
        class_count = 0

    context = {
        'school': school,
        'school_count': school_count,
        'teacher_count': teacher_count,
        'subject_count': subject_count,
        'class_count': class_count,
    }
    return render(request, 'dashboard.html', context)


# ---------------------- School CRUD Views ----------------------
@login_required
def school_list(request):
    """
    STRICT LOCK:
    - Superusers can see all schools.
    - School Admins are only shown THEIR OWN school (or redirected to their own edit page).
    """
    if request.user.is_superuser:
        schools = School.objects.all().order_by('name')
        return render(request, 'schools/school_list.html', {'schools': schools})
    
    school = getattr(request, 'school', None)
    if not school:
        messages.error(request, "No school associated with this account.")
        return redirect('dashboard')
        
        # Redirect school admin directly to their school detail page
    return redirect('school_detail', pk=school.id)


@login_required
def school_detail(request, pk):
    """Prevent School B from viewing School A's details by tampering with the URL ID"""
    if not request.user.is_superuser:
        current_school = getattr(request, 'school', None)
        if not current_school or current_school.id != pk:
            raise PermissionDenied("You do not have permission to view other schools.")
            
    school = get_object_or_404(School, pk=pk)
    return render(request, 'schools/school_detail.html', {'school': school})


def school_create(request):
    """Create a new school via staff admin."""
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'School created successfully!')
            return redirect('school_list')
    else:
        form = SchoolForm()
    return render(request, 'schools/school_form.html', {'form': form, 'title': 'Add School'})


@login_required
def school_update(request, pk):
    """Prevent School B from editing School A's profile"""
    if not request.user.is_superuser:
        current_school = getattr(request, 'school', None)
        if not current_school or current_school.id != pk:
            raise PermissionDenied("You do not have permission to edit other schools.")
            
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, "School details updated successfully.")
            return redirect('dashboard')
    else:
        form = SchoolForm(instance=school)
        
    return render(request, 'schools/school_form.html', {'form': form, 'school': school})


def school_delete(request, pk):
    """Delete a school."""
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        school.delete()
        messages.success(request, 'School deleted successfully!')
        return redirect('school_list')
    return render(request, 'schools/school_confirm_delete.html', {'school': school})


# ---------------------- Multi-Tenant Onboarding ----------------------
def create_default_school_periods(school):
    """Auto-populates standard 8-period schedule with default start/end times."""
    base_time = datetime.strptime("08:00", "%H:%M")
    
    for wing in ['Junior', 'Middle', 'Senior']:
        current_time = base_time
        for p_num in range(1, 9):
            p_start = current_time.time()
            current_time += timedelta(minutes=45)
            p_end = current_time.time()

            is_assembly = (p_num == 1)
            is_lunch = (p_num == 5)

            PeriodDefinition.objects.get_or_create(
                school=school,
                wing=wing,
                period_number=p_num,
                defaults={
                    'start_time': p_start,
                    'end_time': p_end,
                    'is_assembly': is_assembly,
                    'is_lunch': is_lunch,
                    'is_break': False,
                }
            )


@transaction.atomic
def register_school(request):
    """Self-service registration for new schools."""
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST)
        if form.is_valid():
            school = form.save(commit=False)

            # Default Session Dates
            today = date.today()
            school.session_start = date(today.year, 4, 1)
            school.session_end = date(today.year + 1, 3, 31)

            # Default Operating Hours
            school.opening_time = time(8, 0)
            school.closing_time = time(14, 0)

            # Save full School model instance
            school.save()

            # Create Admin User
            email = form.cleaned_data['admin_email']
            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['admin_name']
            )

            # Assign Group & Profile
            admin_group, _ = Group.objects.get_or_create(name='Admin')
            user.groups.add(admin_group)

            UserProfile.objects.create(
                user=user,
                school=school,
                role='SCHOOL_ADMIN'
            )

            # Initialize Periods (disabled — admins create periods manually)
            # create_default_school_periods(school)

            messages.success(request, f"🎉 {school.name} registered successfully! Log in to access your workspace.")
            return redirect('login')
        else:
            print("❌ Form Validation Errors:", form.errors)
    else:
        form = SchoolRegistrationForm()

    return render(request, 'schools/register.html', {'form': form})
# Add this inside D:\timetable_project\apps\schools\views.py

@login_required
def switch_school_context(request, school_id):
    """
    Allows Master Admin (Superuser) to switch between schools on the frontend UI.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Only Master Admin can switch schools.")
        return redirect('dashboard')
    
    if school_id == 0:
        # Clear selected school to view platform-wide overview
        if 'master_selected_school_id' in request.session:
            del request.session['master_selected_school_id']
        messages.info(request, "Switched to Global Platform View.")
    else:
        school = get_object_or_404(School, id=school_id)
        request.session['master_selected_school_id'] = school.id
        messages.success(request, f"Active workspace switched to: {school.name}")

    # Return to the previous page or dashboard
    next_url = request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)