from django.contrib import admin
from django.utils.html import format_html

from .models import Categoria, Ingrediente, Plato, PlatoIngrediente


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_display_links = ('nombre',)
    list_editable = ('activo',)


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_con_alerta', 'stock_actual', 'stock_minimo', 'unidad_medida', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

    @admin.display(description='Nombre', ordering='nombre')
    def nombre_con_alerta(self, obj):
        if obj.stock_actual < obj.stock_minimo:
            return format_html(
                '<span style="color:#dc3545; font-weight:600;">'
                '&#9888; {}</span>',
                obj.nombre,
            )
        return obj.nombre


class PlatoIngredienteInline(admin.TabularInline):
    model = PlatoIngrediente
    extra = 1
    fields = ('ingrediente', 'cantidad_necesaria')


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'disponible', 'tiempo_preparacion')
    list_filter = ('categoria', 'disponible')
    search_fields = ('nombre', 'descripcion')
    list_display_links = ('nombre',)
    list_editable = ('disponible',)
    inlines = [PlatoIngredienteInline]


@admin.register(PlatoIngrediente)
class PlatoIngredienteAdmin(admin.ModelAdmin):
    list_display = ('plato', 'ingrediente', 'cantidad_necesaria')
    search_fields = ('plato__nombre', 'ingrediente__nombre')
