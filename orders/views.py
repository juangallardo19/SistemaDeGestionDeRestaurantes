import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required, mesero_required
from accounts.email_utils import (
    send_alerta_stock_bajo,
    send_cambio_estado_pedido,
    send_confirmacion_pedido,
)
from inventory.models import MovimientoInventario
from menu.models import Plato, PlatoIngrediente

from .carrito import Carrito
from .filters import PedidoFilter
from .forms import (
    AgregarAlCarritoForm,
    AsignarMeseroForm,
    CambiarEstadoPedidoForm,
    PedidoForm,
)
from .models import DetallePedido, Pedido

logger = logging.getLogger(__name__)


def _descontar_ingredientes(pedido, responsable):
    for detalle in pedido.detalles.select_related('plato').all():
        for pi in PlatoIngrediente.objects.filter(
            plato=detalle.plato
        ).select_related('ingrediente'):
            ingrediente = pi.ingrediente
            cantidad_descontar = pi.cantidad_necesaria * detalle.cantidad
            nuevo_stock = max(Decimal('0'), ingrediente.stock_actual - cantidad_descontar)
            ingrediente.stock_actual = nuevo_stock
            ingrediente.save(update_fields=['stock_actual'])
            MovimientoInventario.objects.create(
                ingrediente=ingrediente,
                tipo='salida',
                cantidad=cantidad_descontar,
                responsable=responsable,
                motivo=f'Pedido #{pedido.pk}',
                stock_resultante=nuevo_stock,
            )
            if ingrediente.stock_bajo:
                send_alerta_stock_bajo(ingrediente)


# ── Carrito ───────────────────────────────────────────────────────────────────

@login_required
def ver_carrito(request):
    carrito = Carrito(request)
    return render(request, 'orders/carrito.html', {
        'carrito': carrito,
        'total': carrito.get_total(),
    })


@login_required
def agregar_al_carrito(request, plato_id):
    plato = get_object_or_404(Plato, pk=plato_id, disponible=True)
    if request.method == 'POST':
        form = AgregarAlCarritoForm(request.POST)
        if form.is_valid():
            carrito = Carrito(request)
            cantidad = form.cleaned_data['cantidad']
            if form.cleaned_data.get('actualizar'):
                carrito.actualizar(plato.pk, cantidad)
                messages.success(request, 'Cantidad actualizada en el carrito.')
            else:
                carrito.agregar(plato, cantidad)
                messages.success(request, f'"{plato.nombre}" agregado al carrito.')
    return redirect('orders:cart')


@login_required
def remover_del_carrito(request, plato_id):
    if request.method == 'POST':
        Carrito(request).remover(plato_id)
        messages.info(request, 'Plato removido del carrito.')
    return redirect('orders:cart')


@login_required
def actualizar_carrito(request, plato_id):
    if request.method == 'POST':
        form = AgregarAlCarritoForm(request.POST)
        if form.is_valid():
            Carrito(request).actualizar(plato_id, form.cleaned_data['cantidad'])
            messages.success(request, 'Carrito actualizado.')
    return redirect('orders:cart')


# ── Pedidos ───────────────────────────────────────────────────────────────────

@login_required
def crear_pedido(request):
    carrito = Carrito(request)

    if len(carrito) == 0:
        messages.warning(request, 'Tu carrito está vacío. Agrega platos antes de confirmar.')
        return redirect('menu:list')

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pedido = Pedido.objects.create(
                        cliente=request.user,
                        notas=form.cleaned_data['notas'],
                        metodo_pago=form.cleaned_data['metodo_pago'],
                    )
                    for item in carrito:
                        DetallePedido.objects.create(
                            pedido=pedido,
                            plato=item['plato'],
                            cantidad=item['cantidad'],
                            precio_unitario=item['precio'],
                        )
                    pedido.calcular_total()
                    _descontar_ingredientes(pedido, request.user)

                send_confirmacion_pedido(pedido)
                carrito.limpiar()
                messages.success(
                    request,
                    f'¡Pedido #{pedido.pk} confirmado! Recibirás un correo de confirmación.',
                )
                return redirect('orders:detalle_pedido', pk=pedido.pk)

            except Exception:
                logger.exception('Error al crear el pedido para el usuario %s', request.user)
                messages.error(request, 'Ocurrió un error al procesar el pedido. Intenta nuevamente.')
    else:
        form = PedidoForm()

    return render(request, 'orders/crear_pedido.html', {
        'form': form,
        'carrito': carrito,
        'total': carrito.get_total(),
    })


