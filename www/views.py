from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, F

from .models import ProjetoLei, Autor, TipoProposicao, Comissao


class ProjetoLeiListView(ListView):
    model = ProjetoLei
    template_name = "www/pl_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()

        tipo = self.request.GET.get("tipo")
        numero = self.request.GET.get("numero")
        comissao = self.request.GET.get("comissao")
        autor = self.request.GET.get("autor")
        aguardando_parecer = self.request.GET.get("aguardando_parecer")

        if tipo:
            qs = qs.filter(tipo_id=tipo)

        if numero:
            qs = qs.filter(numero_pl__icontains=numero)

        if comissao:
            qs = qs.filter(comissao_id=comissao)

        if autor:
            qs = qs.filter(autores__id=autor)

        if aguardando_parecer == "1":
            qs = qs.filter(pareceres__isnull=True)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipos"] = TipoProposicao.objects.filter(ativo=True)
        context["comissoes"] = Comissao.objects.filter(ativa=True)
        context["autores"] = Autor.objects.all().order_by("nome")
        return context


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

        # 1️⃣ Quantidade de proposições por TIPO
        context["proposicoes_por_tipo"] = (
            ProjetoLei.objects
            .values(
                "tipo__nome",
                "tipo__chave"
            )
            .annotate(total=Count("id"))
            .order_by("tipo__nome")
        )

        # 2️⃣ Proposições aguardando parecer (por tipo)
        context["aguardando_parecer_por_tipo"] = (
            ProjetoLei.objects
            .filter(pareceres__isnull=True)
            .values("tipo__nome")
            .annotate(total=Count("id"))
            .order_by("tipo__nome")
        )

        # 3️⃣ Tempo médio de tramitação (GERAL)
        tempos = []

        for pl in ProjetoLei.objects.all():
            trams = pl.tramitacoes.order_by("data_evento")
            if trams.count() >= 2:
                dias = (trams.last().data_evento - trams.first().data_evento).days
                tempos.append(dias)

        context["tempo_medio_tramitacao"] = (
            round(sum(tempos) / len(tempos), 1) if tempos else 0
        )

        return context


class AutorListView(ListView):
    model = Autor
    template_name = "www/autor_list.html"


class AutorCreateView(CreateView):
    model = Autor
    fields = ["chave", "nome", "sexo"]
    template_name = "www/autor_form.html"
    success_url = reverse_lazy("autor_list")


class AutorUpdateView(UpdateView):
    model = Autor
    fields = ["chave", "nome", "sexo"]
    template_name = "www/autor_form.html"
    success_url = reverse_lazy("autor_list")


class AutorDeleteView(DeleteView):
    model = Autor
    template_name = "www/autor_confirm_delete.html"
    success_url = reverse_lazy("autor_list")
