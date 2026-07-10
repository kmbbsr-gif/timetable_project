from django.urls import path
from .views import (
    SessionListView, SessionDetailView, SessionCreateView, SessionUpdateView, SessionDeleteView,
    ClassListView, ClassDetailView, ClassCreateView, ClassUpdateView, ClassDeleteView,
    SectionListView, SectionDetailView, SectionCreateView, SectionUpdateView, SectionDeleteView,
    RoomListView, RoomDetailView, RoomCreateView, RoomUpdateView, RoomDeleteView,
    PeriodListView, PeriodDetailView, PeriodCreateView, PeriodUpdateView, PeriodDeleteView, ClassSubjectListView, ClassSubjectDetailView,
    ClassSubjectCreateView, ClassSubjectUpdateView,
    ClassSubjectDeleteView,
)
from .views import (
    # ... existing imports ...
    bulk_create_periods,
)

urlpatterns = [
    # Academic Sessions
    path('sessions/', SessionListView.as_view(), name='session_list'),
    path('sessions/<int:pk>/', SessionDetailView.as_view(), name='session_detail'),
    path('sessions/create/', SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/update/', SessionUpdateView.as_view(), name='session_update'),
    path('sessions/<int:pk>/delete/', SessionDeleteView.as_view(), name='session_delete'),

    # Classes
    path('classes/', ClassListView.as_view(), name='class_list'),
    path('classes/<int:pk>/', ClassDetailView.as_view(), name='class_detail'),
    path('classes/create/', ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/update/', ClassUpdateView.as_view(), name='class_update'),
    path('classes/<int:pk>/delete/', ClassDeleteView.as_view(), name='class_delete'),

    # Sections
    path('sections/', SectionListView.as_view(), name='section_list'),
    path('sections/<int:pk>/', SectionDetailView.as_view(), name='section_detail'),
    path('sections/create/', SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/update/', SectionUpdateView.as_view(), name='section_update'),
    path('sections/<int:pk>/delete/', SectionDeleteView.as_view(), name='section_delete'),

    # Rooms
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('rooms/create/', RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/update/', RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/delete/', RoomDeleteView.as_view(), name='room_delete'),

    # Period Definitions
    path('periods/', PeriodListView.as_view(), name='period_list'),
    path('periods/<int:pk>/', PeriodDetailView.as_view(), name='period_detail'),
    path('periods/create/', PeriodCreateView.as_view(), name='period_create'),
    path('periods/<int:pk>/update/', PeriodUpdateView.as_view(), name='period_update'),
    path('periods/<int:pk>/delete/', PeriodDeleteView.as_view(), name='period_delete'),
    path('periods/bulk-create/', bulk_create_periods, name='bulk_period_create'),
    
    path('classsubjects/', ClassSubjectListView.as_view(), name='classsubject_list'),
    path('classsubjects/<int:pk>/', ClassSubjectDetailView.as_view(), name='classsubject_detail'),
    path('classsubjects/create/', ClassSubjectCreateView.as_view(), name='classsubject_create'),
    path('classsubjects/<int:pk>/update/', ClassSubjectUpdateView.as_view(), name='classsubject_update'),
    path('classsubjects/<int:pk>/delete/', ClassSubjectDeleteView.as_view(), name='classsubject_delete'),
    ]