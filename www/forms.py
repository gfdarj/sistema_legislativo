from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget
from www.models import Proposicao, Tramitacao, Autor, Reuniao, Parecer


class TesteCKForm(forms.Form):
    texto = forms.CharField(widget=CKEditor5Widget())



class ProposicaoForm(forms.ModelForm):

    class Meta:
        model = Proposicao
        fields = "__all__"
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "numero_formatado": forms.TextInput(attrs={"class": "form-control"}),
            "comissao_atual": forms.Select(attrs={"class": "form-select"}),
            "autores": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "relator": forms.Select(attrs={"class": "form-select"}),
            "ementa": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "link_proposicao": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
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
        numero_formatado = cleaned_data.get("numero_pl")

        if tipo and numero_formatado:
            if Proposicao.objects.filter(
                tipo=tipo,
                numero_pl=numero_formatado
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
        fields = ["comissao", "data_entrada", "data_saida", "observacao"]
        widgets = {
            "comissao": forms.Select(attrs={"class": "form-select"}),
            "data_entrada": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_saida": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "observacao": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
        }


class ParecerRelatorForm(forms.ModelForm):
    class Meta:
        model = Parecer
        fields = [
            "reuniao",
            "relator",
            "parecer",
            "texto",
            "data_apresentacao",
        ]
        widgets = {
            "reuniao": forms.Select(attrs={"class": "form-select"}),
            "relator": forms.Select(attrs={"class": "form-select"}),
            "parecer": forms.TextInput(attrs={"class": "form-control"}),

            # 🔥 AQUI ESTÁ A CORREÇÃO
            "texto": CKEditor5Widget(config_name="default"),

            "data_apresentacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.tipo = "RELATOR"
        if commit:
            obj.save()
        return obj


class ParecerVencidoForm(forms.ModelForm):
    class Meta:
        model = Parecer
        fields = [
            "reuniao",
            "relator",
            "parecer",
            "texto",
            "data_apresentacao",
        ]
        widgets = {
            "reuniao": forms.Select(attrs={"class": "form-select"}),
            "relator": forms.Select(attrs={"class": "form-select"}),
            "parecer": forms.TextInput(attrs={"class": "form-control"}),
            "texto": CKEditor5Widget(config_name="default"),
            "data_apresentacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.tipo = "VENCIDO"
        if commit:
            obj.save()
        return obj



class ReuniaoForm(forms.ModelForm):

    class Meta:
        model = Reuniao
        fields = [
            "comissao",
            "tipo",
            "numero",
            "ano",
            "data",
            "hora",
            "pauta",
            "ata",
        ]

        widgets = {
            "data": forms.DateInput(
                attrs={"type": "date"}
            ),
            "hora": forms.TimeInput(
                attrs={"type": "time"}
            ),
            "pauta": forms.Textarea(
                attrs={"rows": 2}
            ),
            "ata": forms.Textarea(
                attrs={"rows": 2}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        comissao = cleaned_data.get("comissao")
        numero = cleaned_data.get("numero")
        ano = cleaned_data.get("ano")

        if comissao and numero and ano:
            qs = Reuniao.objects.filter(
                comissao=comissao,
                numero=numero,
                ano=ano
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Já existe uma reunião com esse número e ano para essa comissão."
                )

        return cleaned_data




class ReuniaoForm(forms.ModelForm):
    class Meta:
        model = Reuniao
        fields = [
            "comissao",
            "tipo",
            "numero",
            "ano",
            "data",
            "hora",
            "pauta",
            "ata",
        ]
        widgets = {
            "data": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "hora": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "pauta": forms.Textarea(
                attrs={"rows": 2, "class": "form-control"}
            ),
            "ata": forms.Textarea(
                attrs={"rows": 2, "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            # evita sobrescrever widgets já configurados
            if "class" in widget.attrs:
                continue

            if widget.__class__.__name__ == "Select":
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super().clean()
        data = cleaned_data.get("data")
        ano = cleaned_data.get("ano")

        if data and ano and data.year != ano:
            self.add_error(
                "ano",
                "O ano deve ser o mesmo da data da reunião."
            )

        return cleaned_data





