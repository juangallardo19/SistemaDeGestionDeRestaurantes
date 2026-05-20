from django.contrib import admin

from .models import MovimientoInventario


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('ingrediente', 'tipo', 'cantidad', 'stock_resultante', 'responsable', 'fecha', 'motivo')
    list_filter = ('tipo', 'fecha', 'ingrediente')
    search_fields = ('ingrediente__nombre', 'responsable__username', 'motivo')
    readonly_fields = ('fecha',)
