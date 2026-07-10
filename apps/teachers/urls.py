from django.urls import path
from .views import (
    TeacherListView, TeacherDetailView, TeacherCreateView,
    TeacherUpdateView, TeacherDeleteView,
    TeacherAssignmentListView, TeacherAssignmentDetailView,
    TeacherAssignmentCreateView, TeacherAssignmentUpdateView,
    TeacherAssignmentDeleteView, teacher_load,
)

urlpatterns = [
    path('', TeacherListView.as_view(), name='teacher_list'),
    path('<int:pk>/', TeacherDetailView.as_view(), name='teacher_detail'),
    path('create/', TeacherCreateView.as_view(), name='teacher_create'),
    path('<int:pk>/update/', TeacherUpdateView.as_view(), name='teacher_update'),
    path('<int:pk>/delete/', TeacherDeleteView.as_view(), name='teacher_delete'),
    
     # Teacher-Subject Assignments
    path('assignments/', TeacherAssignmentListView.as_view(), name='teacherassignment_list'),
    path('assignments/<int:pk>/', TeacherAssignmentDetailView.as_view(), name='teacherassignment_detail'),
    path('assignments/create/', TeacherAssignmentCreateView.as_view(), name='teacherassignment_create'),
    path('assignments/<int:pk>/update/', TeacherAssignmentUpdateView.as_view(), name='teacherassignment_update'),
    path('assignments/<int:pk>/delete/', TeacherAssignmentDeleteView.as_view(), name='teacherassignment_delete'),
    path('load/<int:teacher_id>/', teacher_load, name='teacher_load'),
]