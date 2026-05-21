import logging
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required, mesero_required
from accounts.email_utils import send_alerta_stock_bajo
from menu.models import Ingrediente, PlatoIngrediente

from .forms import MovimientoInventarioForm
from .models import MovimientoInventario

logger = logging.getLogger(__name__)


@mesero_required
def lista_inventario(request):
    solo_bajo_stock = request.GET.get('solo_bajo_stock') == '1'
    ingredientes = Ingrediente.objects.filter(activo=True)
    n_bajo_stock = Ingrediente.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo'),
    ).count()

    return render(request, 'inventory/lista_inventario.html', {
        'ingredientes': ingredientes,
        'solo_bajo_stock': solo_bajo_stock,
        'n_bajo_stock': n_bajo_stock,
    })


@mesero_required
def registrar_movimiento(request):
    form = MovimientoInventarioForm(request.POST or None)
    if form.is_valid():
        ingrediente = form.cleaned_data['ingrediente']
        tipo = form.cleaned_data['tipo']
        cantidad = form.cleaned_data['cantidad']

        if tipo == 'entrada':
            ingrediente.stock_actual += cantidad
        elif tipo == 'salida':
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
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if ingrediente_id:
        movimientos = movimientos.filter(ingrediente_id=ingrediente_id)
    if tipo_filtro:
        movimientos = movimientos.filter(tipo=tipo_filtro)
    if fecha_desde:
        try:
            movimientos = movimientos.filter(fecha__date__gte=date.fromisoformat(fecha_desde))
        except ValueError:
            fecha_desde = ''
    if fecha_hasta:
        try:
            movimientos = movimientos.filter(fecha__date__lte=date.fromisoformat(fecha_hasta))
        except ValueError:
            fecha_hasta = ''

    return render(request, 'inventory/historial_movimientos.html', {
        'movimientos': movimientos,
        'ingredientes': ingredientes,
        'ingrediente_id': ingrediente_id,
        'tipo_filtro': tipo_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
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


@admin_required
def stock_por_categoria(request):
    from orders.models import DetallePedido

    hace_30_dias = date.today() - timedelta(days=30)
    hoy = date.today()
    estados_completados = ['listo', 'entregado']

    subtotal_expr = ExpressionWrapper(
        F('cantidad') * F('precio_unitario'),
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )

    # Ventas por categoría en los últimos 30 días
    consumo_por_categoria = (
        DetallePedido.objects
        .filter(
            pedido__fecha_creacion__date__gte=hace_30_dias,
            pedido__estado__in=estados_completados,
        )
        .values('plato__categoria__nombre', 'plato__categoria_id')
        .annotate(
            total_porciones=Sum('cantidad'),
            ingresos=Sum(subtotal_expr),
        )
        .order_by('-total_porciones')
    )

    # Consumo de ingredientes por categoría (vía PlatoIngrediente)
    ingredientes_consumidos = (
        PlatoIngrediente.objects
        .filter(
            plato__detalles_pedido__pedido__fecha_creacion__date__gte=hace_30_dias,
            plato__detalles_pedido__pedido__estado__in=estados_completados,
        )
        .values(
            'plato__categoria__nombre',
            'ingrediente__nombre',
            'ingrediente__unidad_medida',
            'ingrediente__stock_actual',
            'ingrediente__stock_minimo',
        )
        .annotate(
            cantidad_consumida=Sum(
                ExpressionWrapper(
                    F('cantidad_necesaria') * F('plato__detalles_pedido__cantidad'),
                    output_field=DecimalField(max_digits=12, decimal_places=4),
                )
            )
        )
        .order_by('plato__categoria__nombre', '-cantidad_consumida')
    )

    return render(request, 'inventory/stock_por_categoria.html', {
        'consumo_por_categoria': consumo_por_categoria,
        'ingredientes_consumidos': ingredientes_consumidos,
        'fecha_desde': hace_30_dias,
        'fecha_hasta': hoy,
    })
