import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import mesero_required
from accounts.email_utils import send_alerta_stock_bajo
from menu.models import Ingrediente

from .forms import MovimientoInventarioForm
from .models import MovimientoInventario

logger = logging.getLogger(__name__)


@mesero_required
def lista_inventario(request):
    ingredientes = Ingrediente.objects.all()
    return render(request, 'inventory/lista_inventario.html', {'ingredientes': ingredientes})


@mesero_required
def registrar_movimiento(request):
    form = MovimientoInventarioForm(request.POST or None)
    if form.is_valid():
        ingrediente = form.cleaned_data['ingrediente']
        tipo = form.cleaned_data['tipo']
        cantidad = form.cleaned_data['cantidad']

        # Actualizar stock según el tipo de movimiento
        if tipo == 'entrada':
            ingrediente.stock_actual += cantidad
        elif tipo == 'salida':
            # La validación de stock suficiente ya se hizo en el formulario
            ingrediente.stock_actual = max(Decimal('0'), ingrediente.stock_actual - cantidad)
        elif tipo == 'ajuste':
            ingrediente.stock_actual = cantidad

        ingrediente.save(update_fields=['stock_actual'])

        movimiento = form.save(commit=False)
        movimiento.responsable = request.user
        movimiento.stock_resultante = ingrediente.stock_actual
        movimiento.save()

        messages.success(
            request,
            f'Movimiento registrado. Stock de "{ingrediente.nombre}" actualizado a '
            f'{ingrediente.stock_actual} {ingrediente.unidad_medida}.',
        )

        if ingrediente.stock_bajo:
            send_alerta_stock_bajo(ingrediente)
            messages.warning(
                request,
                f'¡Atención! El stock de "{ingrediente.nombre}" está por debajo del mínimo '
                f'({ingrediente.stock_minimo} {ingrediente.unidad_medida}). '
                'Se envió una alerta al administrador.',
            )

        return redirect('inventory:list')

    return render(request, 'inventory/registrar_movimiento.html', {'form': form})


@mesero_required
def historial_movimientos(request):
    movimientos = MovimientoInventario.objects.select_related('ingrediente', 'responsable').all()
    ingredientes = Ingrediente.objects.filter(activo=True)

    ingrediente_id = request.GET.get('ingrediente', '')
    tipo_filtro = request.GET.get('tipo', '')
    fecha_filtro = request.GET.get('fecha', '')

    if ingrediente_id:
        movimientos = movimientos.filter(ingrediente_id=ingrediente_id)
    if tipo_filtro:
        movimientos = movimientos.filter(tipo=tipo_filtro)
    if fecha_filtro:
        try:
            fecha = date.fromisoformat(fecha_filtro)
            movimientos = movimientos.filter(fecha__date=fecha)
        except ValueError:
            pass

    return render(request, 'inventory/historial_movimientos.html', {
        'movimientos': movimientos,
        'ingredientes': ingredientes,
        'ingrediente_id': ingrediente_id,
        'tipo_filtro': tipo_filtro,
        'fecha_filtro': fecha_filtro,
        'tipo_choices': MovimientoInventario.TIPO_CHOICES,
    })


@mesero_required
def detalle_ingrediente(request, pk):
    ingrediente = get_object_or_404(Ingrediente, pk=pk)
    movimientos = MovimientoInventario.objects.filter(
        ingrediente=ingrediente,
    ).select_related('responsable').order_by('-fecha')

    return render(request, 'inventory/detalle_ingrediente.html', {
        'ingrediente': ingrediente,
        'movimientos': movimientos,
    })
