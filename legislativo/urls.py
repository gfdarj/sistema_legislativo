from django.urls import path, include
from django.contrib import admin

from www.views import *

urlpatterns = [
    path("", include("www.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("teste-ckeditor/", teste_ckeditor),
]
