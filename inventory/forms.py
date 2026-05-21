from django import forms

from menu.models import Ingrediente, PlatoIngrediente

from .models import MovimientoInventario


class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = ['nombre', 'unidad_medida', 'stock_actual', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Harina de trigo',
            }),
            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: kg, litros, unidades',
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
        }


class PlatoIngredienteForm(forms.ModelForm):
    class Meta:
        model = PlatoIngrediente
        fields = ['ingrediente', 'cantidad_necesaria']
        widgets = {
            'ingrediente':       forms.Select(attrs={'class': 'form-select'}),
            'cantidad_necesaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Ej: 0.25',
            }),
        }

    def __init__(self, *args, plato=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.plato = plato
        if plato:
            usados = plato.plato_ingredientes.values_list('ingrediente_id', flat=True)
            qs = Ingrediente.objects.filter(activo=True).exclude(pk__in=usados)
            self.fields['ingrediente'].queryset = qs
        else:
            self.fields['ingrediente'].queryset = Ingrediente.objects.filter(activo=True)


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
