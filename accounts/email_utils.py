import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_confirmacion_pedido(pedido):
    """Envía al cliente la confirmación con el detalle completo del pedido."""
    try:
        if not pedido.cliente.email:
            return

        context = {
            'pedido': pedido,
            'cliente': pedido.cliente,
            'detalles': pedido.detalles.select_related('plato').all(),
        }
        html_message = render_to_string('emails/confirmacion_pedido.html', context)

        send_mail(
            subject=f'Confirmación de pedido #{pedido.pk} — RestaurApp',
            message=(
                f'Hola {pedido.cliente.get_full_name() or pedido.cliente.username}, '
                f'tu pedido #{pedido.pk} fue recibido. Total: ${pedido.total}.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.cliente.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logger.exception('Error enviando confirmación del pedido #%s', pedido.pk)


def send_confirmacion_reserva(reserva):
    """Envía al cliente la confirmación de su reserva."""
    try:
        if not reserva.cliente.email:
            return

        context = {
            'reserva': reserva,
            'cliente': reserva.cliente,
            'mesa': reserva.mesa,
        }
        html_message = render_to_string('emails/confirmacion_reserva.html', context)

        send_mail(
            subject='Confirmación de reserva — RestaurApp',
            message=(
                f'Hola {reserva.cliente.get_full_name() or reserva.cliente.username}, '
                f'tu reserva para el {reserva.fecha} a las {reserva.hora_inicio} '
                f'en mesa {reserva.mesa.numero} fue registrada.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reserva.cliente.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logger.exception('Error enviando confirmación de reserva #%s', reserva.pk)


def send_reserva_confirmada(reserva):
    """Notifica al cliente que el restaurante confirmó su reserva."""
    try:
        if not reserva.cliente.email:
            return

        context = {
            'reserva': reserva,
            'cliente': reserva.cliente,
            'mesa': reserva.mesa,
        }
        html_message = render_to_string('emails/confirmacion_reserva.html', context)

        send_mail(
            subject='Tu reserva fue confirmada — RestaurApp',
            message=(
                f'Hola {reserva.cliente.get_full_name() or reserva.cliente.username}, '
                f'tu reserva del {reserva.fecha} a las {reserva.hora_inicio} '
                f'en mesa {reserva.mesa.numero} fue confirmada por el restaurante.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reserva.cliente.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logger.exception('Error enviando confirmación de reserva #%s', reserva.pk)


def send_cambio_estado_pedido(pedido, estado_anterior):
    """Notifica al cliente cuando el estado de su pedido cambia."""
    try:
        if not pedido.cliente.email:
            return

        context = {
            'pedido': pedido,
            'cliente': pedido.cliente,
            'estado_anterior': estado_anterior,
            'estado_nuevo': pedido.estado,
        }
        html_message = render_to_string('emails/cambio_estado_pedido.html', context)

        send_mail(
            subject=f'Actualización de tu pedido #{pedido.pk} — RestaurApp',
            message=(
                f'El estado de tu pedido #{pedido.pk} cambió '
                f'de "{estado_anterior}" a "{pedido.get_estado_display()}".'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.cliente.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logger.exception('Error enviando cambio de estado del pedido #%s', pedido.pk)


def send_alerta_stock_bajo(ingrediente):
    """Envía una alerta al administrador cuando el stock de un ingrediente está bajo."""
    try:
        admin_email = getattr(settings, 'ADMIN_EMAIL', None) or settings.EMAIL_HOST_USER
        if not admin_email:
            logger.warning('ADMIN_EMAIL no configurado. No se envió alerta para %s.', ingrediente.nombre)
            return

        html_message = (
            f'<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">'
            f'<div style="background:#dc3545;padding:20px;text-align:center;">'
            f'<h2 style="color:#fff;margin:0;">&#9888; Alerta de Stock Bajo</h2>'
            f'</div>'
            f'<div style="padding:30px;background:#fff;border:1px solid #dee2e6;">'
            f'<p style="font-size:16px;">El ingrediente <strong>{ingrediente.nombre}</strong> '
            f'está por debajo del stock mínimo requerido.</p>'
            f'<table style="width:100%;border-collapse:collapse;margin-top:16px;">'
            f'<tr style="background:#f8f9fa;">'
            f'<td style="padding:10px;border:1px solid #dee2e6;">Stock actual</td>'
            f'<td style="padding:10px;border:1px solid #dee2e6;color:#dc3545;font-weight:bold;">'
            f'{ingrediente.stock_actual} {ingrediente.unidad_medida}</td>'
            f'</tr>'
            f'<tr>'
            f'<td style="padding:10px;border:1px solid #dee2e6;">Stock mínimo</td>'
            f'<td style="padding:10px;border:1px solid #dee2e6;">'
            f'{ingrediente.stock_minimo} {ingrediente.unidad_medida}</td>'
            f'</tr>'
            f'</table>'
            f'<p style="margin-top:20px;color:#666;">Por favor registra una entrada de inventario.</p>'
            f'</div>'
            f'</div>'
        )

        send_mail(
            subject=f'⚠ Stock bajo: {ingrediente.nombre} — RestaurApp',
            message=(
                f'ALERTA: {ingrediente.nombre} tiene stock bajo. '
                f'Actual: {ingrediente.stock_actual} {ingrediente.unidad_medida}. '
                f'Mínimo: {ingrediente.stock_minimo} {ingrediente.unidad_medida}.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logger.exception('Error enviando alerta de stock bajo para %s', ingrediente.nombre)
