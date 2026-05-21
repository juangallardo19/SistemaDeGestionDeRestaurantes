from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required, mesero_required
from accounts.email_utils import send_confirmacion_reserva, send_reserva_confirmada

from .forms import FiltroReservaForm, MesaForm, ReservaForm
from .models import Mesa, Reserva


@login_required
def hacer_reserva(request):
    form = ReservaForm(request.POST or None)
    if form.is_valid():
        reserva = form.save(commit=False)
        reserva.cliente = request.user
        reserva.save()
        send_confirmacion_reserva(reserva)
        messages.success(
            request,
            f'Reserva creada para el {reserva.fecha} a las {reserva.hora_inicio}. '
            'Recibirás un correo de confirmación.',
        )
        return redirect('reservations:list')
    return render(request, 'reservations/hacer_reserva.html', {'form': form})


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(cliente=request.user).select_related('mesa')
    return render(request, 'reservations/mis_reservas.html', {
        'reservas': reservas,
        'today': date.today(),
    })


@login_required
def cancelar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, cliente=request.user)

    if reserva.estado not in ['pendiente', 'confirmada']:
        messages.error(request, 'Solo podés cancelar reservas pendientes o confirmadas.')
        return redirect('reservations:list')

    if reserva.fecha <= date.today():
        messages.error(request, 'No podés cancelar reservas de fechas pasadas o del día de hoy.')
        return redirect('reservations:list')

    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()
        messages.success(request, f'Reserva del {reserva.fecha} a las {reserva.hora_inicio} cancelada.')
        return redirect('reservations:list')

    return render(request, 'reservations/cancelar_reserva.html', {'reserva': reserva})


@mesero_required
def lista_reservas(request):
    form = FiltroReservaForm(request.GET or None)
    qs = Reserva.objects.select_related('cliente', 'mesa').all()

    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            qs = qs.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            qs = qs.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data.get('estado'):
            qs = qs.filter(estado=form.cleaned_data['estado'])

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reservations/lista_reservas.html', {
        'reservas': page_obj,
        'page_obj': page_obj,
        'form': form,
    })


@mesero_required
def confirmar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        if reserva.estado == 'pendiente':
            reserva.estado = 'confirmada'
            reserva.save()
            send_reserva_confirmada(reserva)
            messages.success(
                request,
                f'Reserva #{pk} confirmada. Se notificó al cliente por correo.',
            )
        else:
            messages.warning(request, f'La reserva #{pk} no está en estado pendiente.')
    return redirect('reservations:lista_reservas')


@mesero_required
def completar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        if reserva.estado == 'confirmada':
            reserva.estado = 'completada'
            reserva.save()
            messages.success(
                request,
                f'Reserva #{pk} marcada como completada. La mesa queda liberada.',
            )
        else:
            messages.warning(request, 'Solo se pueden completar reservas en estado confirmada.')
    return redirect('reservations:lista_reservas')


@mesero_required
def mesa_detalle(request, pk):
    from orders.models import Pedido
    mesa = get_object_or_404(Mesa, pk=pk, activa=True)
    today = date.today()

    pedidos_activos = (
        Pedido.objects
        .filter(mesa=mesa, estado__in=['pendiente', 'en_preparacion', 'listo'])
        .select_related('cliente', 'mesero')
        .prefetch_related('detalles__plato')
        .order_by('fecha_creacion')
    )
    reserva_hoy = Reserva.objects.filter(
        mesa=mesa, fecha=today, estado__in=['pendiente', 'confirmada']
    ).select_related('cliente').first()

    total_mesa = sum(p.total for p in pedidos_activos)

    return render(request, 'reservations/mesa_detalle.html', {
        'mesa': mesa,
        'pedidos_activos': pedidos_activos,
        'reserva_hoy': reserva_hoy,
        'total_mesa': total_mesa,
        'today': today,
    })


