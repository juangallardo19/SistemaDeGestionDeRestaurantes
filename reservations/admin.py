from django.contrib import admin

from .models import Mesa, Reserva


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'capacidad', 'ubicacion', 'activa')
    list_filter = ('ubicacion', 'activa')
    list_display_links = ('numero',)
    list_editable = ('activa',)
    ordering = ('numero',)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'mesa', 'fecha', 'hora_inicio', 'hora_fin', 'numero_personas', 'estado')
    list_filter = ('estado', 'fecha', 'mesa__ubicacion')
    search_fields = ('cliente__username', 'cliente__email', 'mesa__numero')
    readonly_fields = ('fecha_creacion',)
    ordering = ('fecha', 'hora_inicio')
    list_per_page = 20

    fieldsets = (
        ('Información de la reserva', {
            'fields': ('cliente', 'mesa', 'numero_personas', 'estado', 'notas'),
        }),
        ('Horario', {
            'fields': ('fecha', 'hora_inicio', 'hora_fin'),
        }),
        ('Registro', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',),
        }),
    )
