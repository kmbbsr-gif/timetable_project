from django.contrib import admin
from .models import School

admin.site.register(School)

from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = "Keshab Sir's School Studio Admin"
    site_title = "Keshab Sir's School Studio"
    index_title = "Welcome to Keshab Sir's School Studio"

admin_site = CustomAdminSite(name='myadmin')