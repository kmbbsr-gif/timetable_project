from django.urls import path
from . import views
from .views import (
    TeacherListView, TeacherDetailView, TeacherCreateView,
    TeacherUpdateView, TeacherDeleteView,
    TeacherAssignmentListView, TeacherAssignmentDetailView,
    TeacherAssignmentCreateView, TeacherAssignmentUpdateView,
    TeacherAssignmentDeleteView, teacher_load,
)

urlpatterns = [
    # ---------- Teacher Management ----------
    path('', views.TeacherListView.as_view(), name='teacher_list'),
    path('add/', views.TeacherCreateView.as_view(), name='teacher_create'),
    path('create/', views.TeacherCreateView.as_view(), name='teacher_create_alias'),
    path('<int:pk>/', views.TeacherDetailView.as_view(), name='teacher_detail'),
    path('<int:pk>/edit/', views.TeacherUpdateView.as_view(), name='teacher_update'),
    path('<int:pk>/update/', views.TeacherUpdateView.as_view(), name='teacher_update_alias'),
    path('<int:pk>/delete/', views.TeacherDeleteView.as_view(), name='teacher_delete'),

    # ---------- Teacher-Subject Assignments ----------
    path('assignments/', views.TeacherAssignmentListView.as_view(), name='teacherassignment_list'),
    path('assignments/<int:pk>/', views.TeacherAssignmentDetailView.as_view(), name='teacherassignment_detail'),
    path('assignments/add/', views.TeacherAssignmentCreateView.as_view(), name='teacherassignment_create'),
    path('assignments/create/', views.TeacherAssignmentCreateView.as_view(), name='teacherassignment_create_alias'),
    path('assignments/<int:pk>/edit/', views.TeacherAssignmentUpdateView.as_view(), name='teacherassignment_update'),
    path('assignments/<int:pk>/update/', views.TeacherAssignmentUpdateView.as_view(), name='teacherassignment_update_alias'),
    path('assignments/<int:pk>/delete/', views.TeacherAssignmentDeleteView.as_view(), name='teacherassignment_delete'),

    # ---------- Dynamic Load API ----------
    path('load/<int:teacher_id>/', views.teacher_load, name='teacher_load'),
    path('api/<int:teacher_id>/load/', views.teacher_load, name='teacher_load_api'),
]