import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum
from django.http import JsonResponse
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

def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _carrito_payload(request):
    carrito = Carrito(request)
    items = []
    for item in carrito:
        items.append({
            'plato_id': item['plato'].pk,
            'nombre':   item['plato'].nombre,
            'cantidad': item['cantidad'],
            'precio':   str(item['precio']),
            'subtotal': str(item['subtotal']),
        })
    return {
        'items': items,
        'total': str(carrito.get_total()),
        'count': len(carrito),
    }


@login_required
def ver_carrito(request):
    carrito = Carrito(request)
    return render(request, 'orders/carrito.html', {
        'carrito': carrito,
        'total': carrito.get_total(),
    })


@login_required
def carrito_json(request):
    return JsonResponse(_carrito_payload(request))


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
            else:
                carrito.agregar(plato, cantidad)
            if _is_ajax(request):
                return JsonResponse(_carrito_payload(request))
            messages.success(request, f'"{plato.nombre}" agregado al carrito.')
    if _is_ajax(request):
        return JsonResponse(_carrito_payload(request))
    next_url = request.POST.get('next', '')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('orders:cart')


@login_required
def remover_del_carrito(request, plato_id):
    if request.method == 'POST':
        Carrito(request).remover(plato_id)
        if _is_ajax(request):
            return JsonResponse(_carrito_payload(request))
        messages.info(request, 'Plato removido del carrito.')
    if _is_ajax(request):
        return JsonResponse(_carrito_payload(request))
    return redirect('orders:cart')


@login_required
def actualizar_carrito(request, plato_id):
    if request.method == 'POST':
        form = AgregarAlCarritoForm(request.POST)
        if form.is_valid():
            Carrito(request).actualizar(plato_id, form.cleaned_data['cantidad'])
            if _is_ajax(request):
                return JsonResponse(_carrito_payload(request))
            messages.success(request, 'Carrito actualizado.')
    if _is_ajax(request):
        return JsonResponse(_carrito_payload(request))
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
                        mesa=form.cleaned_data.get('mesa'),
                        mesero=request.user if request.user.is_mesero else None,
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

    mesas_ocupadas_ids = list(
        Pedido.objects
        .filter(estado__in=['pendiente', 'en_preparacion', 'listo'])
        .exclude(mesa__isnull=True)
        .values_list('mesa_id', flat=True)
        .distinct()
    )

    return render(request, 'orders/crear_pedido.html', {
        'form': form,
        'carrito': carrito,
        'total': carrito.get_total(),
        'mesas_ocupadas_ids': mesas_ocupadas_ids,
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
    qs = Pedido.objects.filter(
        estado__in=['pendiente', 'en_preparacion', 'listo'],
    ).select_related('cliente', 'mesero', 'mesa').prefetch_related('detalles__plato').order_by('fecha_creacion')

    listos = [p for p in qs if p.estado == 'listo']
    en_preparacion = [p for p in qs if p.estado == 'en_preparacion']
    pendientes = [p for p in qs if p.estado == 'pendiente']

    return render(request, 'orders/lista_pedidos_activos.html', {
        'pedidos': qs,
        'listos': listos,
        'en_preparacion': en_preparacion,
        'pendientes': pendientes,
    })


_TRANSICIONES_VALIDAS = {
    'pendiente':      ['en_preparacion', 'cancelado'],
    'en_preparacion': ['listo', 'cancelado'],
    'listo':          ['entregado'],
    'entregado':      [],
    'cancelado':      [],
}


@mesero_required
def cambiar_estado_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado', '')
        permitidos = _TRANSICIONES_VALIDAS.get(pedido.estado, [])
        if nuevo_estado not in permitidos:
            messages.error(
                request,
                f'No se puede cambiar el pedido #{pk} de '
                f'"{pedido.get_estado_display()}" a ese estado.',
            )
        else:
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            pedido.save(update_fields=['estado', 'fecha_actualizacion'])
            send_cambio_estado_pedido(pedido, estado_anterior)
            messages.success(
                request,
                f'Pedido #{pk} → {pedido.get_estado_display()}.',
            )
        next_url = request.POST.get('next', '')
        return redirect(next_url if next_url and next_url.startswith('/') else 'orders:list')

    form = CambiarEstadoPedidoForm(instance=pedido)
    return render(request, 'orders/cambiar_estado.html', {'form': form, 'pedido': pedido})


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