@mesero_required
def mesas_overview(request):
    from orders.models import Pedido
    today = date.today()
    mesas = Mesa.objects.filter(activa=True).order_by('numero')
    mesa_data = []
    for mesa in mesas:
        reserva_hoy = Reserva.objects.filter(
            mesa=mesa, fecha=today, estado__in=['pendiente', 'confirmada']
        ).select_related('cliente').first()
        pedidos_activos = list(
            Pedido.objects.filter(
                mesa=mesa, estado__in=['pendiente', 'en_preparacion', 'listo']
            ).select_related('cliente')
        )
        total_mesa = sum(p.total for p in pedidos_activos)
        if pedidos_activos and reserva_hoy:
            estado = 'mixta'
        elif pedidos_activos:
            estado = 'con_pedido'
        elif reserva_hoy:
            estado = 'reservada'
        else:
            estado = 'libre'
        mesa_data.append({
            'mesa': mesa,
            'reserva_hoy': reserva_hoy,
            'pedidos_activos': pedidos_activos,
            'total_mesa': total_mesa,
            'estado': estado,
        })
    return render(request, 'reservations/mesas_overview.html', {
        'mesa_data': mesa_data,
        'today': today,
    })


# ── CRUD Mesas ────────────────────────────────────────────────────────────────

@admin_required
def crud_mesas(request):
    form = MesaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        mesa = form.save()
        messages.success(request, f'Mesa {mesa.numero} creada exitosamente.')
        return redirect('reservations:crud_mesas')
    mesas = Mesa.objects.all()
    return render(request, 'reservations/crud_mesas.html', {'mesas': mesas, 'form': form})


@admin_required
def editar_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    form = MesaForm(request.POST or None, instance=mesa)
    if form.is_valid():
        form.save()
        messages.success(request, f'Mesa {mesa.numero} actualizada.')
        return redirect('reservations:crud_mesas')
    return render(request, 'reservations/editar_mesa.html', {'form': form, 'mesa': mesa})


@admin_required
def toggle_mesa(request, pk):
    if request.method == 'POST':
        mesa = get_object_or_404(Mesa, pk=pk)
        mesa.activa = not mesa.activa
        mesa.save()
        estado = 'activada' if mesa.activa else 'desactivada'
        messages.success(request, f'Mesa {mesa.numero} {estado}.')
    return redirect('reservations:crud_mesas')


# ── API JSON ──────────────────────────────────────────────────────────────────

@login_required
def disponibilidad_mesas(request):
    """
    GET /reservations/disponibilidad/?fecha=YYYY-MM-DD&hora_inicio=HH:MM&hora_fin=HH:MM
    Retorna JSON con las mesas activas que no tienen conflicto de reserva.
    """
    fecha_str = request.GET.get('fecha', '')
    hora_inicio_str = request.GET.get('hora_inicio', '')
    hora_fin_str = request.GET.get('hora_fin', '')

    if not all([fecha_str, hora_inicio_str, hora_fin_str]):
        return JsonResponse(
            {'error': 'Parámetros requeridos: fecha, hora_inicio, hora_fin.'},
            status=400,
        )

    try:
        from datetime import time
        fecha = date.fromisoformat(fecha_str)
        hora_inicio = time.fromisoformat(hora_inicio_str)
        hora_fin = time.fromisoformat(hora_fin_str)
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha u hora inválido.'}, status=400)

    if hora_fin <= hora_inicio:
        return JsonResponse(
            {'error': 'La hora de fin debe ser posterior a la hora de inicio.'},
            status=400,
        )

    ocupadas_ids = Reserva.objects.filter(
        fecha=fecha,
        estado__in=['pendiente', 'confirmada'],
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    ).values_list('mesa_id', flat=True)

    mesas = Mesa.objects.filter(activa=True).exclude(pk__in=ocupadas_ids)

    return JsonResponse({
        'mesas': [
            {
                'id': m.pk,
                'numero': m.numero,
                'capacidad': m.capacidad,
                'ubicacion': m.get_ubicacion_display(),
                'ubicacion_slug': m.ubicacion,
            }
            for m in mesas
        ]
    })
