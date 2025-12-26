from django.urls import path
from .views import *

urlpatterns = [
    path("", ProjetoLeiListView.as_view(), name="pl_list"),
    path("novo/", ProjetoLeiCreateView.as_view(), name="pl_create"),
    path("<int:pk>/", ProjetoLeiDetailView.as_view(), name="pl_detail"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # Autores
    path("autores/", AutorListView.as_view(), name="autor_list"),
    path("autores/novo/", AutorCreateView.as_view(), name="autor_create"),
    path("autores/<int:pk>/editar/", AutorUpdateView.as_view(), name="autor_update"),
    path("autores/<int:pk>/excluir/", AutorDeleteView.as_view(), name="autor_delete"),

]

