from django.urls import path
from www.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path("", DashboardView.as_view(), name="dashboard"),


    path("proposicao/", ProposicaoListView.as_view(), name="proposicao_list"),
    path("proposicao/nova/", ProposicaoCreateView.as_view(), name="proposicao_create"),
    path("proposicao/<str:pk>/editar/", ProposicaoUpdateView.as_view(), name="proposicao_update"),


    path("proposicao/<int:proposicao_id>/tramitacoes/", TramitacaoListView.as_view(), name="tramitacao_list"),
    ####path("proposicao/<int:proposicao_id>/tramitacoes/nova/", TramitacaoCreateView.as_view(), name="tramitacao_create"),
    # 👉 TELA ÚNICA (Tramitação + Pareceres)
    path("proposicao/<str:proposicao_id>/tramitacoes/nova/", TramitacaoComParecerCreateView.as_view(), name="tramitacao_create"),
    path("proposicao/<int:proposicao_id>/tramitacoes/<int:t>/editar/", TramitacaoUpdateView.as_view(), name="tramitacao_update"),
    path("proposicao/<int:proposicao_id>/tramitacoes/<int:t>/excluir/", TramitacaoDeleteView.as_view(), name="tramitacao_delete"),
    path("tramitacao/<int:pk>/pdf/", TramitacaoPDFView.as_view(), name="tramitacao_pdf"),

    path("autores/", AutorListView.as_view(), name="autor_list"),
    path("autores/novo/", AutorCreateView.as_view(), name="autor_create"),
    path("autores/<int:pk>/editar/", AutorUpdateView.as_view(), name="autor_update"),
    path("autores/<int:pk>/excluir/", AutorDeleteView.as_view(), name="autor_delete"),


    path("reuniao/", ReuniaoListView.as_view(), name="reuniao_list"),
    path("reuniao/nova/", ReuniaoCreateView.as_view(), name="reuniao_create"),
    path("reuniao/<int:pk>/editar/", ReuniaoUpdateView.as_view(), name="reuniao_update"),
    path("reuniao/<int:pk>/", ReuniaoDetailView.as_view(), name="reuniao_detail"),
    path("reuniao/<int:pk>/excluir/", ReuniaoDeleteView.as_view(), name="reuniao_delete"),


    path("tipos/", TipoProposicaoListView.as_view(), name="tipo_list"),


    path("comissoes/", ComissaoListView.as_view(), name="comissao_list"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

