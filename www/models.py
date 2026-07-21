from pickle import TRUE

from django.db import models
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
#-- cria o perfil do usuário
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from minhas_libs import math_utils
from minhas_libs.math_utils import obter_ordinal

User = get_user_model()

@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)
#--

#########################################################################################

class TipoProposicao(models.Model):
    sigla = models.CharField(
        max_length=10,
        unique=True,
        help_text="Código curto do tipo de proposição (até 10 caracteres)"
    )
    nome = models.CharField(
        max_length=100,
        unique=True
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Proposição"
        verbose_name_plural = "Tipos de Proposição"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}"


#########################################################################################

class Autor(models.Model):
    nome = models.CharField(max_length=150)
    sexo = models.CharField(
        max_length=1,
        choices=[
            ("M", "Masculino"),
            ("F", "Feminino"),
        ]
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autores"
        ordering = ["nome"]

    def __str__(self):
        status = "" if self.ativo else " (inativo)"
        return f"{self.nome}{status}"


#########################################################################################

class Comissao(models.Model):
    sigla = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=255)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


#########################################################################################

class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil"
    )

    comissao_padrao = models.ForeignKey(
        Comissao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Perfil do Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self):
        return self.user.get_username()


#########################################################################################

class Proposicao(models.Model):
    tipo = models.ForeignKey(
        TipoProposicao,
        on_delete=models.PROTECT,
        related_name="proposicoes"
    )
    numero = models.CharField(max_length=11, primary_key=True)
    numero_formatado = models.CharField(max_length=20)
    ementa = models.TextField()
    data_publicacao = models.DateField()
    autores = models.ManyToManyField(Autor, related_name="proposicoes_autoria")
    link_proposicao = models.CharField(max_length=400, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "numero_formatado"],
                name="unique_numero_formatado_por_tipo"
            )
        ]

    def __str__(self):
        return f"{self.tipo} {self.numero_formatado}"

    # =========================
    # 🔹 ESTADO DERIVADO
    # =========================

    @property
    def comissao_atual(self):
        ultima = self.tramitacoes.order_by("-data_entrada").first()
        return ultima.comissao if ultima else None

    @property
    def relator_atual(self):
        ultima = self.tramitacoes.order_by("-data_entrada").first()
        return ultima.relator_atual if ultima else None


#########################################################################################
class Reuniao(models.Model):

    TIPO_CHOICES = [
        ("ORDINÁRIA", "Ordinária"),
        ("EXTRAORDINÁRIA", "Extraordinária"),
    ]

    comissao = models.ForeignKey(
        Comissao,
        on_delete=models.PROTECT,
        related_name="reunioes"
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    numero = models.PositiveIntegerField(verbose_name="Ordem")

    data = models.DateField()
    hora = models.TimeField()

    pauta = models.TextField(blank=True)
    ata = models.TextField(blank=True)

    # 🔹 Controle de edital
    data_edital_do = models.DateField(null=True, blank=True, verbose_name="Data do Edital")
    tem_edital_assinado = models.BooleanField(null=True, blank=True, verbose_name="Edital Assinado")

    # 🔹 Controle de presença e ata
    tem_presenca_assinada = models.BooleanField(null=True, blank=True, verbose_name="Presença Assinada")
    tem_ata_assinada = models.BooleanField(null=True, blank=True, verbose_name="Ata Assinada")
    data_ata_do = models.DateField(null=True, blank=True, verbose_name="Data da Ata")

    # 🔹 Controle de parecer
    tem_parecer_assinado = models.BooleanField(null=True, blank=True, verbose_name="Parecer Assinado")

    # 🔹 Controle de deliberação
    tem_deliberacao = models.BooleanField(null=True, blank=True, verbose_name="Tem Deliberação")
    tem_deliberacao_assinada = models.BooleanField(null=True, blank=True, verbose_name="Deliberação Assinada")

    # 🔹 Controle de conclusão
    tem_conclusao = models.BooleanField(null=True, blank=True, verbose_name="Tem Conclusão")
    tem_conclusao_assinada = models.BooleanField(null=True, blank=True, verbose_name="Conclusão Assinada")

    @property
    def ano(self):
        """Ano da reunião, derivado da própria data."""
        return self.data.year if self.data else None

    @property
    def descricao(self):
        return (
            f"{obter_ordinal(self.numero, feminino=True)} "
            f"reunião {self.tipo} de {self.ano}"
        )

    @property
    def descricao_combo(self):
        """Formato usado nas combos: 1ª Reunião EXTRAORDINÁRIA (SIGLA dd/mm/aaaa)."""
        return (
            f"{obter_ordinal(self.numero, feminino=True)} Reunião {self.tipo} "
            f"({self.comissao.sigla} {self.data.strftime('%d/%m/%Y')})"
        )

    def __str__(self):
        return self.descricao

#########################################################################################

class Tramitacao(models.Model):
    proposicao = models.ForeignKey(Proposicao, on_delete=models.CASCADE, related_name="tramitacoes")
    comissao = models.ForeignKey(Comissao, on_delete=models.PROTECT)
    data_entrada = models.DateField()
    data_saida = models.DateField(null=True, blank=True)
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    # =========================
    # 🔹 PARECER DO RELATOR (1-para-1 com a tramitação)
    # =========================
    reuniao = models.ForeignKey(
        Reuniao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tramitacoes"
    )
    relator = models.ForeignKey(
        Autor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tramitacoes_como_relator"
    )
    parecer = models.CharField(max_length=200, blank=True)
    texto = CKEditor5Field(blank=True)

    # 🔹 Indica que a proposição terá parecer(es) em separado (vencido),
    # pois algum membro pediu vista do processo.
    pedido_vista = models.BooleanField(
        default=False,
        verbose_name="Pedido de Vista"
    )

    # =========================
    # 🔹 AUDITORIA
    # =========================
    usuario_inclusao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tramitacoes_incluidas",
        verbose_name="Usuário de Inclusão",
        editable=False,
    )
    usuario_alteracao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tramitacoes_alteradas",
        verbose_name="Usuário da Última Alteração",
        editable=False,
    )
    alterada_em = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["data_entrada"]

    def __str__(self):
        return (
            f"{self.proposicao} - {self.comissao} "
            f"({self.data_entrada})"
        )

    @property
    def relator_atual(self):
        return self.relator

    @property
    def tem_parecer_relator(self):
        return self.relator_id is not None

    def save(self, *args, **kwargs):
        if self.parecer:
            self.parecer = self.parecer.upper()

        super().save(*args, **kwargs)


#########################################################################################

class ParecerVencido(models.Model):
    tramitacao = models.ForeignKey(
        Tramitacao,
        on_delete=models.CASCADE,
        related_name="pareceres_vencidos"
    )
    reuniao = models.ForeignKey(
        Reuniao,
        on_delete=models.PROTECT
    )
    relator = models.ForeignKey(Autor, on_delete=models.PROTECT)
    parecer = models.CharField(max_length=200)
    texto = CKEditor5Field()
    data_apresentacao = models.DateField()

    class Meta:
        verbose_name = "Parecer Vencido"
        verbose_name_plural = "Pareceres Vencidos"
        ordering = ["data_apresentacao"]

    def __str__(self):
        return f"Voto vencido de {self.relator} em {self.tramitacao}"

    def save(self, *args, **kwargs):
        if self.parecer:
            self.parecer = self.parecer.upper()
        super().save(*args, **kwargs)


#########################################################################################

