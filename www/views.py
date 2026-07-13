from django.http import Http404, HttpResponse
from django.db import transaction
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from weasyprint import HTML
from django.forms import formset_factory
#from django.forms import modelformset_factory
#from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
#-----
from www.models import *
from www.forms import *



def teste_ckeditor(request):
    form = TesteCKForm()
    return render(request, "teste_ckeditor.html", {"form": form})


###################################################################################

class ProposicaoListView(LoginRequiredMixin, ListView):
    model = Proposicao
    template_name = "www/proposicao_list.html"
    paginate_by = 20

    def _tipo_selecionado(self):
        """Tipo escolhido no filtro; por padrão, 'Projeto Lei' (PL)."""
        if hasattr(self, "_tipo_cache"):
            return self._tipo_cache

        tipo = self.request.GET.get("tipo")
        if tipo is None:
            tipo_pl = TipoProposicao.objects.filter(sigla="PL").first()
            tipo = str(tipo_pl.id) if tipo_pl else None

        self._tipo_cache = tipo
        return tipo

    def _comissao_selecionada(self):
        """Comissão escolhida no filtro; por padrão, a comissão do usuário."""
        if hasattr(self, "_comissao_cache"):
            return self._comissao_cache

        comissao = self.request.GET.get("comissao")
        if comissao is None:
            user = self.request.user
            if getattr(user, "perfil", None) and user.perfil.comissao_padrao_id:
                comissao = str(user.perfil.comissao_padrao_id)

        self._comissao_cache = comissao
        return comissao

    def get_queryset(self):
        qs = (
            Proposicao.objects
            .annotate(
                ultima_data=models.Max("tramitacoes__data_entrada")
            )
            .select_related("tipo")
            .prefetch_related(
                "autores",
                "tramitacoes",
                "tramitacoes__relator",
                "tramitacoes__reuniao",
                "tramitacoes__pareceres_vencidos",
            )
        )

        user = self.request.user

        # 🔒 Restrição por comissão (baseada na ÚLTIMA tramitação)
        if not user.is_superuser:
            try:
                comissao_usuario = user.perfil.comissao_padrao
                qs = qs.filter(
                    tramitacoes__data_entrada=models.F("ultima_data"),
                    tramitacoes__comissao=comissao_usuario,
                )
            except Exception:
                return qs.none()

        # 🔍 Filtros da tela
        tipo = self._tipo_selecionado()
        numero = self.request.GET.get("numero")
        autor = self.request.GET.get("autor")
        comissao_filtro = self._comissao_selecionada()
        aguardando_parecer = self.request.GET.get("aguardando_parecer")

        if tipo:
            qs = qs.filter(tipo_id=tipo)

        if numero:
            qs = qs.filter(
                Q(numero__icontains=numero) |
                Q(numero_formatado__icontains=numero)
            )

        if autor:
            qs = qs.filter(autores__id=autor)

        if comissao_filtro:
            qs = qs.filter(
                tramitacoes__data_entrada=models.F("ultima_data"),
                tramitacoes__comissao_id=comissao_filtro
            )

        # 🟡 Aguardando parecer do relator (NOVA REGRA CORRETA)
        if aguardando_parecer == "1":
            qs = (
                qs
                .exclude(tramitacoes__relator__isnull=False)
            )

        return qs.distinct().order_by("-ultima_data", "-data_publicacao")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = self.request.GET.copy()
        params.pop("page", None)

        context["querystring"] = params.urlencode()

        context["tipos"] = TipoProposicao.objects.filter(ativo=True)
        context["tipo_selecionado"] = self._tipo_selecionado()
        context["comissao_selecionada"] = self._comissao_selecionada()
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
            ultima = obj.tramitacoes.order_by("-data_entrada").first()
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

        # 🔹 Proposições com data da última tramitação
        proposicoes = (
            Proposicao.objects
            .annotate(
                ultima_data=models.Max("tramitacoes__data_entrada")
            )
        )

        # 🔹 Filtra apenas a última tramitação da comissão
        if comissao:
            proposicoes = proposicoes.filter(
                tramitacoes__data_entrada=models.F("ultima_data"),
                tramitacoes__comissao=comissao
            )

        # 1️⃣ Total na comissão
        total_na_comissao = proposicoes.distinct().count()

        # 2️⃣ Aguardando parecer do relator
        #
        # Regra:
        # - última tramitação na comissão
        # - NÃO existe parecer do relator preenchido nessa tramitação
        aguardando_parecer = (
            proposicoes
            .exclude(
                tramitacoes__relator__isnull=False
            )
            .distinct()
            .count()
        )

        # 3️⃣ Entradas no período (últimos 30 dias)
        data_inicio = now().date() - timedelta(days=30)

        entradas_periodo = (
            Tramitacao.objects
            .filter(
                data_entrada__gte=data_inicio
            )
        )

        if comissao:
            entradas_periodo = entradas_periodo.filter(comissao=comissao)

        entradas_periodo = entradas_periodo.count()

        # 4️⃣ Tempo médio na comissão (dias)
        tramitacoes = Tramitacao.objects.all()

        if comissao:
            tramitacoes = tramitacoes.filter(comissao=comissao)

        tramitacoes = tramitacoes.annotate(
            dias=models.ExpressionWrapper(
                now().date() - models.F("data_entrada"),
                output_field=models.DurationField()
            )
        )

        if tramitacoes.exists():
            tempo_medio = (
                sum(t.dias.days for t in tramitacoes) / tramitacoes.count()
            )
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


