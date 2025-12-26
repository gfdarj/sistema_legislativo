from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("", include("www.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]
