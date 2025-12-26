from django.db import models

# Create your models here.

class Autor(models.Model):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]
    chave = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=255)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

    def __str__(self):
        return self.nome


class Comissao(models.Model):
    sigla = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=255)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.sigla


class ProjetoLei(models.Model):
    tipo = models.CharField(max_length=10)
    numero_pl = models.CharField(max_length=30, unique=True)
    ementa = models.TextField()

    autores = models.ManyToManyField(Autor, related_name="projetos_autoria")
    relator = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, blank=True, related_name="relatorias")

    comissao_atual = models.ForeignKey(Comissao, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.tipo} {self.numero_pl}"


class Parecer(models.Model):
    projeto = models.ForeignKey(ProjetoLei, on_delete=models.CASCADE, related_name="pareceres")
    relator = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, blank=True)
    comissao = models.ForeignKey(Comissao, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=30)
    texto = models.TextField()
    data_parecer = models.DateField()


class Tramitacao(models.Model):
    projeto = models.ForeignKey(ProjetoLei, on_delete=models.CASCADE, related_name="tramitacoes")
    comissao = models.ForeignKey(Comissao, on_delete=models.SET_NULL, null=True, blank=True)
    data_evento = models.DateField()
    descricao = models.CharField(max_length=255)
    observacao = models.TextField(blank=True, null=True)