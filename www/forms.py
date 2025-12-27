from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import localdate
from www.models import Proposicao, Tramitacao, Autor


class ProposicaoForm(forms.ModelForm):

    class Meta:
        model = Proposicao
        fields = "__all__"
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "comissao_atual": forms.Select(attrs={"class": "form-select"}),
            "autores": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "relator": forms.Select(attrs={"class": "form-select"}),
            "ementa": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["autores"].queryset = Autor.objects.filter(ativo=True)

        # SOMENTE NO CREATE
        if not self.instance.pk and user:
            try:
                self.fields["comissao_atual"].initial = (
                    user.perfil.comissao_padrao
                )
            except:
                pass


    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        numero = cleaned_data.get("numero_pl")

        if tipo and numero:
            if Proposicao.objects.filter(
                tipo=tipo,
                numero_pl=numero
            ).exclude(pk=self.instance.pk).exists():
                raise ValidationError(
                    "Já existe uma proposição com esse número para este tipo."
                )

        return cleaned_data



class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ["nome", "sexo", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "sexo": forms.Select(attrs={"class": "form-select"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TramitacaoForm(forms.ModelForm):
    existe_parecer_vencido = forms.BooleanField(
        required=False,
        label="Existe parecer vencido?"
    )

    class Meta:
        model = Tramitacao
        fields = [
            "comissao",
            "relator",
            "data_evento",
            "descricao",
            "observacao",

            "parecer",
            "texto_parecer",
            "data_parecer",

            "parecer_vencido",
            "texto_parecer_vencido",
            "data_parecer_vencido",

            "data_publicacao_parecer",
        ]

        widgets = {
            "comissao": forms.Select(attrs={"class": "form-select"}),
            "relator": forms.Select(attrs={"class": "form-select"}),
            "data_evento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "descricao": forms.TextInput(attrs={"class": "form-control"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "parecer": forms.TextInput(attrs={"class": "form-control"}),
            "data_parecer": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "parecer_vencido": forms.TextInput(attrs={"class": "form-control"}),
            "data_parecer_vencido": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "data_publicacao_parecer": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Se já existe parecer vencido, marca o checkbox
        if (
            self.instance.parecer_vencido
            or self.instance.texto_parecer_vencido
            or self.instance.data_parecer_vencido
        ):
            self.fields["existe_parecer_vencido"].initial = True

        if not self.instance.pk:
            self.fields["data_evento"].initial = localdate()


    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("existe_parecer_vencido"):
            cleaned_data["parecer_vencido"] = None
            cleaned_data["texto_parecer_vencido"] = ""
            cleaned_data["data_parecer_vencido"] = None

        return cleaned_data