@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(
        cliente=request.user,
    ).select_related('mesero').prefetch_related('detalles__plato')

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    return render(request, 'orders/mis_pedidos.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'estado_choices': Pedido.ESTADO_CHOICES,
    })


@login_required
def detalle_pedido(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente', 'mesero', 'mesa')
                      .prefetch_related('detalles__plato'),
        pk=pk,
    )

    puede_ver = (
        pedido.cliente == request.user
        or request.user.is_admin
        or request.user.is_mesero
    )
    if not puede_ver:
        messages.error(request, 'No tienes permiso para ver este pedido.')
        return redirect('menu:list')

    asignar_form = None
    if request.user.is_admin:
        if request.method == 'POST':
            asignar_form = AsignarMeseroForm(request.POST, instance=pedido)
            if asignar_form.is_valid():
                asignar_form.save()
                messages.success(request, 'Mesero asignado correctamente.')
                return redirect('orders:detalle_pedido', pk=pk)
        else:
            asignar_form = AsignarMeseroForm(instance=pedido)

    return render(request, 'orders/detalle_pedido.html', {
        'pedido': pedido,
        'asignar_form': asignar_form,
    })


@mesero_required
def lista_pedidos_activos(request):
    pedidos = Pedido.objects.filter(
        estado__in=['pendiente', 'en_preparacion'],
    ).select_related('cliente', 'mesero', 'mesa').prefetch_related('detalles__plato')

    return render(request, 'orders/lista_pedidos_activos.html', {'pedidos': pedidos})


@mesero_required
def cambiar_estado_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == 'POST':
        form = CambiarEstadoPedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            estado_anterior = pedido.estado
            form.save()
            send_cambio_estado_pedido(pedido, estado_anterior)
            messages.success(
                request,
                f'Estado del pedido #{pedido.pk} cambiado a "{pedido.get_estado_display()}".',
            )
            return redirect('orders:detalle_pedido', pk=pk)
    else:
        form = CambiarEstadoPedidoForm(instance=pedido)

    return render(request, 'orders/cambiar_estado.html', {
        'form': form,
        'pedido': pedido,
    })


@admin_required
def historial_pedidos(request):
    qs = Pedido.objects.select_related('cliente', 'mesero').prefetch_related('detalles')

    # Translate legacy single-date param to range for PedidoFilter
    get_data = request.GET.copy()
    if get_data.get('fecha') and not get_data.get('fecha_desde'):
        get_data['fecha_desde'] = get_data['fecha']
        get_data['fecha_hasta'] = get_data['fecha']

    pedidos_qs = PedidoFilter(get_data, qs).filter()

    totales = pedidos_qs.aggregate(
        total_ingresos=Sum('total'),
        total_count=Count('pk'),
    )

    paginator = Paginator(pedidos_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'orders/historial_pedidos.html', {
        'pedidos': page_obj,
        'page_obj': page_obj,
        'estado_choices': Pedido.ESTADO_CHOICES,
        'estado_filtro': request.GET.get('estado', ''),
        'fecha_filtro': request.GET.get('fecha', ''),
        'total_ingresos': totales['total_ingresos'] or Decimal('0'),
        'total_count': totales['total_count'] or 0,
    })


# ── Reportes ──────────────────────────────────────────────────────────────────

@admin_required
def reporte_ventas_diarias(request):
    from .reporte_ventas import (
        platos_mas_vendidos,
        resumen_por_mesero,
        ventas_del_dia,
        ventas_por_rango,
    )

    fecha_str = request.GET.get('fecha', '')
    try:
        fecha = date.fromisoformat(fecha_str) if fecha_str else date.today()
    except ValueError:
        fecha = date.today()

    kpis = ventas_del_dia(fecha)

    # Prepare pedidos_por_estado as list of (label, count) for easy template iteration
    pedidos_por_estado = [
        (label, kpis['pedidos_por_estado'].get(estado, 0))
        for estado, label in Pedido.ESTADO_CHOICES
    ]

    from datetime import timedelta
    semana_desde = fecha - timedelta(days=6)
    top_platos = platos_mas_vendidos(semana_desde, fecha, limit=5)
    resumen_meseros = resumen_por_mesero(semana_desde, fecha)
    ventas_semana = ventas_por_rango(semana_desde, fecha)

    return render(request, 'orders/reporte_ventas.html', {
        'fecha': fecha,
        'kpis': kpis,
        'pedidos_por_estado': pedidos_por_estado,
        'top_platos': top_platos,
        'resumen_meseros': resumen_meseros,
        'ventas_semana': ventas_semana,
        'semana_desde': semana_desde,
    })
