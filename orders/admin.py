from django.contrib import admin

from .models import DetallePedido, Pedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('plato', 'cantidad', 'precio_unitario', 'subtotal')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'mesero', 'estado', 'total', 'metodo_pago', 'fecha_creacion')
    list_filter = ('estado', 'metodo_pago', 'fecha_creacion')
    search_fields = ('cliente__username', 'cliente__email', 'mesero__username')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'total')
    ordering = ('-fecha_creacion',)
    list_per_page = 20
    inlines = [DetallePedidoInline]

    fieldsets = (
        ('Información del pedido', {
            'fields': ('cliente', 'mesero', 'mesa', 'estado', 'metodo_pago', 'notas'),
        }),
        ('Totales', {
            'fields': ('total',),
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',),
        }),
    )


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'plato', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('pedido__id', 'plato__nombre')
    readonly_fields = ('subtotal',)
