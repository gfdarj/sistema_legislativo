from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from www.models import Proposicao, Autor, TipoProposicao, Comissao, Tramitacao
from www.forms import TramitacaoForm, AutorForm, ProposicaoForm


###################################################################################

class ProposicaoListView(LoginRequiredMixin, ListView):
    model = Proposicao
    template_name = "www/proposicao_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Proposicao.objects
            .annotate(
                ultima_data=models.Max("tramitacoes__data_evento")
            )
            .prefetch_related("autores", "tramitacoes")
            .select_related("tipo")
        )

        user = self.request.user

        # 🔒 RESTRIÇÃO POR COMISSÃO (BASEADA NA ÚLTIMA TRAMITAÇÃO)
        if not user.is_superuser:
            try:
                comissao_usuario = user.perfil.comissao_padrao
                qs = qs.filter(
                    tramitacoes__data_evento=models.F("ultima_data"),
                    tramitacoes__comissao=comissao_usuario,
                )
            except:
                return qs.none()

        # 🔍 FILTROS DA TELA
        tipo = self.request.GET.get("tipo")
        numero = self.request.GET.get("numero")
        autor = self.request.GET.get("autor")
        aguardando_parecer = self.request.GET.get("aguardando_parecer")

        if tipo:
            qs = qs.filter(tipo_id=tipo)

        if numero:
            qs = qs.filter(numero__icontains=numero)

        if autor:
            qs = qs.filter(autores__id=autor)

        if aguardando_parecer == "1":
            qs = qs.filter(pareceres__isnull=True)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tipos"] = TipoProposicao.objects.filter(ativo=True)
        context["autores"] = Autor.objects.filter(ativo=True).order_by("nome")

        # Combo de comissão (informativo)
        if self.request.user.is_superuser:
            context["comissoes"] = Comissao.objects.filter(ativa=True)
        else:
            context["comissoes"] = Comissao.objects.filter(
                id=self.request.user.perfil.comissao_padrao_id
            )

        return context


class ProposicaoDetailView(LoginRequiredMixin, DetailView):
    model = Proposicao
    template_name = "www/proposicao_detail.html"


