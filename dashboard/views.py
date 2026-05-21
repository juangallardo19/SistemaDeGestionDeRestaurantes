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

@solo_admin
def dashboard_principal(request):
    today = timezone.now().date()

    total_pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=today).count()

    ingresos_hoy = (
        Pedido.objects
        .filter(fecha_creacion__date=today, estado='entregado')
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
        'total_pedidos_hoy': total_pedidos_hoy,
        'ingresos_hoy': ingresos_hoy,
        'mesas_ocupadas': mesas_ocupadas,
        'stock_bajo_count': stock_bajo_count,
    })


# ── Endpoints JSON para gráficos ──────────────────────────────────────────────

@solo_admin
def json_platos_mas_vendidos(request):
    inicio_mes = timezone.now().date().replace(day=1)

    platos = (
        DetallePedido.objects
        .filter(pedido__fecha_creacion__date__gte=inicio_mes)
        .values('plato__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    )

    labels = [p['plato__nombre'] for p in platos]
    data = [p['total_vendido'] for p in platos]
    colores = _CHART_COLORS[:len(labels)]

    return JsonResponse({'labels': labels, 'data': data, 'colores': colores})


@solo_admin
def json_ingresos_por_mes(request):
    hace_12_meses = timezone.now() - timedelta(days=365)

    ingresos = (
        Pedido.objects
        .filter(estado='entregado', fecha_creacion__gte=hace_12_meses)
        .annotate(mes=TruncMonth('fecha_creacion'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    labels = [_fmt_mes(row['mes']) for row in ingresos]
    data = [float(row['total']) for row in ingresos]

    return JsonResponse({'labels': labels, 'data': data})


@solo_admin
def json_pedidos_por_estado(request):
    estados = (
        Pedido.objects
        .values('estado')
        .annotate(total=Count('id'))
        .order_by('estado')
    )

    labels = [_ESTADO_LABELS.get(row['estado'], row['estado']) for row in estados]
    data = [row['total'] for row in estados]

    return JsonResponse({'labels': labels, 'data': data})


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
    data = [row['total'] for row in reservas]

    return JsonResponse({'labels': labels, 'data': data})


@solo_admin
def json_ocupacion_mesas(request):
    hace_30_dias = timezone.now().date() - timedelta(days=30)

    mesas = (
        Mesa.objects
        .filter(activa=True)
        .annotate(
            dias_ocupados=Count(
                'reservas__fecha',
                filter=Q(
                    reservas__estado='confirmada',
                    reservas__fecha__gte=hace_30_dias,
                ),
                distinct=True,
            )
        )
        .order_by('numero')
    )

    labels = [f'Mesa {m.numero}' for m in mesas]
    data = [min(round((m.dias_ocupados / 30) * 100, 1), 100) for m in mesas]

    return JsonResponse({'labels': labels, 'data': data})


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
