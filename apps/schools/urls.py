from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet, school_list, school_detail, school_create, school_update, school_delete
from django.core.exceptions import PermissionDenied
from . import views

router = DefaultRouter()
router.register(r'schools', SchoolViewSet, basename='school')

urlpatterns = [
    path('', include(router.urls)),  # API endpoints: /schools/, /schools/<id>/
    # HTML views (for the web interface)
    path('list/', school_list, name='school_list'),
    path('<int:pk>/', school_detail, name='school_detail'),
    path('create/', school_create, name='school_create'),
    path('<int:pk>/update/', school_update, name='school_update'),
    path('<int:pk>/delete/', school_delete, name='school_delete'),
    path('register-school/', views.register_school, name='register_school'),
    path('switch-context/<int:school_id>/', views.switch_school_context, name='switch_school_context'),
]

