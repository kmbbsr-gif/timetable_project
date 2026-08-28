# D:\timetable_project\config\urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.schools.views import dashboard
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Keshab Sir's School Studio Admin"
admin.site.site_title = "Keshab Sir's School Studio"
admin.site.index_title = "Welcome to Keshab Sir's School Studio"

urlpatterns = [
    path('system-master-panel-99/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard_alias'),

    path('users/', include('apps.users.urls')),
    path('accounts/', include('apps.users.urls')),
    path('schools/', include('apps.schools.urls')),
    path('academic/', include('apps.academic.urls')),
    # KEEP ONLY THIS ONE for subjects:
    path('subjects/', include('apps.subjects.urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('timetable/', include('apps.timetable.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)