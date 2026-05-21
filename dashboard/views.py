import logging
from datetime import datetime, timedelta

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import solo_admin
from inventory.models import MovimientoInventario
from menu.models import Ingrediente
from orders.models import DetallePedido, Pedido
from reservations.models import Mesa, Reserva

from .exports import (
    generar_excel_inventario,
    generar_excel_pedidos,
    generar_pdf_inventario,
    generar_pdf_pedidos,
)

logger = logging.getLogger(__name__)

_MESES_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

_CHART_COLORS = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
    '#FF9F40', '#C9CBCF', '#7BC8A4', '#E7A1B0', '#B5A7D5',
]

_ESTADO_LABELS = {
    'pendiente': 'Pendiente',
    'en_preparacion': 'En preparación',
    'listo': 'Listo',
    'entregado': 'Entregado',
    'cancelado': 'Cancelado',
}


def _fmt_mes(dt):
    return f'{_MESES_ES[dt.month]} {dt.year}'


def _parse_fechas(request):
    today = timezone.now().date()
    try:
        fecha_desde = datetime.strptime(
            request.GET.get('fecha_desde', str(today - timedelta(days=30))),
            '%Y-%m-%d',
        ).date()
        fecha_hasta = datetime.strptime(
            request.GET.get('fecha_hasta', str(today)),
            '%Y-%m-%d',
        ).date()
    except ValueError:
        fecha_desde = today - timedelta(days=30)
        fecha_hasta = today
    return fecha_desde, fecha_hasta


# ── Dashboard principal ───────────────────────────────────────────────────────

_RANGO_LABELS = {
    'hoy':    'Hoy',
    'semana': 'Últimos 7 días',
    'mes':    'Este mes',
    'year':   'Este año',
}


def _rango_inicio(rango, today):
    if rango == 'semana':
        return today - timedelta(days=6)
    if rango == 'mes':
        return today.replace(day=1)
    if rango == 'year':
        return today.replace(month=1, day=1)
    return today  # 'hoy'


@solo_admin
def dashboard_principal(request):
    today = timezone.now().date()
    rango = request.GET.get('rango', 'hoy')
    if rango not in _RANGO_LABELS:
        rango = 'hoy'
    fecha_inicio = _rango_inicio(rango, today)

    total_pedidos_hoy = Pedido.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=today,
    ).exclude(estado='cancelado').count()

    ingresos_hoy = (
        Pedido.objects
        .filter(
            fecha_creacion__date__gte=fecha_inicio,
            fecha_creacion__date__lte=today,
            estado__in=['listo', 'entregado'],
        )
        .aggregate(total=Sum('total'))['total'] or 0
    )

    ingresos_en_proceso = (
        Pedido.objects
        .filter(
            fecha_creacion__date__gte=fecha_inicio,
            fecha_creacion__date__lte=today,
            estado__in=['pendiente', 'en_preparacion'],
        )
        .aggregate(total=Sum('total'))['total'] or 0
    )

    mesas_ocupadas = (
        Pedido.objects
        .filter(estado__in=['pendiente', 'en_preparacion', 'listo'])
        .exclude(mesa__isnull=True)
        .values('mesa')
        .distinct()
        .count()
    )

    stock_bajo_count = (
        Ingrediente.objects
        .filter(activo=True, stock_actual__lte=F('stock_minimo'))
        .count()
    )

    return render(request, 'dashboard/principal.html', {
        'total_pedidos_hoy':   total_pedidos_hoy,
        'ingresos_hoy':        ingresos_hoy,
        'ingresos_en_proceso': ingresos_en_proceso,
        'mesas_ocupadas':      mesas_ocupadas,
        'stock_bajo_count':    stock_bajo_count,
        'rango':               rango,
        'rango_label':         _RANGO_LABELS[rango],
        'rango_opciones':      list(_RANGO_LABELS.items()),
    })


# ── Endpoints JSON para gráficos ──────────────────────────────────────────────

