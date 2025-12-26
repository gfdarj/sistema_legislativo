from django.db import models
from django.conf import settings

#-- cria o perfil do usuário
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)
#--



class TipoProposicao(models.Model):
    chave = models.CharField(
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

class Comissao(models.Model):
    sigla = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=255)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Proposicao(models.Model):
    tipo = models.ForeignKey(
        TipoProposicao,
        on_delete=models.PROTECT,
        related_name="proposicoes"
    )
    numero = models.CharField(max_length=20)
    ementa = models.TextField()

    autores = models.ManyToManyField(Autor, related_name="proposicoes_autoria")

    relator = models.ForeignKey(
        Autor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relatorias"
    )

    comissao_atual = models.ForeignKey(
        Comissao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "numero"],
                name="unique_numero_por_tipo"
            )
        ]

    def __str__(self):
        return f"{self.tipo} {self.numero}"


class Parecer(models.Model):
    projeto = models.ForeignKey(
        Proposicao,
        on_delete=models.CASCADE,
        related_name="pareceres"
    )

    relator = models.ForeignKey(
        Autor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    comissao = models.ForeignKey(
        Comissao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    tipo = models.CharField(max_length=30)
    texto = models.TextField()
    data_parecer = models.DateField()


class Tramitacao(models.Model):
    projeto = models.ForeignKey(
        Proposicao,
        on_delete=models.CASCADE,
        related_name="tramitacoes"
    )

    comissao = models.ForeignKey(
        Comissao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    data_evento = models.DateField()
    descricao = models.CharField(max_length=255)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["data_evento"]

    def __str__(self):
        return f"{self.projeto} - {self.data_evento}"




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

