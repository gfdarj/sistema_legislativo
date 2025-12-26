from django.contrib import admin
from www.models import TipoProposicao, Autor, Comissao, Proposicao, Parecer, Tramitacao, PerfilUsuario

admin.site.register(Autor)
admin.site.register(Proposicao)
admin.site.register(Parecer)
admin.site.register(Tramitacao)

# Register your models here.

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "comissao_padrao")


@admin.register(TipoProposicao)
class TipoProposicaoAdmin(admin.ModelAdmin):
    list_display = ("chave", "nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("chave", "nome")
    ordering = ("nome",)


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = ("sigla", "nome", "ativa")
    list_filter = ("ativa",)
    search_fields = ("sigla", "nome")
    ordering = ("nome",)

