"""
Relatórios do sistema legislativo.

Cada relatório possui uma tela (com filtros) e uma versão em PDF.
A geração de PDF é centralizada no RelatorioPDFMixin.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import F, Max, OuterRef, Q, Subquery
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.views.generic import TemplateView, View
from weasyprint import HTML

from www.models import Comissao, Proposicao, Reuniao, Tramitacao


# =========================================================================
# 🔹 Infraestrutura comum
# =========================================================================

class RelatorioPDFMixin:
    """Gera a resposta PDF a partir de um template e um contexto."""

    def renderizar_pdf(self, template_name, context, filename):
        context.setdefault("gerado_em", now())
        context.setdefault("gerado_por", self.request.user)

        html_string = render_to_string(template_name, context)
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


def _comissao_do_filtro(request):
    """
    Resolve a comissão a partir do GET.
    Ausente -> comissão do usuário; vazio explícito -> None (todas).
    """
    comissao_id = request.GET.get("comissao")
    if comissao_id:
        return Comissao.objects.filter(pk=comissao_id).first()
    if comissao_id is None:
        perfil = getattr(request.user, "perfil", None)
        if perfil and perfil.comissao_padrao_id:
            return perfil.comissao_padrao
    return None


def _ultimas_tramitacoes_da_comissao(comissao):
    """
    Tramitações que são a ÚLTIMA da sua proposição e pertencem à comissão.
    """
    ultima_data = (
        Tramitacao.objects
        .filter(proposicao=OuterRef("proposicao"))
        .values("proposicao")
        .annotate(m=Max("data_entrada"))
        .values("m")[:1]
    )
    return (
        Tramitacao.objects
        .filter(comissao=comissao)
        .annotate(max_data=Subquery(ultima_data))
        .filter(data_entrada=F("max_data"))
        .select_related("proposicao", "proposicao__tipo", "relator", "reuniao")
        .order_by("data_entrada")
    )


# =========================================================================
# 1️⃣ Situação da Comissão
# =========================================================================

class RelatorioSituacaoComissaoView(LoginRequiredMixin, TemplateView):
    template_name = "www/relatorios/situacao_comissao.html"

    def montar_dados(self):
        comissao = _comissao_do_filtro(self.request)

        com_relator, aguardando = [], []
        if comissao:
            hoje = now().date()
            for t in _ultimas_tramitacoes_da_comissao(comissao):
                item = {
                    "proposicao": t.proposicao,
                    "tramitacao": t,
                    "dias": (hoje - t.data_entrada).days,
                }
                (com_relator if t.relator_id else aguardando).append(item)

        return {
            "comissao": comissao,
            "comissoes": Comissao.objects.filter(ativa=True),
            "com_relator": com_relator,
            "aguardando": aguardando,
            "total": len(com_relator) + len(aguardando),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.montar_dados())
        return context


class RelatorioSituacaoComissaoPDFView(RelatorioPDFMixin,
                                       RelatorioSituacaoComissaoView):
    def get(self, request, *args, **kwargs):
        dados = self.montar_dados()
        if not dados["comissao"]:
            raise Http404("Selecione uma comissão para gerar o PDF.")
        return self.renderizar_pdf(
            "www/relatorios/situacao_comissao_pdf.html",
            dados,
            f"situacao_{dados['comissao'].sigla}.pdf",
        )


# =========================================================================
# 6️⃣ Pendências documentais das Reuniões
# =========================================================================

# (campo, rótulo) — usados para montar a lista de pendências de cada reunião
CAMPOS_DOCUMENTAIS = [
    ("tem_edital_assinado", "Edital assinado"),
    ("tem_presenca_assinada", "Presença assinada"),
    ("tem_ata_assinada", "Ata assinada"),
    ("tem_parecer_assinado", "Parecer assinado"),
    ("tem_deliberacao_assinada", "Deliberação assinada"),
    ("tem_conclusao_assinada", "Conclusão assinada"),
]


class RelatorioPendenciasReunioesView(LoginRequiredMixin, TemplateView):
    template_name = "www/relatorios/pendencias_reunioes.html"

    def montar_dados(self):
        comissao = _comissao_do_filtro(self.request)
        ano = self.request.GET.get("ano") or now().year
        somente_pendentes = self.request.GET.get("todas") != "1"

        reunioes = (
            Reuniao.objects
            .filter(data__year=ano)
            .select_related("comissao")
            .order_by("comissao__sigla", "data")
        )
        if comissao:
            reunioes = reunioes.filter(comissao=comissao)

        linhas = []
        for reuniao in reunioes:
            pendencias = [
                rotulo
                for campo, rotulo in CAMPOS_DOCUMENTAIS
                if getattr(reuniao, campo) is not True
            ]
            if pendencias or not somente_pendentes:
                linhas.append({"reuniao": reuniao, "pendencias": pendencias})

        anos = Reuniao.objects.dates("data", "year", order="DESC")

        return {
            "comissao": comissao,
            "comissoes": Comissao.objects.filter(ativa=True),
            "ano": int(ano),
            "anos": anos,
            "somente_pendentes": somente_pendentes,
            "linhas": linhas,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.montar_dados())
        return context


class RelatorioPendenciasReunioesPDFView(RelatorioPDFMixin,
                                         RelatorioPendenciasReunioesView):
    def get(self, request, *args, **kwargs):
        dados = self.montar_dados()
        sufixo = dados["comissao"].sigla if dados["comissao"] else "todas"
        return self.renderizar_pdf(
            "www/relatorios/pendencias_reunioes_pdf.html",
            dados,
            f"pendencias_reunioes_{sufixo}_{dados['ano']}.pdf",
        )


# =========================================================================
# 3️⃣ Dossiê da Proposição
# =========================================================================

class RelatorioDossieView(LoginRequiredMixin, TemplateView):
    """Tela de busca da proposição para geração do dossiê."""

    template_name = "www/relatorios/dossie.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        busca = self.request.GET.get("busca", "").strip()
        context["busca"] = busca

        if busca:
            context["resultados"] = (
                Proposicao.objects
                .filter(
                    Q(numero__icontains=busca) |
                    Q(numero_formatado__icontains=busca) |
                    Q(ementa__icontains=busca)
                )
                .select_related("tipo")[:20]
            )
        return context


class RelatorioDossiePDFView(LoginRequiredMixin, RelatorioPDFMixin, View):
    def get(self, request, pk, *args, **kwargs):
        proposicao = get_object_or_404(
            Proposicao.objects
            .select_related("tipo")
            .prefetch_related(
                "autores",
                "tramitacoes__comissao",
                "tramitacoes__relator",
                "tramitacoes__reuniao",
                "tramitacoes__pareceres_vencidos__relator",
                "tramitacoes__pareceres_vencidos__reuniao",
            ),
            pk=pk,
        )
        return self.renderizar_pdf(
            "www/relatorios/dossie_pdf.html",
            {"proposicao": proposicao},
            f"dossie_{proposicao.pk}.pdf",
        )
