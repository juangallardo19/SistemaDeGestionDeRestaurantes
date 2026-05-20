from django import forms

from .models import Categoria, Ingrediente, Plato, PlatoIngrediente


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PlatoForm(forms.ModelForm):
    # Custom field: M2M through PlatoIngrediente cannot be auto-saved by ModelForm,
    # so we define it manually and handle persistence in save().
    ingredientes = forms.ModelMultipleChoiceField(
        queryset=Ingrediente.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Ingredientes',
    )

    class Meta:
        model = Plato
        fields = ['nombre', 'descripcion', 'precio', 'categoria', 'imagen', 'disponible', 'tiempo_preparacion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'tiempo_preparacion': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['ingredientes'].initial = self.instance.ingredientes.all()

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio

    def save(self, commit=True):
        plato = super().save(commit=commit)
        if commit:
            self._sync_ingredientes(plato)
        else:
            _orig = getattr(self, 'save_m2m', lambda: None)

            def _patched():
                _orig()
                self._sync_ingredientes(plato)

            self.save_m2m = _patched
        return plato

    def _sync_ingredientes(self, plato):
        nuevos = self.cleaned_data.get('ingredientes', [])
        ids_nuevos = {i.pk for i in nuevos}
        PlatoIngrediente.objects.filter(plato=plato).exclude(ingrediente_id__in=ids_nuevos).delete()
        existentes = set(
            PlatoIngrediente.objects.filter(plato=plato).values_list('ingrediente_id', flat=True)
        )
        for ingrediente in nuevos:
            if ingrediente.pk not in existentes:
                PlatoIngrediente.objects.create(
                    plato=plato,
                    ingrediente=ingrediente,
                    cantidad_necesaria=1,
                )


class IngredienteForm(forms.ModelForm):
    class Meta:
        model = Ingrediente
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo is not None and stock_minimo < 0:
            raise forms.ValidationError('El stock mínimo no puede ser negativo.')
        return stock_minimo