class TramitacoesPainelView(LoginRequiredMixin, ListView):
    template_name = "www/tramitacoes/tramitacoes_painel.html"
    context_object_name = "proposicoes"
    paginate_by = 25

    def _get_filtros(self):
        """Calcula (uma única vez) comissão/reunião selecionadas a partir do GET."""
        if hasattr(self, "_filtros_cache"):
            return self._filtros_cache

        user = self.request.user

        # 🔒 Comissão: vem do filtro selecionado, ou por padrão a comissão
        # registrada para o usuário (mesmo se ele for superusuário)
        comissao_id = self.request.GET.get("comissao")
        if comissao_id:
            comissao_selecionada = Comissao.objects.filter(pk=comissao_id).first()
        elif getattr(user, "perfil", None) and user.perfil.comissao_padrao_id:
            comissao_selecionada = user.perfil.comissao_padrao
        else:
            comissao_selecionada = None

        # 🔹 Reuniões do ano corrente, restritas à comissão selecionada (se houver)
        ano_atual = now().year
        reunioes_qs = Reuniao.objects.filter(data__year=ano_atual).select_related("comissao")
        if comissao_selecionada:
            reunioes_qs = reunioes_qs.filter(comissao=comissao_selecionada)
        reunioes_qs = reunioes_qs.order_by("comissao__sigla", "-data")

        reuniao_id = self.request.GET.get("reuniao")
        reuniao_selecionada = None
        if reuniao_id:
            reuniao_selecionada = reunioes_qs.filter(pk=reuniao_id).first()

        self._filtros_cache = {
            "ano_atual": ano_atual,
            "comissao_selecionada": comissao_selecionada,
            "reunioes_qs": reunioes_qs,
            "reuniao_selecionada": reuniao_selecionada,
        }
        return self._filtros_cache

    def get_queryset(self):
        filtros = self._get_filtros()

        # 🔹 Só entram proposições que já têm alguma tramitação cadastrada
        proposicoes = (
            Proposicao.objects
            .select_related("tipo")
            .filter(tramitacoes__isnull=False)
        )

        if filtros["comissao_selecionada"]:
            proposicoes = proposicoes.filter(
                tramitacoes__comissao=filtros["comissao_selecionada"]
            )

        if filtros["reuniao_selecionada"]:
            proposicoes = proposicoes.filter(
                tramitacoes__reuniao=filtros["reuniao_selecionada"]
            )

        return proposicoes.distinct().order_by("-data_publicacao")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtros = self._get_filtros()

        context.update({
            "comissoes": Comissao.objects.filter(ativa=True),
            "reunioes": filtros["reunioes_qs"],
            "comissao_selecionada": filtros["comissao_selecionada"],
            "reuniao_selecionada": filtros["reuniao_selecionada"],
            "ano_atual": filtros["ano_atual"],
        })
        return context


