from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required, mesero_required
from accounts.email_utils import send_confirmacion_reserva

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
    reservas = Reserva.objects.select_related('cliente', 'mesa').all()

    if form.is_valid():
        if form.cleaned_data.get('fecha_desde'):
            reservas = reservas.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            reservas = reservas.filter(fecha__lte=form.cleaned_data['fecha_hasta'])
        if form.cleaned_data.get('estado'):
            reservas = reservas.filter(estado=form.cleaned_data['estado'])

    return render(request, 'reservations/lista_reservas.html', {
        'reservas': reservas,
        'form': form,
    })


@mesero_required
def confirmar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        if reserva.estado == 'pendiente':
            reserva.estado = 'confirmada'
            reserva.save()
            messages.success(request, f'Reserva #{pk} confirmada exitosamente.')
        else:
            messages.warning(request, f'La reserva #{pk} no está en estado pendiente.')
    return redirect('reservations:lista_reservas')


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
            }
            for m in mesas
        ]
    })
