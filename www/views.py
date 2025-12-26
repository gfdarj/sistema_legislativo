from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, F

from .models import ProjetoLei


class ProjetoLeiListView(ListView):
    model = ProjetoLei
    template_name = "www/pl_list.html"


class ProjetoLeiDetailView(DetailView):
    model = ProjetoLei
    template_name = "www/pl_detail.html"


class ProjetoLeiCreateView(CreateView):
    model = ProjetoLei
    fields = "__all__"
    template_name = "www/pl_form.html"
    success_url = reverse_lazy("pl_list")


class DashboardView(TemplateView):
    template_name = "www/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["pls_por_comissao"] = (
            ProjetoLei.objects
            .values(nome=F("comissao_atual__sigla"))
            .annotate(total=Count("id"))
        )

        context["pls_aguardando_parecer"] = (
            ProjetoLei.objects
            .filter(pareceres__isnull=True)
            .distinct()
            .count()
        )

        tempos = []
        for pl in ProjetoLei.objects.all():
            trams = pl.tramitacoes.order_by("data_evento")
            if trams.count() >= 2:
                tempos.append(
                    (trams.last().data_evento - trams.first().data_evento).days
                )

        context["tempo_medio_tramitacao"] = (
            round(sum(tempos) / len(tempos), 1) if tempos else 0
        )

        return context