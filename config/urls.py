from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.schools.views import dashboard 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', dashboard, name='dashboard'),   # root
    path('dashboard/', dashboard, name='dashboard'),
    path('schools/', include('apps.schools.urls')),
    path('academic/', include('apps.academic.urls')),
    # Include only apps that exist for now
    path('api/v1/', include('apps.schools.urls')),
    path('subjects/', include('apps.subjects.urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('timetable/', include('apps.timetable.urls')),
    # path('generate/', generate_timetable, name='generate_timetable'),
    # path('api/v1/', include('apps.academic.urls')),      # uncomment later
    # path('api/v1/', include('apps.teachers.urls')),      # uncomment later
    # path('api/v1/', include('apps.subjects.urls')),      # uncomment later
    # path('api/v1/', include('apps.timetable.urls')),     # uncomment later
    # path('api/v1/', include('apps.reports.urls')),       # uncomment later
    # path('api/v1/', include('apps.import_export.urls')), # uncomment later
    # path('api/v1/', include('apps.analytics.urls')),     # uncomment later
    # path('api/v1/', include('apps.users.urls')),         # uncomment later
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)