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
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
#-----
from www.models import *
from www.forms import TramitacaoForm, AutorForm, ProposicaoForm, ReuniaoForm, ParecerRelatorForm, ParecerVencidoForm


###################################################################################

class ProposicaoListView(LoginRequiredMixin, ListView):
    model = Proposicao
    template_name = "www/proposicao_list.html"
    paginate_by = 20

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
                "tramitacoes__pareceres",
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
        tipo = self.request.GET.get("tipo")
        numero = self.request.GET.get("numero")
        autor = self.request.GET.get("autor")
        comissao_filtro = self.request.GET.get("comissao")
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
                .exclude(tramitacoes__pareceres__tipo="RELATOR")
            )

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = self.request.GET.copy()
        params.pop("page", None)

        context["querystring"] = params.urlencode()

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
        # - NÃO existe parecer do tipo RELATOR nessa tramitação
        aguardando_parecer = (
            proposicoes
            .exclude(
                tramitacoes__pareceres__tipo="RELATOR"
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
            )
            .prefetch_related(
                "pareceres",
                "pareceres__relator",
                "pareceres__reuniao",
            )
            .order_by("data_entrada")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposicao"] = self.proposicao
        return context


# View ÚNICA Tramitacao - Parecer - Parecer vencido
class TramitacaoComParecerCreateView(View):
    template_name = "www/tramitacao_unica_form.html"

    ParecerVencidoFormSet = modelformset_factory(
        Parecer,
        form=ParecerVencidoForm,
        extra=1,
        can_delete=True
    )

    def get(self, request, proposicao_id):
        proposicao = get_object_or_404(Proposicao, pk=proposicao_id)

        context = {
            "proposicao": proposicao,
            "tramitacao_form": TramitacaoForm(),
            "parecer_relator_form": ParecerRelatorForm(),
            "vencidos_formset": self.ParecerVencidoFormSet(
                queryset=Parecer.objects.none(),
                prefix="vencido"
            ),
        }
        return render(request, self.template_name, context)

    def post(self, request, proposicao_id):
        proposicao = get_object_or_404(Proposicao, pk=proposicao_id)

        tramitacao_form = TramitacaoForm(request.POST)
        parecer_relator_form = ParecerRelatorForm(request.POST)
        vencidos_formset = ParecerVencidoFormSet(
            request.POST,
            queryset=Parecer.objects.none(),
            prefix="vencido"
        )

        forms_valid = (
            tramitacao_form.is_valid()
            and parecer_relator_form.is_valid()
            and vencidos_formset.is_valid()
        )

        if forms_valid:
            with transaction.atomic():
                tramitacao = tramitacao_form.save(commit=False)
                tramitacao.proposicao = proposicao
                tramitacao.save()

                parecer_relator = parecer_relator_form.save(commit=False)
                parecer_relator.tramitacao = tramitacao
                parecer_relator.save()

                for form in vencidos_formset:
                    if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                        parecer = form.save(commit=False)
                        parecer.tramitacao = tramitacao
                        parecer.save()

            return redirect("tramitacao_list", proposicao.pk)

        context = {
            "proposicao": proposicao,
            "tramitacao_form": tramitacao_form,
            "parecer_relator_form": parecer_relator_form,
            "vencidos_formset": vencidos_formset,
        }
        return render(request, self.template_name, context)



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
        initial["comissao"] = self.request.user.perfil.comissao_padrao
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


class TramitacaoPDFView(LoginRequiredMixin, View):
    """
    Gera o PDF do parecer da tramitação
    """

    def get(self, request, pk, *args, **kwargs):
        tramitacao = get_object_or_404(Tramitacao, pk=pk)

        html_string = render_to_string(
            "www/tramitacao_pdf.html",
            {"tramitacao": tramitacao}
        )

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="parecer_tramitacao_{pk}.pdf"'
        )

        return response


###################################################################################

class ReuniaoListView(ListView):
    model = Reuniao
    template_name = "www/reuniao_list.html"
    context_object_name = "reunioes"
    paginate_by = 20

    def get_queryset(self):
        return (
            Reuniao.objects
            .select_related("comissao")
            .order_by("-data", "-hora")
        )


class ReuniaoCreateView(CreateView):
    model = Reuniao
    form_class = ReuniaoForm
    template_name = "www/reuniao_form.html"
    success_url = reverse_lazy("reuniao_list")


class ReuniaoUpdateView(UpdateView):
    model = Reuniao
    form_class = ReuniaoForm
    template_name = "www/reuniao_form.html"
    success_url = reverse_lazy("reuniao_list")


class ReuniaoDetailView(DetailView):
    model = Reuniao
    template_name = "www/reuniao_detail.html"
    context_object_name = "reuniao"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["pareceres"] = (
            self.object.parecer_set
            .select_related("relator", "tramitacao__proposicao")
            .order_by("data_apresentacao")
        )

        return context



###################################################################################




