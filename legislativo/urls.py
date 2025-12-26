from django.urls import path
from .views import *

urlpatterns = [
    path("", ProjetoLeiListView.as_view(), name="pl_list"),
    path("novo/", ProjetoLeiCreateView.as_view(), name="pl_create"),
    path("<int:pk>/", ProjetoLeiDetailView.as_view(), name="pl_detail"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]