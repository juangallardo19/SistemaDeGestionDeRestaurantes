from django import forms

from accounts.models import CustomUser

from .models import Pedido


class AgregarAlCarritoForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        label='Cantidad',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '20',
        }),
    )
    # Cuando es True, reemplaza la cantidad en lugar de incrementarla.
    actualizar = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput,
    )


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['notas', 'metodo_pago']
        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Instrucciones especiales, alergias, preferencias...',
            }),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
        }


class CambiarEstadoPedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


class AsignarMeseroForm(forms.ModelForm):
    mesero = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='mesero'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label='Sin asignar',
        label='Mesero',
    )

    class Meta:
        model = Pedido
        fields = ['mesero']


class FiltroPedidoForm(forms.Form):
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
        choices=[('', '— Todos —')] + Pedido.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    mesero = forms.ModelChoiceField(
        required=False,
        label='Mesero',
        queryset=CustomUser.objects.filter(role='mesero'),
        empty_label='— Todos —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cliente = forms.CharField(
        required=False,
        label='Cliente',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre o email...',
        }),
    )
    metodo_pago = forms.ChoiceField(
        required=False,
        label='Método de pago',
        choices=[('', '— Todos —')] + Pedido.METODO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
