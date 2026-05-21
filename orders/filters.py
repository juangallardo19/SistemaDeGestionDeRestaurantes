from django.db.models import Q

from .models import Pedido


class PedidoFilter:
    def __init__(self, data, queryset=None):
        self.data = data or {}
        self.queryset = queryset if queryset is not None else Pedido.objects.all()

    def filter(self):
        qs = self.queryset

        fecha_desde = self.data.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(fecha_creacion__date__gte=fecha_desde)

        fecha_hasta = self.data.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(fecha_creacion__date__lte=fecha_hasta)

        estado = self.data.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        mesero_id = self.data.get('mesero')
        if mesero_id:
            qs = qs.filter(mesero_id=mesero_id)

        cliente = (self.data.get('cliente') or '').strip()
        if cliente:
            qs = qs.filter(
                Q(cliente__first_name__icontains=cliente)
                | Q(cliente__last_name__icontains=cliente)
                | Q(cliente__email__icontains=cliente)
                | Q(cliente__username__icontains=cliente)
            )

        metodo_pago = self.data.get('metodo_pago')
        if metodo_pago:
            qs = qs.filter(metodo_pago=metodo_pago)

        return qs


class ReservaFilter:
    def __init__(self, data, queryset=None):
        from reservations.models import Reserva
        self.data = data or {}
        self.queryset = queryset if queryset is not None else Reserva.objects.all()

    def filter(self):
        qs = self.queryset

        fecha_desde = self.data.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)

        fecha_hasta = self.data.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)

        estado = self.data.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        mesa_id = self.data.get('mesa')
        if mesa_id:
            qs = qs.filter(mesa_id=mesa_id)

        return qs
