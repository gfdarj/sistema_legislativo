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
    class Meta:
        model = Tramitacao
        fields = [
            "comissao",
            "relator",
            "data_evento",
            "descricao",
            "observacao",
        ]
        widgets = {
            "comissao": forms.Select(
                attrs={
                    "class": "form-select",
                    "readonly": "readonly"
                    # "disabled": "disabled"  # 👈 desabilita visualmente
                }
            ),
            "relator": forms.Select(attrs={"class": "form-select"}),
            "data_evento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "descricao": forms.TextInput(attrs={"class": "form-control"}),
            "observacao": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        # 🔑 remove o argumento extra ANTES do super()
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # ✔ SOMENTE NA CRIAÇÃO
        if not self.instance.pk:
            self.fields["data_evento"].initial = localdate()



