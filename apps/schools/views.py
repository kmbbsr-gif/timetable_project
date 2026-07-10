from rest_framework import viewsets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import School
from .serializers import SchoolSerializer
from .forms import SchoolForm
from apps.teachers.models import Teacher
from apps.subjects.models import Subject
from apps.academic.models import Class

# ---------------------- API ViewSet ----------------------
class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = []  # Adjust later

# ---------------------- Dashboard ----------------------
# @login_required
def dashboard(request):
    context = {
        'school_count': School.objects.count(),
        'teacher_count': Teacher.objects.count(),
        'subject_count': Subject.objects.count(),
        'class_count': Class.objects.count(),
    }
    return render(request, 'dashboard.html', context)

# ---------------------- School CRUD Views ----------------------

def school_list(request):
    """List all schools"""
    schools = School.objects.all()
    return render(request, 'schools/school_list.html', {'schools': schools})

def school_detail(request, pk):
    """Show detailed view of a single school"""
    school = get_object_or_404(School, pk=pk)
    return render(request, 'schools/school_detail.html', {'school': school})

def school_create(request):
    """Create a new school"""
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'School created successfully!')
            return redirect('school_list')
    else:
        form = SchoolForm()
    return render(request, 'schools/school_form.html', {'form': form, 'title': 'Add School'})

def school_update(request, pk):
    """Update an existing school"""
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, 'School updated successfully!')
            return redirect('school_detail', pk=school.pk)
    else:
        form = SchoolForm(instance=school)
    return render(request, 'schools/school_form.html', {'form': form, 'title': 'Edit School'})

def school_delete(request, pk):
    """Delete a school"""
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        school.delete()
        messages.success(request, 'School deleted successfully!')
        return redirect('school_list')
    return render(request, 'schools/school_confirm_delete.html', {'school': school})

from apps.teachers.utils import get_average_load

def dashboard(request):
    context = {
        'school_count': School.objects.count(),
        'teacher_count': Teacher.objects.count(),
        'subject_count': Subject.objects.count(),
        'class_count': Class.objects.count(),
        'avg_teacher_load': get_average_load(),
    }
    return render(request, 'dashboard.html', context)
