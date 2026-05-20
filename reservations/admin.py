from django.contrib import admin

from .models import Mesa, Reserva


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'capacidad', 'ubicacion', 'activa')
    list_filter = ('ubicacion', 'activa')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'mesa', 'fecha', 'hora_inicio', 'hora_fin', 'numero_personas', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha', 'mesa__ubicacion')
    search_fields = ('cliente__username', 'cliente__email')
    readonly_fields = ('fecha_creacion',)
