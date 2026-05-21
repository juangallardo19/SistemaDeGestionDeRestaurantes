from datetime import date

from django import forms

from .models import Mesa, Reserva


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['mesa', 'fecha', 'hora_inicio', 'hora_fin', 'numero_personas', 'notas']
        widgets = {
            'mesa': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'numero_personas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Motivo de la visita, peticiones especiales...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mesa'].queryset = Mesa.objects.filter(activa=True)

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        mesa = cleaned_data.get('mesa')
        fecha = cleaned_data.get('fecha')
        numero_personas = cleaned_data.get('numero_personas')

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error('hora_fin', 'La hora de fin debe ser posterior a la hora de inicio.')

        if fecha and fecha < date.today():
            self.add_error('fecha', 'No podés hacer una reserva para una fecha pasada.')

        if mesa and numero_personas and numero_personas > mesa.capacidad:
            self.add_error(
                'numero_personas',
                f'La mesa {mesa.numero} tiene capacidad máxima para {mesa.capacidad} persona(s).',
            )

        # Verificar conflicto de horario (solo si todos los campos son válidos)
        if mesa and fecha and hora_inicio and hora_fin and hora_fin > hora_inicio:
            conflictos = Reserva.objects.filter(
                mesa=mesa,
                fecha=fecha,
                estado__in=['pendiente', 'confirmada'],
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            )
            if self.instance.pk:
                conflictos = conflictos.exclude(pk=self.instance.pk)
            if conflictos.exists():
                raise forms.ValidationError(
                    f'La mesa {mesa.numero} ya tiene una reserva en ese horario el {fecha}. '
                    'Elegí otro horario o mesa disponible.'
                )

        return cleaned_data


class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ['numero', 'capacidad', 'ubicacion', 'activa']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'ubicacion': forms.Select(attrs={'class': 'form-select'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FiltroReservaForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        label='Fecha desde',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    fecha_hasta = forms.DateField(
        required=False,
        label='Fecha hasta',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    estado = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[('', '— Todos —')] + Reserva.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
