import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
from .forms import (
    AgregarAlCarritoForm,
    AsignarMeseroForm,
    CambiarEstadoPedidoForm,
    PedidoForm,
)
from .models import DetallePedido, Pedido

logger = logging.getLogger(__name__)


def _descontar_ingredientes(pedido, responsable):
    """
    Por cada DetallePedido descuenta del stock los ingredientes del plato,
    registra el movimiento en inventario y emite alerta si el stock queda bajo.
    """
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

                # Email y limpieza del carrito fuera de la transacción
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
    pedidos = Pedido.objects.select_related('cliente', 'mesero').all()

    estado_filtro = request.GET.get('estado', '')
    fecha_filtro = request.GET.get('fecha', '')

    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    if fecha_filtro:
        try:
            fecha = date.fromisoformat(fecha_filtro)
            pedidos = pedidos.filter(fecha_creacion__date=fecha)
        except ValueError:
            pass

    return render(request, 'orders/historial_pedidos.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'fecha_filtro': fecha_filtro,
        'estado_choices': Pedido.ESTADO_CHOICES,
    })