@solo_admin
def json_platos_mas_vendidos(request):
    today = timezone.now().date()
    rango = request.GET.get('rango', 'mes')
    desde = _rango_inicio(rango if rango in _RANGO_LABELS else 'mes', today)

    platos = (
        DetallePedido.objects
        .filter(pedido__fecha_creacion__date__gte=desde)
        .exclude(pedido__estado='cancelado')
        .values('plato__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    )

    labels = [p['plato__nombre'] for p in platos]
    valores = [p['total_vendido'] for p in platos]
    colores = _CHART_COLORS[:len(labels)]

    return JsonResponse({'labels': labels, 'valores': valores, 'colores': colores})


@solo_admin
def json_ingresos_por_mes(request):
    hace_12_meses = timezone.now() - timedelta(days=365)

    ingresos = (
        Pedido.objects
        .filter(estado__in=['listo', 'entregado'], fecha_creacion__gte=hace_12_meses)
        .annotate(mes=TruncMonth('fecha_creacion'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    labels = [_fmt_mes(row['mes']) for row in ingresos]
    valores = [float(row['total']) for row in ingresos]

    return JsonResponse({'labels': labels, 'valores': valores})


@solo_admin
def json_pedidos_por_estado(request):
    estados = (
        Pedido.objects
        .values('estado')
        .annotate(total=Count('id'))
        .order_by('estado')
    )

    labels = [_ESTADO_LABELS.get(row['estado'], row['estado']) for row in estados]
    valores = [row['total'] for row in estados]

    return JsonResponse({'labels': labels, 'valores': valores})


@solo_admin
def json_reservas_por_mes(request):
    hace_6_meses = timezone.now() - timedelta(days=180)

    reservas = (
        Reserva.objects
        .filter(fecha_creacion__gte=hace_6_meses)
        .annotate(mes=TruncMonth('fecha_creacion'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    labels = [_fmt_mes(row['mes']) for row in reservas]
    valores = [row['total'] for row in reservas]

    return JsonResponse({'labels': labels, 'valores': valores})


@solo_admin
def json_ocupacion_mesas(request):
    today = timezone.now().date()
    inicio_mes = today.replace(day=1)
    dias_en_mes = max((today - inicio_mes).days + 1, 1)

    mesas_qs = Mesa.objects.filter(activa=True).order_by('numero')
    resultado = []

    for mesa in mesas_qs:
        pedidos_mes = (
            Pedido.objects
            .filter(mesa=mesa, fecha_creacion__date__gte=inicio_mes)
            .exclude(estado='cancelado')
            .count()
        )
        dias_activos = (
            Pedido.objects
            .filter(mesa=mesa, fecha_creacion__date__gte=inicio_mes)
            .exclude(estado='cancelado')
            .dates('fecha_creacion', 'day')
            .count()
        )
        porcentaje = round((dias_activos / dias_en_mes) * 100, 1)
        resultado.append({
            'numero':     mesa.numero,
            'ubicacion':  mesa.get_ubicacion_display(),
            'capacidad':  mesa.capacidad,
            'pedidos_mes': pedidos_mes,
            'porcentaje': porcentaje,
        })

    return JsonResponse({'mesas': resultado})


# ── Exportaciones ─────────────────────────────────────────────────────────────

@solo_admin
def exportar_pedidos_pdf(request):
    fecha_desde, fecha_hasta = _parse_fechas(request)
    pedidos = (
        Pedido.objects
        .filter(
            fecha_creacion__date__gte=fecha_desde,
            fecha_creacion__date__lte=fecha_hasta,
        )
        .select_related('cliente', 'mesero')
        .prefetch_related('detalles__plato')
        .order_by('fecha_creacion')
    )
    buffer = generar_pdf_pedidos(pedidos, fecha_desde, fecha_hasta)
    filename = f'pedidos_{fecha_desde}_{fecha_hasta}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@solo_admin
def exportar_pedidos_excel(request):
    fecha_desde, fecha_hasta = _parse_fechas(request)
    pedidos = (
        Pedido.objects
        .filter(
            fecha_creacion__date__gte=fecha_desde,
            fecha_creacion__date__lte=fecha_hasta,
        )
        .select_related('cliente', 'mesero')
        .prefetch_related('detalles__plato')
        .order_by('fecha_creacion')
    )
    buffer = generar_excel_pedidos(pedidos, fecha_desde, fecha_hasta)
    filename = f'pedidos_{fecha_desde}_{fecha_hasta}.xlsx'
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@solo_admin
def exportar_inventario_pdf(request):
    ingredientes = Ingrediente.objects.filter(activo=True).order_by('nombre')
    buffer = generar_pdf_inventario(ingredientes)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventario.pdf"'
    return response


@solo_admin
def exportar_inventario_excel(request):
    ingredientes = Ingrediente.objects.filter(activo=True).order_by('nombre')
    movimientos = (
        MovimientoInventario.objects
        .select_related('ingrediente', 'responsable')
        .order_by('-fecha')
    )
    buffer = generar_excel_inventario(ingredientes, movimientos)
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="inventario.xlsx"'
    return response
