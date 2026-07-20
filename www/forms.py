from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget
from www.models import Proposicao, Tramitacao, Autor, Reuniao, ParecerVencido


class NullBooleanSelectNA(forms.NullBooleanSelect):
    """Combo Sim/Não/N-A (em vez do 'Unknown' padrão do Django)."""

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.choices = (
            ("unknown", "N/A"),
            ("true", "Sim"),
            ("false", "Não"),
        )


class TesteCKForm(forms.Form):
    texto = forms.CharField(widget=CKEditor5Widget())



class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ["nome", "sexo", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "sexo": forms.Select(attrs={"class": "form-select"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ReuniaoSelect(forms.Select):
    """Select de Reunião com data-comissao em cada opção (para filtragem via JS)."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-comissao"] = str(instance.comissao_id)
        return option


class ReuniaoChoiceField(forms.ModelChoiceField):
    """Combo de Reunião no formato: 1ª Reunião EXTRAORDINÁRIA (SIGLA dd/mm/aaaa)."""

    def label_from_instance(self, obj):
        return obj.descricao_combo


class TramitacaoForm(forms.ModelForm):
    reuniao = ReuniaoChoiceField(
        queryset=Reuniao.objects.select_related("comissao"),
        widget=ReuniaoSelect(attrs={"class": "form-select"}),
        required=False,
    )

    class Meta:
        model = Tramitacao
        fields = [
            "comissao",
            "data_entrada",
            "data_saida",
            "observacao",
            "reuniao",
            "relator",
            "parecer",
            "texto",
            "pedido_vista",
        ]
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
            "relator": forms.Select(attrs={"class": "form-select"}),
            "parecer": forms.TextInput(attrs={"class": "form-control"}),
            "texto": CKEditor5Widget(config_name="default"),
            "pedido_vista": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, "perfil") and user.perfil.comissao_padrao:
            self.fields["comissao"].initial = user.perfil.comissao_padrao

    def clean(self):
        cleaned_data = super().clean()
        comissao = cleaned_data.get("comissao")
        reuniao = cleaned_data.get("reuniao")

        # 🔒 A reunião escolhida deve pertencer à comissão selecionada
        if comissao and reuniao and reuniao.comissao_id != comissao.id:
            self.add_error(
                "reuniao",
                "A reunião selecionada não pertence à comissão escolhida."
            )

        return cleaned_data


class ParecerVencidoForm(forms.ModelForm):
    reuniao = ReuniaoChoiceField(
        queryset=Reuniao.objects.select_related("comissao"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ParecerVencido
        fields = [
            "reuniao",
            "relator",
            "parecer",
            "texto",
            "data_apresentacao",
        ]
        widgets = {
            "relator": forms.Select(attrs={"class": "form-select"}),
            "parecer": forms.TextInput(attrs={"class": "form-control"}),
            "texto": CKEditor5Widget(config_name="default"),
            "data_apresentacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }



class ReuniaoForm(forms.ModelForm):
    class Meta:
        model = Reuniao
        fields = [
            "comissao",
            "tipo",
            "numero",
            "data",
            "hora",
            "pauta",
            "ata",
            "data_edital_do",
            "tem_edital_assinado",
            "tem_presenca_assinada",
            "tem_ata_assinada",
            "data_ata_do",
            "tem_parecer_assinado",
            "tem_deliberacao",
            "tem_deliberacao_assinada",
            "tem_conclusao",
            "tem_conclusao_assinada",
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
            "data_edital_do": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_ata_do": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "tem_edital_assinado": NullBooleanSelectNA(),
            "tem_presenca_assinada": NullBooleanSelectNA(),
            "tem_ata_assinada": NullBooleanSelectNA(),
            "tem_parecer_assinado": NullBooleanSelectNA(),
            "tem_deliberacao": NullBooleanSelectNA(),
            "tem_deliberacao_assinada": NullBooleanSelectNA(),
            "tem_conclusao": NullBooleanSelectNA(),
            "tem_conclusao_assinada": NullBooleanSelectNA(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            # evita sobrescrever widgets já configurados
            if "class" in widget.attrs:
                continue

            if "Select" in widget.__class__.__name__:
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super().clean()
        comissao = cleaned_data.get("comissao")
        numero = cleaned_data.get("numero")
        data = cleaned_data.get("data")

        # 🔒 A ordem não pode se repetir dentro da mesma comissão no mesmo ano
        if comissao and numero and data:
            qs = Reuniao.objects.filter(
                comissao=comissao,
                numero=numero,
                data__year=data.year,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    "numero",
                    f"Já existe uma reunião com essa ordem em {data.year} "
                    f"para essa comissão."
                )

        return cleaned_data





