import copy
from decimal import Decimal

from menu.models import Plato

CARRITO_SESSION_KEY = 'carrito'


class Carrito:
    def __init__(self, request):
        self.session = request.session
        self._carrito = self.session.setdefault(CARRITO_SESSION_KEY, {})

    def _guardar(self):
        self.session.modified = True

    def agregar(self, plato, cantidad=1):
        """Agrega un plato o incrementa su cantidad si ya existe."""
        plato_id = str(plato.pk)
        if plato_id not in self._carrito:
            self._carrito[plato_id] = {
                'cantidad': 0,
                'precio': str(plato.precio),
            }
        self._carrito[plato_id]['cantidad'] += cantidad
        self._guardar()

    def remover(self, plato_id):
        """Elimina un plato del carrito."""
        plato_id = str(plato_id)
        if plato_id in self._carrito:
            del self._carrito[plato_id]
            self._guardar()

    def actualizar(self, plato_id, cantidad):
        """Establece la cantidad exacta de un plato. Si cantidad <= 0 lo remueve."""
        plato_id = str(plato_id)
        if plato_id in self._carrito:
            if cantidad > 0:
                self._carrito[plato_id]['cantidad'] = cantidad
            else:
                del self._carrito[plato_id]
            self._guardar()

    def limpiar(self):
        """Vacía el carrito completamente."""
        del self.session[CARRITO_SESSION_KEY]
        self._carrito = {}
        self.session.modified = True

    def __iter__(self):
        """
        Itera sobre los ítems enriquecidos con el objeto Plato y el subtotal.
        Ignora silenciosamente platos que ya no existan en la BD.
        """
        plato_ids = list(self._carrito.keys())
        platos = {str(p.pk): p for p in Plato.objects.filter(pk__in=plato_ids)}
        carrito = copy.deepcopy(self._carrito)

        for plato_id, item in carrito.items():
            if plato_id not in platos:
                continue
            item['plato'] = platos[plato_id]
            item['precio'] = Decimal(item['precio'])
            item['subtotal'] = item['precio'] * item['cantidad']
            yield item

    def get_total(self):
        """Retorna el total del carrito como Decimal."""
        return sum(
            Decimal(item['precio']) * item['cantidad']
            for item in self._carrito.values()
        )

    def __len__(self):
        """Retorna la cantidad total de unidades en el carrito."""
        return sum(item['cantidad'] for item in self._carrito.values())
