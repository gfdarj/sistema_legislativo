from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, F

from www.models import Proposicao, Autor, TipoProposicao, Comissao, Tramitacao
from www.forms import TramitacaoForm, AutorForm, ProposicaoForm


class ProposicaoListView(LoginRequiredMixin, ListView):
    model = Proposicao
    template_name = "www/proposicao_list.html"
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
            qs = qs.filter(numero_proposicao__icontains=numero)

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


class ProposicaoDetailView(LoginRequiredMixin, DetailView):
    model = Proposicao
    template_name = "www/proposicao_detail.html"


class ProposicaoCreateView(LoginRequiredMixin, CreateView):
    model = Proposicao
    form_class = ProposicaoForm
    template_name = "www/proposicao_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProposicaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Proposicao
    fields = "__all__"
    template_name = "www/proposicao_form.html"
    success_url = reverse_lazy("proposicao_list")




class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "www/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1️⃣ Quantidade de proposições por TIPO
        context["proposicoes_por_tipo"] = (
            Proposicao.objects
            .values(
                "tipo__nome",
                "tipo__chave"
            )
            .annotate(total=Count("id"))
            .order_by("tipo__nome")
        )

        # 2️⃣ Proposições aguardando parecer (por tipo)
        context["aguardando_parecer_por_tipo"] = (
            Proposicao.objects
            .filter(pareceres__isnull=True)
            .values("tipo__nome")
            .annotate(total=Count("id"))
            .order_by("tipo__nome")
        )

        # 3️⃣ Tempo médio de tramitação (GERAL)
        tempos = []

        for pl in Proposicao.objects.all():
            trams = pl.tramitacoes.order_by("data_evento")
            if trams.count() >= 2:
                dias = (trams.last().data_evento - trams.first().data_evento).days
                tempos.append(dias)

        context["tempo_medio_tramitacao"] = (
            round(sum(tempos) / len(tempos), 1) if tempos else 0
        )

        return context




class AutorListView(LoginRequiredMixin, ListView):
    model = Autor
    template_name = "www/autor_list.html"
    context_object_name = "autores"

    def get_queryset(self):
        qs = Autor.objects.all()
        ativo = self.request.GET.get("ativo")
        if ativo == "1":
            qs = qs.filter(ativo=True)
        elif ativo == "0":
            qs = qs.filter(ativo=False)
        return qs


class AutorCreateView(LoginRequiredMixin, CreateView):
    model = Autor
    form_class = AutorForm
    template_name = "www/autor_form.html"
    success_url = reverse_lazy("autor_list")


class AutorUpdateView(LoginRequiredMixin, UpdateView):
    model = Autor
    form_class = AutorForm
    template_name = "www/autor_form.html"
    success_url = reverse_lazy("autor_list")


class AutorDeleteView(LoginRequiredMixin, DeleteView):
    model = Autor
    template_name = "www/autor_confirm_delete.html"
    success_url = reverse_lazy("autor_list")



class TipoProposicaoListView(LoginRequiredMixin, ListView):
    model = TipoProposicao
    template_name = "www/tipoproposicao_list.html"
    paginate_by = 20




class ComissaoListView(LoginRequiredMixin, ListView):
    model = Comissao
    template_name = "www/comissao_list.html"
    paginate_by = 20



class TramitacaoListView(LoginRequiredMixin, ListView):
    model = Tramitacao
    template_name = "www/tramitacao_list.html"

    def get_queryset(self):
        self.pl = get_object_or_404(Proposicao, pk=self.kwargs["proposicao_id"])
        return Tramitacao.objects.filter(pl=self.pl)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pl"] = self.pl
        return context


class TramitacaoCreateView(LoginRequiredMixin, CreateView):
    model = Tramitacao
    form_class = TramitacaoForm
    template_name = "www/tramitacao_form.html"

    def form_valid(self, form):
        form.instance.pl = get_object_or_404(Proposicao, pk=self.kwargs["proposicao_id"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "tramitacao_list",
            kwargs={"proposicao_id": self.kwargs["proposicao_id"]}
        )


