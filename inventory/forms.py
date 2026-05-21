from django import forms

from .models import MovimientoInventario


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['ingrediente', 'tipo', 'cantidad', 'motivo']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del movimiento...',
            }),
        }
        help_texts = {
            'cantidad': (
                '<strong>Entrada / Salida:</strong> cantidad a sumar o restar al stock actual. '
                '<strong>Ajuste:</strong> nuevo valor absoluto del stock (corrección por conteo físico).'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from menu.models import Ingrediente
        self.fields['ingrediente'].queryset = Ingrediente.objects.filter(activo=True)
        self.fields['ingrediente'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        ingrediente = cleaned_data.get('ingrediente')

        if tipo == 'salida' and ingrediente and cantidad is not None:
            if ingrediente.stock_actual < cantidad:
                raise forms.ValidationError(
                    f'Stock insuficiente para "{ingrediente.nombre}". '
                    f'Stock actual: {ingrediente.stock_actual} {ingrediente.unidad_medida}, '
                    f'cantidad solicitada: {cantidad} {ingrediente.unidad_medida}.'
                )
        return cleaned_data