###################################################################################


class AutorListView(LoginRequiredMixin, ListView):
    model = Autor
    template_name = "www/autores/autor_list.html"
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
    template_name = "www/autores/autor_form.html"
    success_url = reverse_lazy("autor_list")


class AutorUpdateView(LoginRequiredMixin, UpdateView):
    model = Autor
    form_class = AutorForm
    template_name = "www/autores/autor_form.html"
    success_url = reverse_lazy("autor_list")


class AutorDeleteView(LoginRequiredMixin, DeleteView):
    model = Autor
    template_name = "www/autores/autor_confirm_delete.html"
    success_url = reverse_lazy("autor_list")


###################################################################################

class TipoProposicaoListView(LoginRequiredMixin, ListView):
    model = TipoProposicao
    template_name = "www/tiposproposicoes/tipoproposicao_list.html"
    paginate_by = 20


###################################################################################


class ComissaoListView(LoginRequiredMixin, ListView):
    model = Comissao
    template_name = "www/comissoes/comissao_list.html"
    paginate_by = 20


###################################################################################

class TramitacaoListView(LoginRequiredMixin, ListView):
    model = Tramitacao
    template_name = "www/tramitacoes/tramitacao_list.html"
    context_object_name = "tramitacoes"

    def get_queryset(self):
        proposicao_id = self.kwargs["proposicao_id"]

        try:
            self.proposicao = Proposicao.objects.get(pk=proposicao_id)
        except Proposicao.DoesNotExist:
            raise Http404("Proposição não encontrada")

        user = self.request.user

        # 🔒 Restrição por comissão (baseada na ÚLTIMA tramitação)
        if not user.is_superuser:
            ultima = (
                self.proposicao.tramitacoes
                .order_by("-data_entrada")
                .first()
            )

            if (
                not ultima or
                ultima.comissao != user.perfil.comissao_padrao
            ):
                raise Http404("Acesso negado")

        return (
            Tramitacao.objects
            .filter(proposicao=self.proposicao)
            .select_related(
                "proposicao",
                "comissao",
                "relator",
                "reuniao",
            )
            .prefetch_related(
                "pareceres_vencidos",
                "pareceres_vencidos__relator",
                "pareceres_vencidos__reuniao",
            )
            .order_by("data_entrada")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposicao"] = self.proposicao
        return context


# View de criação da Tramitação (já com o parecer do relator embutido)
class TramitacaoComParecerCreateView(LoginRequiredMixin, View):
    template_name = "www/tramitacoes/tramitacao_unica_form.html"

    def get(self, request, proposicao_id):
        proposicao = get_object_or_404(Proposicao, pk=proposicao_id)
        tramitacao_form = TramitacaoForm(user=request.user)

        return render(request, self.template_name, {
            "proposicao": proposicao,
            "tramitacao_form": tramitacao_form,
        })

    @transaction.atomic
    def post(self, request, proposicao_id):
        proposicao = get_object_or_404(Proposicao, pk=proposicao_id)

        # 🔒 mesma restrição de comissão usada nas outras views de tramitação
        user = request.user
        if not user.is_superuser:
            ultima = proposicao.tramitacoes.order_by("-data_entrada").first()
            if ultima and ultima.comissao != getattr(user.perfil, "comissao_padrao", None):
                raise Http404("Acesso negado")

        tramitacao_form = TramitacaoForm(request.POST, user=user)

        if tramitacao_form.is_valid():
            tramitacao = tramitacao_form.save(commit=False)
            tramitacao.proposicao = proposicao

            # 🔒 força a comissão do usuário, exceto para superusuário
            if not user.is_superuser:
                tramitacao.comissao = user.perfil.comissao_padrao

            tramitacao.save()

            # Votos vencidos (0 a muitos) são adicionados depois, na tela
            # de detalhe da tramitação — agora que ela já tem um id salvo.
            return redirect(
                "tramitacao_detail",
                proposicao_id=proposicao.pk,
                t=tramitacao.pk,
            )

        # ❌ Formulário inválido: re-renderiza a tela com os erros.
        return render(request, self.template_name, {
            "proposicao": proposicao,
            "tramitacao_form": tramitacao_form,
        })



class TramitacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Tramitacao
    form_class = TramitacaoForm
    template_name = "www/tramitacoes/tramitacao_form.html"
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
        if obj.proposicao_id != self.proposicao.pk:
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
            "tramitacao_detail",
            kwargs={"proposicao_id": self.proposicao.pk, "t": self.object.pk}
        )


class TramitacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Tramitacao
    template_name = "www/tramitacoes/tramitacao_confirm_delete.html"
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
        if obj.proposicao_id != self.proposicao.pk:
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
            kwargs={"proposicao_id": self.proposicao.pk}
        )


class TramitacaoDetailView(LoginRequiredMixin, DetailView):
    model = Tramitacao
    template_name = "www/tramitacoes/tramitacao_detail.html"
    context_object_name = "tramitacao"
    pk_url_kwarg = "t"  # 👈 id da tramitação

    def dispatch(self, request, *args, **kwargs):
        try:
            self.proposicao = Proposicao.objects.get(
                pk=kwargs["proposicao_id"]
            )
        except Proposicao.DoesNotExist:
            raise Http404("Proposição não encontrada")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Tramitacao.objects
            .select_related("proposicao", "comissao", "relator", "reuniao")
            .prefetch_related("pareceres_vencidos__relator", "pareceres_vencidos__reuniao")
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        # 🔐 garante que a tramitação pertence à proposição
        if obj.proposicao_id != self.proposicao.pk:
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


class TramitacaoPDFView(LoginRequiredMixin, View):
    """
    Gera o PDF do parecer da tramitação
    """

    def get(self, request, pk, *args, **kwargs):
        tramitacao = get_object_or_404(Tramitacao, pk=pk)

        html_string = render_to_string(
            "www/tramitacoes/tramitacao_pdf.html",
            {"tramitacao": tramitacao}
        )

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="parecer_tramitacao_{pk}.pdf"'
        )

        return response



###################################################################################

class ParecerVencidoCreateView(LoginRequiredMixin, CreateView):
    model = ParecerVencido
    form_class = ParecerVencidoForm
    template_name = "www/pareceres_vencidos/parecervencido_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.tramitacao = get_object_or_404(
            Tramitacao, pk=kwargs["tramitacao_id"]
        )
        user = request.user

        # 🔒 permissão por comissão
        if not user.is_superuser:
            if self.tramitacao.comissao != user.perfil.comissao_padrao:
                raise Http404("Acesso negado")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tramitacao = self.tramitacao
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tramitacao"] = self.tramitacao
        context["proposicao"] = self.tramitacao.proposicao
        return context

    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_detail",
            kwargs={
                "proposicao_id": self.tramitacao.proposicao_id,
                "t": self.tramitacao.pk,
            }
        )


