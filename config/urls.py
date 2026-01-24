"""
URL configuration for Deribit project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/prices/', include('apps.prices.urls')),
]
