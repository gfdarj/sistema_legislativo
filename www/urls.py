from django.urls import path
from www.views import *
from www import views_relatorios
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path("", DashboardView.as_view(), name="dashboard"),
    path("tramitacoes/", TramitacoesPainelView.as_view(), name="tramitacoes_painel"),

    # 📊 Relatórios
    path("relatorios/situacao-comissao/",
         views_relatorios.RelatorioSituacaoComissaoView.as_view(),
         name="relatorio_situacao_comissao"),
    path("relatorios/situacao-comissao/pdf/",
         views_relatorios.RelatorioSituacaoComissaoPDFView.as_view(),
         name="relatorio_situacao_comissao_pdf"),
    path("relatorios/pendencias-reunioes/",
         views_relatorios.RelatorioPendenciasReunioesView.as_view(),
         name="relatorio_pendencias_reunioes"),
    path("relatorios/pendencias-reunioes/pdf/",
         views_relatorios.RelatorioPendenciasReunioesPDFView.as_view(),
         name="relatorio_pendencias_reunioes_pdf"),
    path("relatorios/dossie/",
         views_relatorios.RelatorioDossieView.as_view(),
         name="relatorio_dossie"),
    path("relatorios/dossie/<str:pk>/pdf/",
         views_relatorios.RelatorioDossiePDFView.as_view(),
         name="relatorio_dossie_pdf"),


    path("proposicao/", ProposicaoListView.as_view(), name="proposicao_list"),


    path("proposicao/<int:proposicao_id>/tramitacoes/", TramitacaoListView.as_view(), name="tramitacao_list"),
    ####path("proposicao/<int:proposicao_id>/tramitacoes/nova/", TramitacaoCreateView.as_view(), name="tramitacao_create"),
    # 👉 TELA ÚNICA (Tramitação + Parecer do Relator)
    path("proposicao/<str:proposicao_id>/tramitacoes/nova/", TramitacaoComParecerCreateView.as_view(), name="tramitacao_create"),
    path("proposicao/<int:proposicao_id>/tramitacoes/<int:t>/", TramitacaoDetailView.as_view(), name="tramitacao_detail"),
    path("proposicao/<int:proposicao_id>/tramitacoes/<int:t>/editar/", TramitacaoUpdateView.as_view(), name="tramitacao_update"),
    path("proposicao/<int:proposicao_id>/tramitacoes/<int:t>/excluir/", TramitacaoDeleteView.as_view(), name="tramitacao_delete"),
    path("tramitacao/<int:pk>/pdf/", TramitacaoPDFView.as_view(), name="tramitacao_pdf"),

    # 👉 Votos vencidos: telas próprias, ligadas a uma tramitação já salva
    path("tramitacao/<int:tramitacao_id>/votos-vencidos/novo/", ParecerVencidoCreateView.as_view(), name="parecer_vencido_create"),
    path("tramitacao/<int:tramitacao_id>/votos-vencidos/<int:pk>/editar/", ParecerVencidoUpdateView.as_view(), name="parecer_vencido_update"),
    path("tramitacao/<int:tramitacao_id>/votos-vencidos/<int:pk>/excluir/", ParecerVencidoDeleteView.as_view(), name="parecer_vencido_delete"),

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