class ParecerVencidoUpdateView(LoginRequiredMixin, UpdateView):
    model = ParecerVencido
    form_class = ParecerVencidoForm
    template_name = "www/pareceres_vencidos/parecervencido_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.tramitacao = get_object_or_404(
            Tramitacao, pk=kwargs["tramitacao_id"]
        )
        user = request.user

        if not user.is_superuser:
            if self.tramitacao.comissao != user.perfil.comissao_padrao:
                raise Http404("Acesso negado")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # 🔐 garante que o voto vencido pertence à tramitação da URL
        if obj.tramitacao_id != self.tramitacao.pk:
            raise Http404("Parecer vencido inválido")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tramitacao"] = self.tramitacao
        context["proposicao"] = self.tramitacao.proposicao
        return context

    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_detail",
            kwargs={
                "proposicao_id": self.tramitacao.proposicao_id,
                "t": self.tramitacao.pk,
            }
        )


class ParecerVencidoDeleteView(LoginRequiredMixin, DeleteView):
    model = ParecerVencido
    template_name = "www/pareceres_vencidos/parecervencido_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.tramitacao = get_object_or_404(
            Tramitacao, pk=kwargs["tramitacao_id"]
        )
        user = request.user

        if not user.is_superuser:
            if self.tramitacao.comissao != user.perfil.comissao_padrao:
                raise Http404("Acesso negado")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if obj.tramitacao_id != self.tramitacao.pk:
            raise Http404("Parecer vencido inválido")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tramitacao"] = self.tramitacao
        context["proposicao"] = self.tramitacao.proposicao
        return context

    def get_success_url(self):
        return reverse_lazy(
            "tramitacao_detail",
            kwargs={
                "proposicao_id": self.tramitacao.proposicao_id,
                "t": self.tramitacao.pk,
            }
        )


###################################################################################


class ReuniaoListView(LoginRequiredMixin, ListView):
    model = Reuniao
    template_name = "www/reunioes/reuniao_list.html"
    context_object_name = "reunioes"
    paginate_by = 10

    def _comissao_selecionada(self):
        if hasattr(self, "_comissao_cache"):
            return self._comissao_cache

        comissao = self.request.GET.get("comissao")
        if comissao is None:
            user = self.request.user
            if getattr(user, "perfil", None) and user.perfil.comissao_padrao_id:
                comissao = str(user.perfil.comissao_padrao_id)

        self._comissao_cache = comissao
        return comissao

    def _ano_selecionado(self):
        return self.request.GET.get("ano") or ""

    def get_queryset(self):
        qs = super().get_queryset().select_related("comissao")

        ano = self._ano_selecionado()
        if ano:
            qs = qs.filter(data__year=ano)

        comissao = self._comissao_selecionada()
        if comissao:
            qs = qs.filter(comissao_id=comissao)

        return qs.order_by("-data", "-hora")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()

        context["comissoes"] = Comissao.objects.filter(ativa=True)
        context["comissao_selecionada"] = self._comissao_selecionada()
        context["ano_selecionado"] = self._ano_selecionado()

        context["anos"] = (
            Reuniao.objects
            .dates("data", "year", order="DESC")
        )

        return context


class ReuniaoCreateView(LoginRequiredMixin, CreateView):
    model = Reuniao
    form_class = ReuniaoForm
    template_name = "www/reunioes/reuniao_form.html"
    success_url = reverse_lazy("reuniao_list")

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        if getattr(user, "perfil", None) and user.perfil.comissao_padrao_id:
            initial["comissao"] = user.perfil.comissao_padrao_id
        return initial


class ReuniaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Reuniao
    form_class = ReuniaoForm
    template_name = "www/reunioes/reuniao_form.html"
    success_url = reverse_lazy("reuniao_list")


class ReuniaoDetailView(LoginRequiredMixin, DetailView):
    model = Reuniao
    template_name = "www/reunioes/reuniao_detail.html"
    context_object_name = "reuniao"


class ReuniaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Reuniao
    template_name = "www/reunioes/reuniao_confirm_delete.html"
    success_url = reverse_lazy("reuniao_list")



