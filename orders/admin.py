from django.contrib import admin

from .models import DetallePedido, Pedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'mesero', 'mesa', 'estado', 'total', 'metodo_pago', 'fecha_creacion')
    list_filter = ('estado', 'metodo_pago', 'fecha_creacion')
    search_fields = ('cliente__username', 'cliente__email')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [DetallePedidoInline]


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'plato', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('pedido__id', 'plato__nombre')
    readonly_fields = ('subtotal',)