class ProposicaoCreateView(LoginRequiredMixin, CreateView):
    model = Proposicao
    form_class = ProposicaoForm
    template_name = "www/proposicao_form.html"
    success_url = reverse_lazy("proposicao_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ProposicaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Proposicao
    form_class = ProposicaoForm
    template_name = "www/proposicao_form.html"
    success_url = reverse_lazy("proposicao_list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        if user.is_superuser:
            return obj

        try:
            ultima = obj.tramitacoes.order_by("-data_evento").first()
            if not ultima or ultima.comissao != user.perfil.comissao_padrao:
                raise Http404("Acesso negado")
        except:
            raise Http404("Acesso negado")

        return obj


###################################################################################

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "www/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        # 🔒 Comissão do usuário
        if user.is_superuser:
            comissao = None
        else:
            comissao = user.perfil.comissao_padrao

        # Base: proposições com última tramitação
        proposicoes = (
            Proposicao.objects
            .annotate(
                ultima_data=models.Max("tramitacoes__data_evento")
            )
        )

        if comissao:
            proposicoes = proposicoes.filter(
                tramitacoes__data_evento=models.F("ultima_data"),
                tramitacoes__comissao=comissao
            )

        # 1️⃣ Total na comissão
        total_na_comissao = proposicoes.count()

        # 2️⃣ Aguardando parecer (relator null na última tramitação)
        aguardando_parecer = proposicoes.filter(
            tramitacoes__data_evento=models.F("ultima_data"),
            tramitacoes__relator__isnull=True
        ).count()

        # 3️⃣ Entradas no período (últimos 30 dias)
        data_inicio = now().date() - timedelta(days=30)

        entradas_periodo = Tramitacao.objects.filter(
            data_evento__gte=data_inicio,
            comissao=comissao if comissao else models.F("comissao")
        ).count()

        # 4️⃣ Tempo médio na comissão (dias)
        tempos = (
            Tramitacao.objects
            .filter(
                comissao=comissao if comissao else models.F("comissao")
            )
            .annotate(
                dias=models.ExpressionWrapper(
                    now().date() - models.F("data_evento"),
                    output_field=models.DurationField()
                )
            )
        )

        if tempos.exists():
            tempo_medio = sum(
                t.dias.days for t in tempos
            ) / tempos.count()
        else:
            tempo_medio = 0

        context.update({
            "comissao": comissao,
            "total_na_comissao": total_na_comissao,
            "aguardando_parecer": aguardando_parecer,
            "entradas_periodo": entradas_periodo,
            "tempo_medio": round(tempo_medio, 1),
        })

        return context


###################################################################################


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


###################################################################################

class TipoProposicaoListView(LoginRequiredMixin, ListView):
    model = TipoProposicao
    template_name = "www/tipoproposicao_list.html"
    paginate_by = 20


###################################################################################


class ComissaoListView(LoginRequiredMixin, ListView):
    model = Comissao
    template_name = "www/comissao_list.html"
    paginate_by = 20


###################################################################################

class TramitacaoListView(LoginRequiredMixin, ListView):
    model = Tramitacao
    template_name = "www/tramitacao_list.html"
    context_object_name = "tramitacoes"

    def get_queryset(self):
        proposicao_id = self.kwargs["proposicao_id"]

        try:
            proposicao = Proposicao.objects.get(pk=proposicao_id)
        except Proposicao.DoesNotExist:
            raise Http404("Proposição não encontrada")

        user = self.request.user

        # 🔒 RESTRIÇÃO POR COMISSÃO
        if not user.is_superuser:
            try:
                ultima = proposicao.tramitacoes.order_by(
                    "-data_evento"
                ).first()

                if not ultima or ultima.comissao != user.perfil.comissao_padrao:
                    raise Http404("Acesso negado")
            except:
                raise Http404("Acesso negado")

        return (
            Tramitacao.objects
            .filter(proposicao=proposicao)
            .select_related("comissao", "relator")
            .order_by("data_evento")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposicao"] = Proposicao.objects.get(
            pk=self.kwargs["proposicao_id"]
        )
        return context




class TramitacaoCreateView(LoginRequiredMixin, CreateView):
    model = Tramitacao
    form_class = TramitacaoForm
    template_name = "www/tramitacao_form.html"

    def dispatch(self, request, *args, **kwargs):
        # garante que a proposição existe
        try:
            self.proposicao = Proposicao.objects.get(
                pk=kwargs["proposicao_id"]
            )
        except Proposicao.DoesNotExist:
            raise Http404("Proposição não encontrada")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # associa corretamente a proposição
        form.instance.proposicao = self.proposicao

        # 🔒 força comissão do usuário
        if not self.request.user.is_superuser:
            form.instance.comissao = (
                self.request.user.perfil.comissao_padrao
            )

        return super().form_valid(form)


    def get_initial(self):
        initial = super().get_initial()

        if self.request.method == "GET":
            initial["comissao"] = (
                self.request.user.perfil.comissao_padrao
            )

        return initial


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposicao"] = self.proposicao
        return context


    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_list",
            kwargs={"proposicao_id": self.proposicao.id}
        )


class TramitacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Tramitacao
    form_class = TramitacaoForm
    template_name = "www/tramitacao_form.html"
    pk_url_kwarg = "t"  # 👈 id da tramitação

    def dispatch(self, request, *args, **kwargs):
        # garante que a proposição existe
        try:
            self.proposicao = Proposicao.objects.get(
                pk=kwargs["proposicao_id"]
            )
        except Proposicao.DoesNotExist:
            raise Http404("Proposição não encontrada")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        # 🔐 garante que a tramitação pertence à proposição
        if obj.proposicao_id != self.proposicao.id:
            raise Http404("Tramitação inválida")

        # 🔒 permissão por comissão
        if not user.is_superuser:
            if obj.comissao != user.perfil.comissao_padrao:
                raise Http404("Acesso negado")

        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # 🔒 garante comissão correta
        if not self.request.user.is_superuser:
            form.instance.comissao = self.request.user.perfil.comissao_padrao

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposicao"] = self.proposicao
        return context

    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_list",
            kwargs={"proposicao_id": self.proposicao.id}
        )


class TramitacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Tramitacao
    template_name = "www/tramitacao_confirm_delete.html"
    pk_url_kwarg = "t"  # 👈 id da tramitação

    def dispatch(self, request, *args, **kwargs):
        try:
            self.proposicao = Proposicao.objects.get(
                pk=kwargs["proposicao_id"]
            )
        except Proposicao.DoesNotExist:
            raise Http404("Proposição não encontrada")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        # 🔐 garante vínculo com a proposição
        if obj.proposicao_id != self.proposicao.id:
            raise Http404("Tramitação inválida")

        # 🔒 permissão por comissão
        if not user.is_superuser:
            if obj.comissao != user.perfil.comissao_padrao:
                raise Http404("Acesso negado")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposicao"] = self.proposicao
        return context

    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_list",
            kwargs={"proposicao_id": self.proposicao.id}
        )

    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_list",
            kwargs={"proposicao_id": self.proposicao.id}
        )

###################################################################################

