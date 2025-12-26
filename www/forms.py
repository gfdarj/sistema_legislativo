from django.forms import forms
from django.core.exceptions import ValidationError
from models import ProjetoLei

class ProjetoLeiForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        numero = cleaned_data.get("numero_pl")

        if tipo and numero:
            if ProjetoLei.objects.filter(
                tipo=tipo,
                numero_pl=numero
            ).exclude(pk=self.instance.pk).exists():
                raise ValidationError(
                    "Já existe uma proposição com esse número para este tipo."
                )

        return cleaned_data


