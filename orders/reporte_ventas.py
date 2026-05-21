from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate

from .models import DetallePedido, Pedido

ESTADOS_COMPLETADOS = ['listo', 'entregado']


def ventas_del_dia(fecha=None):
    if fecha is None:
        fecha = date.today()

    agg = Pedido.objects.filter(
        fecha_creacion__date=fecha,
        estado__in=ESTADOS_COMPLETADOS,
    ).aggregate(
        ingresos_totales=Sum('total'),
        total_pedidos=Count('pk'),
    )

    total_pedidos = agg['total_pedidos'] or 0
    ingresos_totales = agg['ingresos_totales'] or Decimal('0')
    ticket_promedio = ingresos_totales / total_pedidos if total_pedidos else Decimal('0')

    pedidos_por_estado = {
        estado: Pedido.objects.filter(fecha_creacion__date=fecha, estado=estado).count()
        for estado, _ in Pedido.ESTADO_CHOICES
    }

    return {
        'fecha': fecha,
        'total_pedidos': total_pedidos,
        'ingresos_totales': ingresos_totales,
        'ticket_promedio': ticket_promedio,
        'pedidos_por_estado': pedidos_por_estado,
    }


def ventas_por_rango(fecha_desde, fecha_hasta):
    return (
        Pedido.objects
        .filter(
            fecha_creacion__date__gte=fecha_desde,
            fecha_creacion__date__lte=fecha_hasta,
            estado__in=ESTADOS_COMPLETADOS,
        )
        .annotate(dia=TruncDate('fecha_creacion'))
        .values('dia')
        .annotate(total_pedidos=Count('pk'), ingresos=Sum('total'))
        .order_by('dia')
    )


def platos_mas_vendidos(fecha_desde, fecha_hasta, limit=5):
    subtotal_expr = ExpressionWrapper(
        F('cantidad') * F('precio_unitario'),
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )
    return (
        DetallePedido.objects
        .filter(
            pedido__fecha_creacion__date__gte=fecha_desde,
            pedido__fecha_creacion__date__lte=fecha_hasta,
            pedido__estado__in=ESTADOS_COMPLETADOS,
        )
        .values('plato__nombre')
        .annotate(
            total_vendido=Sum('cantidad'),
            ingresos=Sum(subtotal_expr),
        )
        .order_by('-total_vendido')[:limit]
    )


def resumen_por_mesero(fecha_desde, fecha_hasta):
    return (
        Pedido.objects
        .filter(
            fecha_creacion__date__gte=fecha_desde,
            fecha_creacion__date__lte=fecha_hasta,
            estado__in=ESTADOS_COMPLETADOS,
            mesero__isnull=False,
        )
        .values('mesero__first_name', 'mesero__last_name', 'mesero__username')
        .annotate(
            total_pedidos=Count('pk'),
            ingresos_totales=Sum('total'),
        )
        .order_by('-ingresos_totales')
    )
